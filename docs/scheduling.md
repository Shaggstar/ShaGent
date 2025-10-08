# Scheduling & Energy Curves

An energy curve encodes how capable you are of doing high-effort work across the day.

Run the server:
```bash
uvicorn app.server.main:app --reload --port 9999
```
Then call:
```bash
curl -X POST http://localhost:9999/api/schedule -H "Content-Type: application/json" -d '{
  "tasks":[
    {"title":"Poem edit","minutes":50,"energy":"high","priority":1},
    {"title":"Inbox zero","minutes":25,"energy":"low","priority":3}
  ],
  "day_start":"09:00",
  "day_end":"17:30",
  "energy_curve":{"09:00":0.6,"10:00":0.8,"11:00":0.9,"13:00":0.7,"15:00":0.6,"16:00":0.5},
  "calendar_csv":"app/data/calendar_sample.csv"
}'
```
