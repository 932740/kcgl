from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
import pandas as pd
import io
from database import get_db


bp = Blueprint('report', __name__, url_prefix='/report')

@bp.route('/history')
def history():
    db = get_db()
    history = db.execute(
        "SELECT timestamp, device_name, action, amount, photo_path FROM history ORDER BY timestamp DESC"
    ).fetchall()
    return render_template('report/history.html', history=history)

@bp.route('/export', methods=['GET'])
def export():
    db = get_db()
    
    start = request.args.get("start")
    end = request.args.get("end")
    device_filter = request.args.get("device")
    export_format = request.args.get("format", "xlsx")
    
    query = "SELECT timestamp, device_name, action, amount, photo_path FROM history"
    conditions = []
    params = []
    
    if start and end:
        conditions.append("timestamp BETWEEN ? AND ?")
        params.extend([f"{start} 00:00:00", f"{end} 23:59:59"])
    
    if device_filter:
        conditions.append("device_name = ?")
        params.append(device_filter)
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY timestamp DESC"
    
    history_data = db.execute(query, params).fetchall()
    
    # 获取当前库存
    devices_dict = {row[0]: (row[1], row[2]) for row in db.execute("SELECT name, quantity, unit FROM devices").fetchall()}
    
    enriched = []
    for row in history_data:
        timestamp, name, action, amount, photo_path = row
        quantity_info = devices_dict.get(name, ("未知", "未知"))
        quantity, unit = quantity_info
        photo_url = url_for('static', filename=f'uploads/{photo_path}') if photo_path else ""
        enriched.append((timestamp, name, action, amount, quantity, unit, photo_url))
    
    df = pd.DataFrame(enriched, columns=['时间', '设备', '操作', '数量', '当前库存', '单位', '照片URL'])
    output = io.BytesIO()
    
    if export_format == 'csv':
        df.to_csv(output, index=False)
        output.seek(0)
        return send_file(output, as_attachment=True, download_name="操作记录.csv", mimetype='text/csv')
    else:
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='操作记录')
        output.seek(0)
        return send_file(
            output,
            as_attachment=True,
            download_name="操作记录_含库存.xlsx",
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

@bp.route('/view_photo/<filename>')
def view_photo(filename):
    return render_template('report/photo_view.html', filename=filename)    