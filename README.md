# Better Self

An integrated ritual system that keeps Obsidian, a web “power tools” app, and a shared Supabase backend in sync. Start every day in your note, call on AI when it helps, track your focus in real time, and close the loop each evening.

## Why It’s Different
- **Temporal models over generic productivity** – choose the version of you the day requires (Researcher, Career Builder, Poet, Parent, …) and align tasks accordingly.
- **Coherence first** – success is matching actions to values, not just checking boxes.
- **Closed-loop feedback** – focus sessions pull lightweight sensor data and push stats back into your daily note.
- **Single source of truth** – Supabase stores goals, tasks, sessions, and reflections for both the plugin and web app.

## Feature Snapshot
- **Obsidian Plugin**
  - Morning check-in and evening review templates
  - AI task generation that respects your temporal model, energy, and goals
  - Quick links to start focus sessions or interview practice in the web app
  - Supabase-backed goal/task sync
- **Web App (Next.js)**
  - Dashboard for launching focus, interview, schedule, and learning modes
  - Focus Mode: camera on, timer running, real-time (simulated) focus score
  - Interview Practice: record, transcribe (Whisper), score STAR coverage
  - Schedule & Learning views (stubs ready to wire to Supabase + calendar)
- **Supabase**
  - Tables for temporal models, goals, tasks, focus sessions, interviews, daily logs, flashcards
  - Migration script provided in `supabase/migrations/001_initial_schema.sql`

## Architecture At A Glance
```
Obsidian Plugin (TypeScript)
  ├─ Daily ritual commands
  ├─ Supabase client
  └─ Calls -> Web App API (AI task generation, focus/interview launch)

Web App / Next.js 14
  ├─ /focus                Deep work mode with live stats
  ├─ /interview            Behavioral practice w/ transcription + analysis
  ├─ /schedule             Placeholder for calendar optimizer
  ├─ /learn                Placeholder for spaced repetition
  └─ /api/*                Task generation + interview analysis endpoints

Supabase (Postgres)
  └─ goals, tasks, daily_logs, focus_sessions, interview_sessions, flashcards, ...
```

## Quick Start
1. **Supabase** – Create a project, run the SQL in `supabase/migrations/001_initial_schema.sql`, and copy the project URL + anon key.
2. **Web App** – `cd web-app && npm install && cp .env.local.example .env.local` → fill in Supabase and OpenAI keys → `npm run dev`.
3. **Obsidian Plugin** – `cd obsidian-plugin && npm install && npm run dev`. Copy `main.js` + `manifest.json` to your vault’s `.obsidian/plugins/better-self/` folder, reload Obsidian, enable the plugin, and paste your Supabase credentials into settings.
4. **Dogfood** – In Obsidian run “Better Self: Create Morning Check-In”, then “Generate Today’s Tasks”. Launch focus mode via the button—it opens http://localhost:3000/focus.

More detail lives in [SETUP.md](./SETUP.md). For automation, run `./quick-start.sh`.

## Workflow Loop
1. **Morning (5 min)** – Choose temporal model, log energy/mood, let GPT-4 generate tasks, sync to calendar.
2. **During Work** – Kick off focus blocks from the note → browser captures attention score → summary comes back later.
3. **Practice / Power Sessions** – Launch interview drills or other modes in the web app; recordings + analysis live in Supabase.
4. **Evening (5 min)** – Check off tasks, rate coherence, jot reflection + gratitude. Data updates dashboards automatically.

## Philosophy & References
Built on:
- Temporal Model Selection & Myth of Objectivity Hypothesis
- Learning science: spaced repetition (Ebbinghaus), mastery learning (Bloom)
- Focus research: ultradian rhythms (Rossi), attention drift (Csikszentmihalyi)
- Habit formation: implementation intentions (Gollwitzer), Tiny Habits (Fogg)

## Roadmap
- **MVP (now)** – Daily rituals, AI tasks, focus mode, interview practice, baseline schema.
- **Next** – Weekly retrospectives, Supabase-powered analytics dashboard, Google Calendar sync, richer spaced repetition.
- **Later** – Mobile companion, accountability sharing, real CV-based focus tracking, multi-agent planning.

## Contributing
This repo is evolving fast. If you want to help:
1. Fork the repo and branch from `main`.
2. Keep changes scoped; add tests if you touch Python pipelines.
3. Open a PR with context and screenshots/GIFs when relevant.

## License
MIT – use it, remix it, iterate on it.
