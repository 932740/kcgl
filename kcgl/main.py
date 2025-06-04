# from flask import Flask
from config import Config
from database import init_db
from routes import auth, device, stock, report
from database import get_db
from flask import Flask, render_template
app = Flask(__name__)
app.config.from_object(Config)

# 初始化数据库
init_db(app)

# 注册蓝图
app.register_blueprint(auth.bp)
app.register_blueprint(device.bp)
app.register_blueprint(stock.bp)
app.register_blueprint(report.bp)

@app.route('/')
def index():
    db = get_db()
    devices = db.execute("SELECT * FROM devices").fetchall()
    total_devices = len(devices)
    total_quantity = sum(device['quantity'] for device in devices) if devices else 0
    
    recent_in = db.execute(
        "SELECT * FROM history WHERE action = '入库' ORDER BY timestamp DESC LIMIT 5"
    ).fetchall()
    
    recent_out = db.execute(
        "SELECT * FROM history WHERE action = '出库' ORDER BY timestamp DESC LIMIT 5"
    ).fetchall()
    
    return render_template('index.html', 
                          total_devices=total_devices, 
                          total_quantity=total_quantity,
                          recent_in=recent_in,
                          recent_out=recent_out)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=app.config['DEBUG'])    