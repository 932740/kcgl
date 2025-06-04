import os
from flask import current_app, flash
from werkzeug.utils import secure_filename
from datetime import datetime

def allowed_file(filename):
    """检查文件是否允许上传"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def upload_file(file):
    """处理文件上传并返回保存的文件名"""
    if file and allowed_file(file.filename):
        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = secure_filename(file.filename)
        unique_filename = f"{timestamp}_{filename}"
        
        # 确保上传目录存在
        upload_folder = current_app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        # 保存文件
        try:
            file.save(os.path.join(upload_folder, unique_filename))
            return unique_filename
        except Exception as e:
            flash(f'文件保存失败: {str(e)}', 'error')
            return None
    
    flash('不支持的文件格式', 'error')
    return None    