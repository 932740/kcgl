import os
from flask import current_app, flash, session
from werkzeug.utils import secure_filename
from datetime import datetime


def allowed_file(filename):
    """检查文件是否允许上传"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def upload_file(file, form_data=None):
    """
    处理文件上传并返回保存的文件名
    增加了表单数据缓存和更完善的错误处理
    """
    # 缓存表单数据（如果提供）
    if form_data:
        session['last_form_data'] = form_data

    # 检查文件是否存在
    if not file:
        flash('请选择要上传的文件', 'error')
        return None

    # 检查文件大小（防止超出 Flask 配置的 MAX_CONTENT_LENGTH）
    try:
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # 重置文件指针

        max_size = current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)
        if file_size > max_size:
            flash(f'文件大小超过限制（最大 {max_size // (1024 * 1024)}MB）', 'error')
            return None
    except Exception as e:
        flash(f'文件大小检查失败: {str(e)}', 'error')
        return None

    # 检查文件格式
    if not allowed_file(file.filename):
        allowed_exts = ', '.join(current_app.config['ALLOWED_EXTENSIONS'])
        flash(f'不支持的文件格式，允许的格式: {allowed_exts}', 'error')
        return None

    # 生成唯一文件名
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = secure_filename(file.filename)
    unique_filename = f"{timestamp}_{filename}"

    # 确保上传目录存在
    upload_folder = current_app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        try:
            os.makedirs(upload_folder)
        except Exception as e:
            flash(f'创建上传目录失败: {str(e)}', 'error')
            return None

    # 保存文件
    try:
        file.save(os.path.join(upload_folder, unique_filename))
        # 上传成功后清除缓存的表单数据
        if 'last_form_data' in session:
            session.pop('last_form_data')
        return unique_filename
    except Exception as e:
        flash(f'文件保存失败: {str(e)}', 'error')
        # 新增：无论失败与否都清理无效的表单缓存
        if 'last_form_data' in session:
            session.pop('last_form_data')
        # 删除可能已上传的不完整文件
        incomplete_path = os.path.join(upload_folder, unique_filename)
        if os.path.exists(incomplete_path):
            os.remove(incomplete_path)
        return None


