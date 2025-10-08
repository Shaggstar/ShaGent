from datetime import datetime, timedelta
from app.core.data_models import Goal, Objective, KeyResult
from app.core.agent_pipeline import goals_to_tasks
from app.core.scheduler import schedule

def demo():
    g = Goal(
        domain="Writing",
        objective=Objective(
            title="Publish one poem per week",
            key_results=[KeyResult(description="Draft and edit a new poem", target=1)]
        ),
        skills=["meter", "imagery"],
        priority=2
    )
    tasks = goals_to_tasks([g])
    plan = schedule(tasks, datetime.now(), datetime.now() + timedelta(hours=3))
    for start, end, task in plan:
        print(start.strftime("%H:%M"), "-", end.strftime("%H:%M"), task.title)

if __name__ == "__main__":
    demo()
