import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    DEBUG = True  # 开发模式启用调试
    
    # 数据库配置
    DB_PATH = os.path.join(os.path.abspath('.'), 'inventory.db')  # SQLite 数据库路径
    
    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(os.path.abspath('.'), 'static', 'uploads')  # 上传目录
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  # 允许的上传格式
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 最大文件大小 16MB
    
    # 分页配置
    DEVICES_PER_PAGE = 15
    HISTORY_PER_PAGE = 20