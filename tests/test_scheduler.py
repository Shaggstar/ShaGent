from datetime import datetime, timedelta
from app.core.data_models import Task
from app.core.scheduler import schedule

def test_schedule_creates_blocks():
    tasks = [Task(title="Test", minutes=50, energy="medium", priority=1)]
    plan = schedule(tasks, datetime(2025,1,1,9,0,0), datetime(2025,1,1,12,0,0))
    assert len(plan) >= 1
