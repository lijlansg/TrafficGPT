from datetime import datetime, timedelta

def get_fake_current_time():
    # 获取当前时间
    current_time = datetime.now()

    # 修改日期为2019年8月16日
    new_date = datetime(2019, 8, 16, current_time.hour, current_time.minute, current_time.second)

    # 格式化时间为指定格式
    formatted_time = new_date.strftime('%Y-%m-%d %H:%M:%S')

    return formatted_time

def get_time_period(given_time_str):
    # 将字符串转换为datetime对象
    given_time = datetime.strptime(given_time_str, '%Y-%m-%d %H:%M:%S')

    # 获取该时间所在的小时
    hour = given_time.hour

    # 构造小时区间的起始时间和结束时间
    start_hour = datetime(given_time.year, given_time.month, given_time.day, hour, 0, 0)
    end_hour = start_hour + timedelta(hours=1)

    return start_hour, end_hour