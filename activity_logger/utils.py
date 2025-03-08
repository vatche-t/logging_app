from datetime import datetime


def format_timestamp(ts):
    return datetime.fromtimestamp(ts).isoformat()
