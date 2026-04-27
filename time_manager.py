import json
import os
from datetime import datetime

# Path Unification
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
TIMETABLE_FILE = os.path.join(DATA_DIR, "timetable.json")

def save_timetable(data):
    """Saves the full timetable data to the data folder."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(TIMETABLE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def get_up_next():
    """Calculates status and returns it without triggering Live Server refresh loops."""
    if not os.path.exists(TIMETABLE_FILE):
        return None

    with open(TIMETABLE_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    now = datetime.now()
    current_day = now.strftime("%A") 
    current_time = now.strftime("%H:%M") 

    status = {
        "current_class": None,
        "next_class": None,
        "time_until_next": None,
        "last_updated": now.strftime("%Y-%m-%d %H:%M:%S")
    }

    todays_classes = [c for c in data.get("classes", []) if c["day"] == current_day]
    todays_classes.sort(key=lambda x: x["time_start"])

    for c in todays_classes:
        start = c["time_start"]
        end = c["time_end"]
        if start <= current_time <= end:
            status["current_class"] = c
        elif start > current_time:
            status["next_class"] = c
            fmt = "%H:%M"
            t_now = datetime.strptime(current_time, fmt)
            t_start = datetime.strptime(start, fmt)
            diff = (t_start - t_now).seconds // 60
            status["time_until_next"] = diff
            break

    return status