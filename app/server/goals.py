import os
from typing import Dict, Any

import pandas as pd

GOALS_PATH = "app/data/private_goals_from_backlog.csv"
TEMPLATE_PATH = "app/data/private_goals_template.csv"

KEYWORDS = {
    "Writing": ["poem", "poetry", "write", "draft", "edit", "essay", "screenplay", "script"],
    "Mental Health": ["sleep", "nsdr", "meditat", "breath", "gratitude", "journal"],
    "Career": ["interview", "communication", "portfolio", "job", "resume", "network", "pm", "product"],
    "Learning": ["read", "study", "course", "lecture", "math", "bayes", "probability", "active inference"],
}


def load_goals(path: str | None = None) -> pd.DataFrame:
    candidate = path or (GOALS_PATH if os.path.exists(GOALS_PATH) else TEMPLATE_PATH)
    return pd.read_csv(candidate)


def categorize(df: pd.DataFrame) -> pd.DataFrame:
    def tag_row(text: str) -> str:
        lowered = (text or "").lower()
        tags = [cat for cat, kws in KEYWORDS.items() if any(k in lowered for k in kws)]
        return ",".join(tags)

    if "task" not in df.columns:
        df["task"] = df.get("objective", "").fillna("")
    df["categories"] = df.apply(lambda row: tag_row(f"{row.get('task', '')} {row.get('objective', '')}"), axis=1)
    df["multi_goal"] = df["categories"].apply(lambda value: 1 if value and "," in value else 0)
    return df


def summarize(df: pd.DataFrame) -> Dict[str, Any]:
    by_cat = (
        df["categories"]
        .fillna("")
        .str.split(",", expand=True)
        .stack()
        .str.strip()
    )
    by_cat = by_cat[by_cat != ""]
    counts = by_cat.value_counts().to_dict()
    multi = int(df["multi_goal"].sum())
    return {"by_category": counts, "multi_goal_tasks": multi}
