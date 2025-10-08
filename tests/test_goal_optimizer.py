from app.core.data_models import Goal, Objective, KeyResult
from app.core.agent_pipeline import goals_to_tasks

def test_goals_to_tasks():
    g = Goal(domain="X", objective=Objective(title="Obj", key_results=[KeyResult(description="KR", target=1)]))
    tasks = goals_to_tasks([g])
    assert tasks and "KR1" in tasks[0].title
