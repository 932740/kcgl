from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_db, add_device, update_device, delete_device

bp = Blueprint('device', __name__, url_prefix='/device')

@bp.route('/management')
def management():
    """设备管理主页面（展示所有设备）"""
    db = get_db()
    devices = db.execute("SELECT * FROM devices ORDER BY name").fetchall()
    return render_template('device/management.html', devices=devices)

@bp.route('/add', methods=['POST'])
def add():
    """新增设备"""
    name = request.form['name']
    quantity = int(request.form['quantity'])
    unit = request.form['unit']
    
    if add_device(name, quantity, unit):  # 调用 database.py 中的函数
        flash('设备添加成功', 'success')
    else:
        flash('设备名称已存在', 'error')
    return redirect(url_for('device.management'))

@bp.route('/edit/<name>', methods=['GET', 'POST'])
def edit(name):
    db = get_db()
    device = db.execute("SELECT name, quantity, unit FROM devices WHERE name = ?", (name,)).fetchone()
    
    if request.method == 'POST':
        new_name = request.form['name']
        quantity = int(request.form['quantity'])
        unit = request.form['unit']
        
        try:
            # 如果设备名称改变，检查新名称是否已存在
            if new_name != name:
                existing = db.execute("SELECT name FROM devices WHERE name = ?", (new_name,)).fetchone()
                if existing:
                    flash('设备名称已存在', 'error')
                    return redirect(url_for('device.edit', name=name))
            
            db.execute(
                "UPDATE devices SET name = ?, quantity = ?, unit = ? WHERE name = ?",
                (new_name, quantity, unit, name)
            )
            db.commit()
            flash('设备更新成功', 'success')
            return redirect(url_for('device.management'))
        except Exception as e:
            flash(f'更新失败: {str(e)}', 'error')
    
    return render_template('device/edit.html', device=device)

@bp.route('/delete/<int:device_id>')  # 改为通过ID删除（更安全）
def delete(device_id):
    success, error = delete_device(device_id)  # 调用database.py中的安全删除函数
    if success:
        flash('设备删除成功', 'success')
    else:
        flash(f'删除失败: {error}', 'error')
    return redirect(url_for('device.management'))
