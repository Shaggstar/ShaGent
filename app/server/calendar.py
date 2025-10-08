# app/server/calendar.py
import requests, datetime
from typing import List, Tuple

def fetch_busy_from_ics(ics_url: str) -> List[Tuple[datetime.datetime, datetime.datetime, str]]:
    """Return a list of (start, end, title) from a Google Calendar ICS feed."""
    r = requests.get(ics_url, timeout=20)
    r.raise_for_status()
    text = r.text

    busy = []
    # Very light parser to avoid heavy deps. Works well on Google ICS.
    def _get(block, key):
        for line in block.splitlines():
            if line.startswith(key + ":"):
                return line.split(":", 1)[1].strip()
        return ""

    for raw_event in text.split("BEGIN:VEVENT")[1:]:
        start = _get(raw_event, "DTSTART")
        end   = _get(raw_event, "DTEND")
        summ  = _get(raw_event, "SUMMARY") or "busy"
        # Google ICS typically uses local or UTC formats. Handle the common ones.
        def parse_dt(s):
            if s.endswith("Z"):
                return datetime.datetime.strptime(s, "%Y%m%dT%H%M%SZ")
            if "T" in s:
                return datetime.datetime.strptime(s, "%Y%m%dT%H%M%S")
            return datetime.datetime.strptime(s, "%Y%m%d")
        try:
            sdt = parse_dt(start)
            edt = parse_dt(end)
            busy.append((sdt, edt, summ))
        except Exception:
            continue
    return busy
