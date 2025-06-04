from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash

bp = Blueprint('auth', __name__, url_prefix='/auth')

# 模拟用户数据（实际应用中应存储在数据库）
users = {
    'admin': generate_password_hash('admin123')
}

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in users and check_password_hash(users[username], password):
            flash('登录成功', 'success')
            return redirect(url_for('index'))
        else:
            flash('用户名或密码错误', 'error')
    
    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    # 清除会话
    flash('已登出', 'success')
    return redirect(url_for('index'))    