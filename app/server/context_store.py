import json
import os
from typing import Dict, List

CONTEXTS_FILE = "app/data/task_contexts.json"

CONTEXT_QUESTIONS: Dict[str, Dict[str, List[str]]] = {
    "PRODUCT LEADERSHIP": {
        "Discovery Engine (PM)": [
            "What is your current LinkedIn post topic/draft?",
            "Which Active Inference concept are you explaining this week?",
            "What research papers or examples will you cite?"
        ],
        "Better Self App": [
            "What feature are you working on right now?",
            "What is your current design/code state?",
            "What specific user problem are you solving?"
        ]
    },
    "RESEARCH & THEORY": {
        "Active Inference Fellow": [
            "What is your current Colab notebook URL?",
            "Which specific function/module are you implementing?",
            "What pseudocode or paper references do you have ready?"
        ],
        "Narrative Research": [
            "What section of the paper are you working on?",
            "What research have you gathered so far?",
            "What is your current draft word count/status?"
        ]
    },
    "CREATIVE EXPRESSION": {
        "Poetry Book": [
            "What day of the 28-day syllabus are you on?",
            "What poetic form are you practicing today (iambic pentameter, heroic couplets, etc.)?",
            "What draft poems do you currently have in progress?"
        ],
        "Screenwriting": [
            "What scene/act number are you working on?",
            "How many pages have you written so far?",
            "What is your target page count for this session?"
        ]
    },
    "CAREER ADVANCEMENT": {
        "Job Search": [
            "Which 2 companies are you targeting today?",
            "Is your resume tailored for these specific roles?",
            "Have you researched both companies' recent news/projects?"
        ],
        "Interview Prep": [
            "Which company/role is this interview for?",
            "What interview format (behavioral, technical, case study)?",
            "What specific prep materials do you have?"
        ]
    },
    "PERSONAL DEVELOPMENT": {
        "Mental Health": [],
        "Journaling": [],
        "Habit Formation": []
    }
}


def load_contexts() -> Dict[str, Dict]:
    if os.path.exists(CONTEXTS_FILE):
        with open(CONTEXTS_FILE, "r", encoding="utf-8") as handle:
            try:
                return json.load(handle)
            except json.JSONDecodeError:
                return {}
    return {}


def save_contexts(contexts: Dict[str, Dict]) -> None:
    os.makedirs(os.path.dirname(CONTEXTS_FILE), exist_ok=True)
    with open(CONTEXTS_FILE, "w", encoding="utf-8") as handle:
        json.dump(contexts, handle, indent=2)


def get_context_questions(domain: str, objective: str) -> List[str]:
    return CONTEXT_QUESTIONS.get(domain, {}).get(objective, [])
