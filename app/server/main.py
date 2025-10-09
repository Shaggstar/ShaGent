import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .calendar import fetch_busy_from_ics
from .context_store import (
    CONTEXT_QUESTIONS,
    get_context_questions,
    load_contexts,
    save_contexts,
)
from .goals import categorize, load_goals, summarize
from .llm_router import run as llm_run

app = FastAPI(title="ShAgent Server")
app.mount("/ui", StaticFiles(directory="app/ui/web", html=True), name="ui")

FOCUS_MAX_MINUTES = 240  # four-hour cap

CATEGORY_META = {
    "career": {"emoji": "💼", "label": "Career"},
    "writing": {"emoji": "✍️", "label": "Writing"},
    "research": {"emoji": "🔬", "label": "Research / Active Inference"},
    "mental health": {"emoji": "🧘", "label": "Mental Health"},
    "learning": {"emoji": "📚", "label": "Learning"},
}


def _focus_log_path(date_label: Optional[str] = None) -> str:
    label = date_label or datetime.now().date().isoformat()
    return os.path.join("app", "data", f"focus_log_{label}.json")


def _load_focus_log(date_label: Optional[str] = None) -> Dict[str, Any]:
    path = _focus_log_path(date_label)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as handle:
            try:
                return json.load(handle)
            except json.JSONDecodeError:
                return {"total_minutes": 0, "sessions": []}
    return {"total_minutes": 0, "sessions": []}


def _save_focus_log(log: Dict[str, Any], date_label: Optional[str] = None) -> None:
    path = _focus_log_path(date_label)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(log, handle, indent=2)


def _focus_stats() -> Dict[str, Any]:
    log = _load_focus_log()
    total = int(log.get("total_minutes", 0))
    remaining = max(0, FOCUS_MAX_MINUTES - total)
    return {
        "total_minutes": total,
        "remaining_minutes": remaining,
        "max_minutes": FOCUS_MAX_MINUTES,
        "warning": remaining <= 30 and remaining > 0,
        "limit_reached": remaining <= 0,
    }


def _canonical_category(raw: str) -> str:
    if not raw:
        return "general"
    slug = raw.lower().strip()
    if slug in CATEGORY_META:
        return slug
    if "career" in slug:
        return "career"
    if "write" in slug or "poetry" in slug:
        return "writing"
    if "research" in slug or "inference" in slug:
        return "research"
    if "mental" in slug or "health" in slug:
        return "mental health"
    if "learn" in slug or "study" in slug:
        return "learning"
    return slug


def _task_status_from_context(
    context_entry: Dict[str, Any],
    questions: List[str],
    domain: str,
) -> str:
    if context_entry.get("status") in {"needs-info", "ready", "in-progress", "completed"}:
        return context_entry["status"]
    if "Mental Health" in domain:
        return "ready"
    if questions and not context_entry.get("answers"):
        return "needs-info"
    return "ready"


def _task_category_key(row: pd.Series) -> str:
    raw = row.get("categories") or row.get("domain") or ""
    first = raw.split(",")[0].strip()
    return _canonical_category(first)


def _task_payload(row: pd.Series, contexts: Dict[str, Any]) -> Dict[str, Any]:
    task_id = int(row.name)
    context_entry = contexts.get(str(task_id), {})
    questions = get_context_questions(row.get("domain", ""), row.get("objective", ""))
    status = row.get("task_status") or _task_status_from_context(
        context_entry,
        questions,
        row.get("domain", ""),
    )
    return {
        "id": task_id,
        "title": row.get("task", ""),
        "domain": f"{row.get('domain', '')} - {row.get('objective', '')}".strip(" -"),
        "minutes": int(row.get("minutes", 60) or 60),
        "energy": row.get("energy", "medium"),
        "priority": int(row.get("priority_num", 3) or 3),
        "time_of_day": row.get("time_of_day", ""),
        "status": status,
        "context_questions": questions,
        "saved_context": context_entry.get("answers", {}),
        "context_timestamp": context_entry.get("timestamp"),
    }


def _load_active_tasks() -> Dict[str, Any]:
    df = load_goals()
    df = categorize(df)
    contexts = load_contexts()
    active = df[df.get("status", "") != "Done"].copy()
    energy_rank = {"high": 0, "medium": 1, "low": 2}
    if "energy" in active.columns:
        active["energy_rank"] = active["energy"].map(lambda val: energy_rank.get(str(val).lower(), 1)).fillna(1)
    else:
        active["energy_rank"] = 1
    active["category_key"] = active.apply(_task_category_key, axis=1)
    active["task_status"] = active.apply(
        lambda row: _task_status_from_context(
            contexts.get(str(row.name), {}),
            get_context_questions(row.get("domain", ""), row.get("objective", "")),
            row.get("domain", ""),
        ),
        axis=1,
    )
    active = active.sort_values(
        by=["priority_num", "energy_rank", "minutes"],
        ascending=[True, True, True],
    )
    return {"dataframe": active, "contexts": contexts}


def _tasks_payload_list(active: pd.DataFrame, contexts: Dict[str, Any]) -> List[Dict[str, Any]]:
    payloads: List[Dict[str, Any]] = []
    for _, row in active.iterrows():
        payload = _task_payload(row, contexts)
        payload["category_key"] = row.get("category_key", "")
        payload["domain_raw"] = row.get("domain", "")
        payload["objective_raw"] = row.get("objective", "")
        payloads.append(payload)
    return payloads


class WritingPayload(BaseModel):
    mode: str = "audience"
    targetDetail: str = "general readers"
    kind: str = "auto"
    text: str

@app.post("/api/writing")
def analyze_writing(payload: WritingPayload):
    try:
        system = "You are a writing coach. Return valid JSON that matches the schema."
        schema = {
            "doc_summary":"string",
            "layers":{
              "grammar":{"score":"int","issues":[{"span":[0,0],"fix":"string"}],"notes":"string"},
              "clarity":{"score":"int","rewrites":[{"span":[0,0],"text":"string"}]},
              "style":{"score":"int","style_axis":{"tone":"string","diction":"string"},"examples":[]},
              "content":{"score":"int","gaps":[],"claims_to_check":[],"outline_fix":[]},
              "target":{"goal":"string","score":"int","keywords":[],"title_tags":[],"meta_desc":""},
              "related":{"reading_list":[],"exemplars":[]}
            }
        }
        prompt = json.dumps({"mode": payload.mode, "targetDetail": payload.targetDetail, "schema": schema, "text": payload.text})
        resp = llm_run(prompt, system)
        start = resp.find("{"); end = resp.rfind("}")
        return json.loads(resp[start:end+1])
    except Exception:
        # simple fallback if a provider fails
        text = payload.text
        words = len(text.split())
        sentences = max(1, text.count(".") + text.count("!") + text.count("?"))
        avg_len = words / sentences
        return {
            "doc_summary": f"{words} words; {sentences} sentences; avg {avg_len:.1f} words/sentence.",
            "layers": {
                "grammar": {"score": 95, "issues": [], "notes": "Heuristic fallback"},
                "clarity": {"score": 100 - int(max(0, avg_len-22)*2), "rewrites": []},
                "style": {"score": 70, "style_axis": {"tone":"neutral","diction":"plain"}, "examples":[]},
                "content": {"score": 75, "gaps": [], "claims_to_check": [], "outline_fix":[]},
                "target": {"goal": payload.mode, "score": 72, "keywords": [], "title_tags": [], "meta_desc": ""},
                "related": {"reading_list": [], "exemplars": []}
            }
        }

class TaskIn(BaseModel):
    title: str
    minutes: int = 50
    energy: str = "medium"
    priority: int = 3

class ScheduleRequest(BaseModel):
    tasks: List[TaskIn]
    day_start: str = "09:00"
    day_end: str = "17:30"
    energy_curve: Dict[str, float] = {"09:00": 0.6, "10:00": 0.8, "11:00": 0.9, "13:00": 0.7, "15:00": 0.6, "16:00": 0.5}
    calendar_csv: Optional[str] = None
    calendar_ics_url: Optional[str] = None

def _parse_time(tstr: str) -> datetime:
    today = datetime.now().date()
    hh, mm = map(int, tstr.split(":"))
    return datetime(today.year, today.month, today.day, hh, mm)

def _load_busy(calendar_csv: Optional[str], calendar_ics_url: Optional[str]):
    busy = []
    if calendar_ics_url:
        try:
            busy.extend(fetch_busy_from_ics(calendar_ics_url))
        except Exception:
            pass
    if calendar_csv and os.path.exists(calendar_csv):
        df = pd.read_csv(calendar_csv)
        for _, row in df.iterrows():
            busy.append(
                (
                    datetime.fromisoformat(row["start"]),
                    datetime.fromisoformat(row["end"]),
                    row.get("title", "busy"),
                )
            )
    return busy

def _is_free(slot_start: datetime, slot_end: datetime, busy):
    for s,e,_ in busy:
        if max(s, slot_start) < min(e, slot_end):
            return False
    return True

@app.post("/api/schedule")
def schedule(req: ScheduleRequest):
    start = _parse_time(req.day_start)
    end = _parse_time(req.day_end)
    busy = _load_busy(req.calendar_csv, req.calendar_ics_url)
    energy_points = {k: v for k,v in req.energy_curve.items()}
    def energy_at(dt: datetime) -> float:
        key = dt.strftime("%H:00")
        return energy_points.get(key, 0.6)
    tasks = sorted(req.tasks, key=lambda t: (t.priority, {"low":0, "medium":1, "high":2}[t.energy]))
    plan = []
    t = start
    while t + timedelta(minutes=5) <= end and tasks:
        slot_energy = energy_at(t)
        def ok(task):
            need = {"low":0.5,"medium":0.75,"high":0.95}[task.energy]
            return slot_energy >= need
        idx = next((i for i,x in enumerate(tasks) if ok(x)), None)
        if idx is None:
            t += timedelta(minutes=30)
            continue
        task = tasks.pop(idx)
        slot_end = t + timedelta(minutes=task.minutes)
        if slot_end > end:
            break
        if _is_free(t, slot_end, busy):
            plan.append({"start": t.isoformat(), "end": slot_end.isoformat(), "title": task.title, "energy": slot_energy})
            t = slot_end + timedelta(minutes=10)
        else:
            t += timedelta(minutes=15)
    return {"plan": plan}

class AttentionPing(BaseModel):
    score: float
    workload: str = "unknown"

ATTENTION = {"last": 0.0}


class TaskContext(BaseModel):
    task_id: int
    answers: Dict[str, str]
    timestamp: Optional[str] = None


class TaskStatusUpdate(BaseModel):
    task_id: int
    status: str  # expected: needs-info | ready | in-progress | completed


class FocusTrackEntry(BaseModel):
    minutes: int
    task_id: Optional[int] = None
    task_title: Optional[str] = None

@app.post("/api/state/attention")
def state_attention(ping: AttentionPing):
    ATTENTION["last"] = float(ping.score)
    if ATTENTION["last"] < 0.35:
        nudge = "Stand, breathe 4x, 30 sec reset. Then resume."
    elif ATTENTION["last"] < 0.6:
        nudge = "Trim the task to one concrete step and continue for 10 minutes."
    else:
        nudge = "Protect focus. Silence notifications for 25 minutes."
    return {"ok": True, "nudge": nudge, "attention": ATTENTION["last"]}

@app.get("/api/calendar/busy")
def calendar_busy(ics: str = Query(..., description="Google Calendar ICS URL")):
    blocks = fetch_busy_from_ics(ics)
    return [{"start": s.isoformat(), "end": e.isoformat(), "title": t} for s, e, t in blocks]

@app.get("/api/today/organized")
def today_organized():
    state = _load_active_tasks()
    active = state["dataframe"]
    contexts = state["contexts"]
    focus = _focus_stats()
    payloads = _tasks_payload_list(active, contexts)

    categories: Dict[str, Dict[str, Any]] = {}
    needs_context, ready, in_progress, completed = [], [], [], []

    for task in payloads:
        category_key = (task.get("category_key") or "general").strip()
        slug = category_key.replace(" ", "-")
        meta = CATEGORY_META.get(category_key, {"emoji": "", "label": category_key.title()})
        bucket = categories.setdefault(
            slug,
            {
                "name": f"{meta.get('emoji', '')} {meta.get('label', category_key.title())}".strip(),
                "tasks": [],
            },
        )
        if len(bucket["tasks"]) < 5:
            bucket["tasks"].append(task)

        status = task.get("status")
        if status == "needs-info":
            needs_context.append(task)
        elif status == "in-progress":
            in_progress.append(task)
        elif status == "completed":
            completed.append(task)
        else:
            ready.append(task)

    summary = {
        "ready": len(ready),
        "needs_context": len(needs_context),
        "in_progress": len(in_progress),
        "completed": len(completed),
        "total": len(payloads),
    }

    return {
        "categories": categories,
        "focus_limit": focus,
        "summary": summary,
        "needs_context": [task["id"] for task in needs_context],
        "ready_tasks": [task["id"] for task in ready],
    }

@app.get("/api/focus/remaining")
def focus_remaining():
    return _focus_stats()

@app.post("/api/focus/track")
def focus_track(entry: FocusTrackEntry):
    if entry.minutes <= 0:
        raise HTTPException(status_code=400, detail="minutes must be positive")
    log = _load_focus_log()
    log.setdefault("sessions", [])
    log["total_minutes"] = int(log.get("total_minutes", 0)) + int(entry.minutes)
    log["sessions"].append(
        {
            "timestamp": datetime.now().isoformat(),
            "minutes": int(entry.minutes),
            "task_id": entry.task_id,
            "task_title": entry.task_title,
        }
    )
    _save_focus_log(log)
    stats = _focus_stats()
    return {
        "total_today": stats["total_minutes"],
        "remaining": stats["remaining_minutes"],
        "warning": stats["warning"],
        "limit_reached": stats["limit_reached"],
    }

@app.post("/api/tasks/context")
def save_task_context(context: TaskContext):
    contexts = load_contexts()
    entry = contexts.get(str(context.task_id), {})
    entry["answers"] = context.answers
    entry["timestamp"] = context.timestamp or datetime.now().isoformat()
    entry["status"] = "ready"
    contexts[str(context.task_id)] = entry
    save_contexts(contexts)
    return {"ok": True, "status": "ready"}

@app.get("/api/tasks/context/{task_id}")
def get_task_context(task_id: int):
    contexts = load_contexts()
    return contexts.get(str(task_id), {})

@app.get("/api/tasks/questions")
def get_context_questions_endpoint(domain: str, objective: str):
    questions = get_context_questions(domain, objective)
    return {"questions": questions}

@app.post("/api/tasks/status")
def update_task_status(update: TaskStatusUpdate):
    allowed = {"needs-info", "ready", "in-progress", "completed"}
    if update.status not in allowed:
        raise HTTPException(status_code=400, detail=f"status must be one of {sorted(allowed)}")
    contexts = load_contexts()
    entry = contexts.get(str(update.task_id), {})
    entry["status"] = update.status
    if update.status == "needs-info":
        entry.pop("answers", None)
    entry.setdefault("timestamp", datetime.now().isoformat())
    contexts[str(update.task_id)] = entry
    save_contexts(contexts)
    return {"ok": True, "status": update.status}

@app.post("/api/tasks/smart-suggest")
def smart_suggest_next_task():
    focus = _focus_stats()
    if focus["limit_reached"]:
        return {
            "action": "rest",
            "message": "🛑 You've hit your 4-hour focus limit. Time to recharge.",
            "reason": "Focus cap reached",
        }

    state = _load_active_tasks()
    active = state["dataframe"]
    contexts = state["contexts"]
    payloads = _tasks_payload_list(active, contexts)

    if not payloads:
        return {
            "action": "celebrate",
            "message": "🎉 You've cleared your priority list!",
            "reason": "No active tasks remain",
        }

    needs_context = [task for task in payloads if task["status"] == "needs-info"]
    if needs_context:
        task = needs_context[0]
        return {
            "action": "gather_context",
            "task_id": task["id"],
            "title": task["title"],
            "message": f"Let's gather context for: {task['title']}",
            "reason": "Highest priority task still needs context",
        }

    ready_tasks = [task for task in payloads if task["status"] in {"ready", "in-progress"}]
    if not ready_tasks:
        return {
            "action": "celebrate",
            "message": "🎉 You're clear for the day!",
            "reason": "All tasks need context or are complete",
        }

    hour = datetime.now().hour
    attention = ATTENTION.get("last", 0.5)

    def pick_task(filter_fn):
        for task in ready_tasks:
            if filter_fn(task):
                return task
        return None

    if 6 <= hour < 11 and attention > 0.65:
        task = pick_task(lambda t: t.get("energy", "medium") == "high")
        if task:
            return {
                "action": "start_task",
                "task_id": task["id"],
                "title": task["title"],
                "message": f"🌅 Peak morning energy! Start: {task['title']}",
                "reason": "High attention window for deep work",
                "estimated_minutes": task.get("minutes", 60),
            }

    if attention < 0.5:
        task = pick_task(lambda t: t.get("energy", "medium") == "low")
        if task:
            return {
                "action": "start_task",
                "task_id": task["id"],
                "title": task["title"],
                "message": f"🔋 Low energy? Try: {task['title']}",
                "reason": "Lower focus required task recommended",
                "estimated_minutes": task.get("minutes", 60),
            }

    task = ready_tasks[0]
    return {
        "action": "start_task",
        "task_id": task["id"],
        "title": task["title"],
        "message": f"Next up: {task['title']}",
        "reason": "Highest priority task that's ready",
        "estimated_minutes": task.get("minutes", 60),
    }

@app.get("/api/tasks/actionability-check")
def check_task_actionability():
    state = _load_active_tasks()
    active = state["dataframe"]
    contexts = state["contexts"]
    payloads = _tasks_payload_list(active, contexts)

    report = {"ready": [], "needs_context": [], "in_progress": []}
    for task in payloads:
        entry = {
            "id": task["id"],
            "title": task["title"],
            "domain": task.get("domain"),
            "priority": task.get("priority"),
        }
        status = task.get("status")
        if status == "in-progress":
            report["in_progress"].append(entry)
        elif status == "needs-info":
            questions = task.get("context_questions") or []
            if questions:
                entry["missing_context"] = questions
            report["needs_context"].append(entry)
        else:
            report["ready"].append(entry)
    return report

@app.get("/api/goals/categorize")
def goals_categorize():
    df = load_goals()
    df = categorize(df)
    return {
        "summary": summarize(df),
        "sample": df.head(20).to_dict(orient="records"),
    }

@app.get("/api/nudge/next")
def nudge_next():
    suggestion = smart_suggest_next_task()
    suggestion["attention"] = ATTENTION.get("last", 0.5)
    return suggestion

class CheckIn(BaseModel):
    task: str
    done: bool
    perceived_difficulty: int  # 1..5
    mood: int  # 1..5

@app.post("/api/checkin/daily")
def checkin_daily(ci: CheckIn):
    path = "app/data/private_goals_from_backlog.csv"
    if not os.path.exists(path):
        return {"error": "goals file missing"}
    df = pd.read_csv(path)
    if "task" not in df.columns or "current_skill" not in df.columns:
        return {"error": "goals file missing required columns"}
    mask = df["task"].fillna("") == ci.task
    if mask.any():
        if ci.done:
            if ci.perceived_difficulty >= 3:
                df.loc[mask, "current_skill"] = (df.loc[mask, "current_skill"] + 0.2).clip(0, 10)
            elif ci.perceived_difficulty <= 2:
                df.loc[mask, "current_skill"] = (df.loc[mask, "current_skill"] + 0.1).clip(0, 10)
        df.loc[mask, "last_mood"] = ci.mood
        df.to_csv(path, index=False)
    return {"ok": True, "updated": bool(mask.any())}

@app.get("/api/health")
def health():
    return {"ok": True}

class KindleImportRequest(BaseModel):
    path: str
    format: str = "auto"

@app.post("/api/kindle/import")
def kindle_import(req: KindleImportRequest):
    path = req.path
    notes = []
    if not os.path.exists(path):
        return {"error": f"File not found: {path}"}
    def push(n):
        if n.get("text"):
            notes.append(n)
    if req.format in ("auto","clippings") and path.lower().endswith(".txt"):
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            blob = f.read()
        for block in blob.split("=========="):
            lines = [x.strip() for x in block.strip().splitlines() if x.strip()]
            if len(lines) >= 3:
                title = lines[0]
                meta = lines[1]
                text = "\n".join(lines[2:])
                push({"title": title, "meta": meta, "text": text})
    else:
        df = pd.read_csv(path)
        for _, row in df.iterrows():
            push({"title": row.get("title","Unknown"), "meta": row.get("location",""), "text": row.get("text","")})
    out_path = os.path.join(os.path.dirname(__file__), "..", "data", "kindle_import.md")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# Kindle Import\n\n")
        for i, n in enumerate(notes, 1):
            f.write(f"## Note {i}: {n['title']}\n\n")
            f.write(f"> {n['text'].strip()}\n\n")
            if n.get("meta"): f.write(f"*{n['meta']}*\n\n")
    return {"count": len(notes), "output": out_path}
