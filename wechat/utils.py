from datetime import datetime 
import pytz
def timesince(dt, default="现在"):
    now = datetime.now(pytz.utc)
    diff = now - dt
    periods = (
        (diff.days / 365, "年"),
        (diff.days / 30, "个月"),
        (diff.days / 7, "周"),
        (diff.days, "天"),
        (diff.seconds / 3600, "小时"),
        (diff.seconds / 60, "分钟"),
        (diff.seconds, "秒"),
    )
    for period, singular in periods:
        if period >= 1:
            return "%d%s前" % (period, singular )
    return default
