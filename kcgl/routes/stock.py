from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from datetime import datetime
from utils.file_upload import upload_file
from database import get_db, update_stock
from utils.date_utils import format_datetime
import logging

# 配置日志记录
logging.basicConfig(level=logging.ERROR)

bp = Blueprint('stock', __name__, url_prefix='/stock')

def handle_stock_operation(action):
    db = get_db()
    if request.method == 'POST':
        # 验证表单数据
        device_name = request.form.get('name')
        if not device_name:
            flash('设备名称字段缺失，请检查表单', 'error')
            return redirect(url_for(f'stock.stock_{action.lower()}'))

        try:
            amount = int(request.form.get('amount'))
            if amount <= 0:
                raise ValueError("数量必须大于 0")
        except (ValueError, TypeError):
            flash('请输入有效的数量', 'error')
            return redirect(url_for(f'stock.stock_{action.lower()}'))

        operation_date = request.form.get('operation_date')
        timestamp = format_datetime(operation_date)

        # 处理文件上传
        photo_file = request.files.get('photo')
        if not photo_file:
            flash('请上传操作照片', 'error')
            return redirect(url_for(f'stock.stock_{action.lower()}'))

        if photo_file.filename == '':
            flash('请选择照片文件', 'error')
            return redirect(url_for(f'stock.stock_{action.lower()}'))

        photo_path = upload_file(photo_file)
        if not photo_path:
            return redirect(url_for(f'stock.stock_{action.lower()}'))

        # 获取出库原因（仅出库操作需要）
        reason = request.form.get('reason') if action == '出库' else None

        # 调用数据库更新函数
        success, error = update_stock(device_name, amount, action, timestamp, photo_path, reason)
        if success:
            flash(f'{action}操作成功', 'success')
            return redirect(url_for(f'stock.stock_{action.lower()}'))
        else:
            # 发生错误时删除已上传的照片
            if photo_path and os.path.exists(os.path.join(current_app.config['UPLOAD_FOLDER'], photo_path)):
                os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], photo_path))
            logging.error(f'{action}操作失败: {error}')
            flash(f'操作失败: {error}', 'error')
            return redirect(url_for(f'stock.stock_{action.lower()}'))

    # 获取设备列表
    devices = db.execute("SELECT name, quantity, unit FROM devices").fetchall()
    current_datetime = datetime.now().strftime("%Y-%m-%dT%H:%M")

    # 获取最近记录
    recent_history = db.execute(
        f"SELECT timestamp, device_name, amount, photo_path FROM history WHERE action = '{action}' ORDER BY timestamp DESC LIMIT 5"
    ).fetchall()

    return render_template(f'stock/{action.lower()}.html', devices=devices, current_datetime=current_datetime, recent_history=recent_history)


@bp.route('/in', methods=['GET', 'POST'])
def stock_in():
    return handle_stock_operation('in')


@bp.route('/out', methods=['GET', 'POST'])
def stock_out():
    return handle_stock_operation('out')


# 删除以下冗余路由（与数据库函数重名且逻辑重复）
# @bp.route('/update_stock', methods=['POST'])
# def update_stock():
#     # 先获取并验证表单数据
#     name = request.form.get('name')
#     amount = request.form.get('amount', type=int)
#     operation_date = request.form.get('operation_date')
#
#     if not name:
#         flash('请选择设备名称', 'error')
#         return redirect(url_for('stock.stock_in'))
#
#     if not amount or amount <= 0:
#         flash('请输入有效的入库数量', 'error')
#         return redirect(url_for('stock.stock_in'))
#
#     # 准备表单数据用于缓存
#     form_data = {
#         'name': name,
#         'amount': amount,
#         'operation_date': operation_date
#     }
#
#     # 处理文件上传，传入表单数据
#     photo = request.files.get('photo')
#     photo_path = upload_file(photo, form_data)
#
#     if not photo_path:
#         # 文件上传失败，重定向回表单页，数据会通过 session 保留
#         return redirect(url_for('stock.stock_in'))
#
#     # 文件上传成功，继续处理入库逻辑
#     success, error = update_stock(name, amount, '入库', operation_date, photo_path)
#     if success:
#         flash('入库操作成功', 'success')
#         return redirect(url_for('stock.stock_in'))
#     else:
#         # 发生错误时删除已上传的照片
#         if photo_path and os.path.exists(os.path.join(current_app.config['UPLOAD_FOLDER'], photo_path)):
#             os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], photo_path))
#         logging.error(f'入库操作失败: {error}')
#         flash(f'操作失败: {error}', 'error')
#         return redirect(url_for('stock.stock_in'))