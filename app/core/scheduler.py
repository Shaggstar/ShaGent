from typing import List
from datetime import datetime, timedelta
from .data_models import Task

def schedule(tasks: List[Task], start: datetime, end: datetime, focus_block_minutes: int = 50, break_minutes: int = 10):
    plan = []
    t = start
    for task in sorted(tasks, key=lambda x: (x.priority, -x.minutes)):
        if t + timedelta(minutes=focus_block_minutes) > end:
            break
        plan.append((t, t + timedelta(minutes=focus_block_minutes), task))
        t += timedelta(minutes=focus_block_minutes + break_minutes)
    return plan
