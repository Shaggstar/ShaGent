# Better Self – Setup Guide

## Prerequisites
- Node.js 18+
- npm
- Obsidian desktop app
- Supabase account (free tier works)
- OpenAI API key

---

## 1. Supabase Setup
1. Sign in at [supabase.com](https://supabase.com) and create a new project.
2. In **Project Settings → API**, copy your:
   - Project URL (e.g. `https://xxxxx.supabase.co`)
   - `anon/public` key
3. Open **SQL Editor** and run the migration in `supabase/migrations/001_initial_schema.sql`.
   ```sql
   -- copy the file contents and execute them in Supabase
   ```
4. (Optional) Enable Row Level Security and policies once you are ready for production.

---

## 2. Web App Setup
```bash
cd web-app

# Install dependencies
npm install

# Configure environment variables
cp .env.local.example .env.local
# Then edit .env.local with:
# NEXT_PUBLIC_SUPABASE_URL=...
# NEXT_PUBLIC_SUPABASE_ANON_KEY=...
# OPENAI_API_KEY=...

# Start the dev server
npm run dev
```
The web dashboard runs at http://localhost:3000.

---

## 3. Obsidian Plugin Setup
```bash
cd obsidian-plugin

# Install dependencies
npm install

# Build (or watch) the plugin
npm run dev
```
1. In your Obsidian vault, create `.obsidian/plugins/better-self/`.
2. Copy `obsidian-plugin/main.js` and `obsidian-plugin/manifest.json` into that folder.
3. Restart Obsidian or reload plugins (Cmd/Ctrl + R).
4. Enable **Better Self** in Community Plugins.
5. Open the plugin settings and paste your Supabase URL, Supabase anon key, and web-app URL.

---

## 4. First Run
**In Obsidian**
- Command Palette → “Better Self: Create Morning Check-In”.
- Fill out energy and temporal model.
- Command Palette → “Better Self: Generate Today’s Tasks”.

**In the Web App**
- Go to http://localhost:3000/focus and allow camera access.
- Start a Pomodoro or Deep Work block.
- Visit /interview for mock interview practice.

---

## 5. Daily Workflow Snapshot
- **Morning (5 min)**: Create the daily note, choose temporal model, generate tasks, review schedule.
- **During work**: Launch focus sessions from the Obsidian note, capture attention data, update tasks.
- **Afternoon practice**: Run interview drills or other power tools in the web app.
- **Evening (5 min)**: Fill the evening review, log coherence, sync tasks to Supabase.

---

## Troubleshooting
- **Plugin missing**: Ensure files are in `YOUR_VAULT/.obsidian/plugins/better-self/`, then reload Obsidian.
- **API errors**: Confirm `.env.local` has correct keys and that your Supabase project is live.
- **Camera blocked**: Allow permissions in your browser (Chrome/Edge recommended).

---

## Suggested Next Steps
1. Populate the `temporal_models`, `goals`, and `tasks` tables in Supabase with seed data.
2. Dogfood for a few days—note pain points in templates, AI output, and scheduling.
3. Hook up Supabase reads/writes in the Next.js pages (`focus`, `interview`, `schedule`, `learn`).
4. Implement Google Calendar integration for automatic time blocks.
5. Plan a weekly retro ritual (new command + dashboard view) to close the loop.

---

## Development Tips
- `npm run dev` (web) and `npm run dev` (plugin) both watch for changes. Reload Obsidian after each plugin build.
- Add new DB changes as additional files under `supabase/migrations/`.
- Keep API keys out of git—`.env.local` is gitignored by default.
- Before shipping, enable Supabase RLS policies to scope data per user.
