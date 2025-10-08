import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .calendar import fetch_busy_from_ics
from .goals import categorize, load_goals, summarize
from .llm_router import run as llm_run

app = FastAPI(title="ShAgent Server")
app.mount("/ui", StaticFiles(directory="app/ui/web", html=True), name="ui")

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
    df = categorize(load_goals())
    att = ATTENTION.get("last", 0.5)
    if att >= 0.6:
        pref = ["Writing", "Career", "Learning", "Mental Health"]
    elif att >= 0.35:
        pref = ["Career", "Learning", "Writing", "Mental Health"]
    else:
        pref = ["Mental Health", "Writing", "Learning", "Career"]
    if "status" not in df.columns:
        df["status"] = "Backlog"
    for cat in pref:
        match = df[
            df["categories"].str.contains(cat, na=False)
            & (~df["status"].str.contains("Done", na=False))
        ]
        if not match.empty:
            row = match.iloc[0]
            return {
                "attention": att,
                "suggestion": row.get("task") or row.get("objective"),
                "category": cat,
                "reason": "Matches your current attention level",
            }
    return {"attention": att, "suggestion": "Review your backlog and pick one small task."}

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
