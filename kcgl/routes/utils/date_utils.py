from datetime import datetime

def format_datetime(datetime_str):
    """将YYYY-MM-DDTHH:MM格式的字符串转换为YYYY-MM-DD HH:MM:SS格式"""
    try:
        dt = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        # 如果格式不匹配，返回当前时间
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")    