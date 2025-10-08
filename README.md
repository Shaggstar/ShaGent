# ShAgent — Better Self App

A self-optimization system that uses AI to make you better, not weaker. ShAgent helps you set goals, track mastery, focus deeply, and grow a personal knowledge graph. It works with Obsidian for writing and note-taking, and includes a schedule optimizer, agile rituals, and optional sensor-based feedback. Privacy first by default.

## Why this exists

- Motivation is most of the solution. We keep standards high and give strong support.
- Closed-loop feedback grows skill. Measure state, act, reflect, adjust.
- AI should amplify attention and effort, not replace them.

## Features

- **Goals and OKRs**: Dynamic objectives, key results, and skill trees.
- **Schedule optimizer**: Plans blocks by priority, energy, and focus windows.
- **Writing coach for Obsidian**: Six-layer analysis (grammar, clarity, style, content, audience or SEO, related exemplars) with inline highlights and quick fixes.
- **Knowledge graph growth**: Auto-link notes and import Kindle highlights.
- **Agile rituals**: Daily stand-in, weekly sprint plan, retro analytics.
- **Feedback and sensors** (optional): Webcam and mic to estimate focus and stress. Built for low or no extra cost.

## Architecture

```
app/
  core/
    agent_pipeline.py      # goals -> tasks -> reflection loop
    scheduler.py           # constraint-based scheduler
    feedback_loop.py       # closed-loop learning and sensors
    data_models.py         # goals, skills, states
  integrations/
    obsidian_plugin/       # TypeScript plugin for writing feedback
    wearable_input/        # camera, mic, or watch hooks (optional)
    kindle_ingest/         # import highlights
  ui/
    mobile/                # React Native or Flutter later
    web/                   # basic web dashboard prototype
  data/
    sample_goals_public.csv
    private_goals_template.csv  # ignored by git
  config/
    settings.yaml
    prompts/               # LLM prompts
```

See `docs/architecture.md` for diagrams and data flows.

## Quick start

### 1) Clone and set up
```bash
git clone https://github.com/Shaggstar/ShaGent.git
cd ShaGent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Configure
Edit `app/config/settings.yaml` to set your model provider and privacy options.
- By default grammar and clarity run locally if you enable a small local model.
- Style and content checks can use a hosted model if you choose.

### 3) Run the base loop
```bash
python scripts/run_agentic_loop.py
```

### 4) Install the Obsidian plugin
Copy `app/integrations/obsidian_plugin` into your vault’s `.obsidian/plugins/` folder.
Reload Obsidian and run **Analyze current note** from the command palette.

## Low-cost defaults

- Grammar and clarity: local model via `lmstudio` or `ollama` if you enable it.
- Style, content, audience: one compact API call per note.
- Sensors: webcam and mic only, no dedicated hardware required.

## Privacy

- Personal goals live in `app/data/private_goals_template.csv`, which git ignores.
- You control all API calls in `config/models.yaml` and `config/settings.yaml`.
- Everything works offline for core note-taking and planning.

## Example goals

See `app/data/sample_goals_public.csv` for a starting point. Replace with your own, and keep private copies in `app/data/private/` or in your vault.

## Contributing

1. Create a feature branch.
2. Add tests in `tests/` if you change core logic.
3. Open a PR with a short rationale.

## License

MIT
