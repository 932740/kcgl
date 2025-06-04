import sqlite3
from flask import g, current_app

def get_db():
    """获取数据库连接"""
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DB_PATH'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row  # 支持字典式访问
    return g.db

def init_db(app):
    """初始化数据库（创建设备表和历史表）"""
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,  -- 设备名称唯一（使用--代替#注释）
                quantity INTEGER DEFAULT 0,
                unit TEXT          -- 单位（如：台、件）（使用--代替#注释）
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY,
                device_name TEXT,   -- 关联设备名称（使用--代替#注释）
                action TEXT,        -- 操作类型（入库/出库）（使用--代替#注释）
                amount INTEGER,     -- 操作数量（使用--代替#注释）
                timestamp TEXT,     -- 操作时间（使用--代替#注释）
                photo_path TEXT     -- 操作照片路径（使用--代替#注释）
            )
        ''')
        db.commit()
    app.teardown_appcontext(close_db)  # 注册关闭连接回调

def close_db(e=None):
    """关闭数据库连接"""
    db = g.pop('db', None)
    if db:
        db.close()


def add_device(name, quantity, unit):
    """添加新设备"""
    db = get_db()
    try:
        db.execute(
            "INSERT INTO devices (name, quantity, unit) VALUES (?, ?, ?)",
            (name, quantity, unit)
        )
        db.commit()
        return True
    except sqlite3.IntegrityError as e:
        # 处理唯一约束冲突
        print(f"设备名称已存在: {e}")
        db.rollback()
        return False
    except Exception as e:
        print(f"添加设备失败: {e}")
        db.rollback()
        return False


def update_device(device_id, name, quantity, unit):
    """更新设备信息"""
    db = get_db()
    try:
        db.execute(
            "UPDATE devices SET name = ?, quantity = ?, unit = ? WHERE id = ?",
            (name, quantity, unit, device_id)
        )
        db.commit()
        return True
    except Exception as e:
        print(f"更新设备失败: {e}")
        db.rollback()
        return False


def delete_device(device_id):
    """删除设备"""
    db = get_db()
    try:
        # 先检查是否有历史记录
        history_count = db.execute(
            "SELECT COUNT(*) FROM history WHERE device_name = (SELECT name FROM devices WHERE id = ?)",
            (device_id,)
        ).fetchone()[0]

        if history_count > 0:
            # 有历史记录，不允许删除
            return False, "该设备有历史记录，无法删除"

        # 没有历史记录，可以删除
        db.execute("DELETE FROM devices WHERE id = ?", (device_id,))
        db.commit()
        return True, None
    except Exception as e:
        print(f"删除设备失败: {e}")
        db.rollback()
        return False, str(e)


def get_all_devices():
    """获取所有设备"""
    db = get_db()
    return db.execute("SELECT * FROM devices ORDER BY id").fetchall()


def get_device_by_id(device_id):
    """根据ID获取设备"""
    db = get_db()
    return db.execute("SELECT * FROM devices WHERE id = ?", (device_id,)).fetchone()


def get_device_by_name(name):
    """根据名称获取设备"""
    db = get_db()
    return db.execute("SELECT * FROM devices WHERE name = ?", (name,)).fetchone()


# 库存操作函数
# 移除原routes/database.py中重复的函数定义
# 保留并优化database.py中的核心函数（如update_stock）

def update_stock(device_name, amount, action, timestamp, photo_path=None, reason=None):
    """更新库存（入库/出库）- 增强错误提示"""
    db = get_db()
    try:
        db.execute("BEGIN")
        device = db.execute("SELECT * FROM devices WHERE name = ?", (device_name,)).fetchone()
        if not device:
            raise ValueError(f"设备 '{device_name}' 不存在（请检查设备名称是否正确）")
        
        if action == '入库':
            new_quantity = device['quantity'] + amount
        elif action == '出库':
            if amount > device['quantity']:
                raise ValueError(f"出库失败：当前库存仅{device['quantity']}{device['unit']}，不足{amount}{device['unit']}")
            new_quantity = device['quantity'] - amount
        else:
            raise ValueError("无效的操作类型（仅支持'入库'或'出库'）")

        db.execute("UPDATE devices SET quantity = ? WHERE name = ?", (new_quantity, device_name))
        db.execute(
            "INSERT INTO history (device_name, action, amount, timestamp, photo_path, reason) VALUES (?, ?, ?, ?, ?, ?)",
            (device_name, action, amount, timestamp, photo_path, reason)
        )
        db.commit()
        return True, None
    except Exception as e:
        db.rollback()
        return False, f"操作失败：{str(e)}（事务已回滚）"


# 历史记录函数
def get_recent_history(limit=10, action_type=None):
    """获取最近的历史记录"""
    db = get_db()
    query = "SELECT * FROM history"
    params = []

    if action_type:
        query += " WHERE action = ?"
        params.append(action_type)

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    return db.execute(query, params).fetchall()


def get_history_by_device(device_name, limit=100):
    """获取特定设备的历史记录"""
    db = get_db()
    return db.execute(
        "SELECT * FROM history WHERE device_name = ? ORDER BY timestamp DESC LIMIT ?",
        (device_name, limit)
    ).fetchall()


def get_all_history(filters=None, limit=100, offset=0):
    """获取所有历史记录，支持筛选"""
    db = get_db()
    query = "SELECT * FROM history"
    conditions = []
    params = []

    if filters:
        if 'device_name' in filters and filters['device_name'] != 'all':
            conditions.append("device_name = ?")
            params.append(filters['device_name'])

        if 'action' in filters and filters['action'] != 'all':
            conditions.append("action = ?")
            params.append(filters['action'])

        if 'start_date' in filters and filters['start_date']:
            conditions.append("timestamp >= ? || ' 00:00:00'")
            params.append(filters['start_date'])

        if 'end_date' in filters and filters['end_date']:
            conditions.append("timestamp <= ? || ' 23:59:59'")
            params.append(filters['end_date'])

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    return db.execute(query, params).fetchall()


def get_history_count(filters=None):
    """获取历史记录总数，支持筛选"""
    db = get_db()
    query = "SELECT COUNT(*) FROM history"
    conditions = []
    params = []

    if filters:
        if 'device_name' in filters and filters['device_name'] != 'all':
            conditions.append("device_name = ?")
            params.append(filters['device_name'])

        if 'action' in filters and filters['action'] != 'all':
            conditions.append("action = ?")
            params.append(filters['action'])

        if 'start_date' in filters and filters['start_date']:
            conditions.append("timestamp >= ? || ' 00:00:00'")
            params.append(filters['start_date'])

        if 'end_date' in filters and filters['end_date']:
            conditions.append("timestamp <= ? || ' 23:59:59'")
            params.append(filters['end_date'])

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    return db.execute(query, params).fetchone()[0]