from typing import List
from .data_models import Goal, Task

def goals_to_tasks(goals: List[Goal]) -> List[Task]:
    tasks: List[Task] = []
    for g in goals:
        for i, kr in enumerate(g.objective.key_results):
            tasks.append(Task(
                title=f"{g.objective.title} • KR{i+1}: {kr.description}",
                minutes=50,
                energy="medium",
                priority=g.priority,
                tags=[g.domain]
            ))
    return tasks
