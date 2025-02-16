from datetime import datetime


def inject_now():
    return {"now": datetime.now}
