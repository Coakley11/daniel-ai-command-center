# Daniel AI Command Center

Central hub and homepage for the **Daniel AI Suite** — one integrated AI ecosystem connecting music, investing, sports analytics, math intelligence, and future AI workflows.

## Apps in the ecosystem

- Music Practice Coach
- Investment Portfolio Analyzer
- Fantasy Baseball / Baseball Analytics
- NBA Playoff Companion
- Advanced Math Intelligence
- Future Lens (AI Transition Simulator)

## Run locally

```bash
pip install -r requirements.txt
streamlit run ai_command_center.py
```

## Status

Cross-app homepage with live activity when Supabase `[suite_activity]` secrets are configured; falls back to local `data/suite_activity.json` for development.

## Roadmap & planning

Product docs live in [`cursor-prompts/`](cursor-prompts/) — start with [`cursor-prompts/app_roadmap.md`](cursor-prompts/app_roadmap.md). Cursor updates these automatically when you ask for a roadmap, feature plan, or implementation plan (see `.cursor/rules/command-center-roadmap-docs.mdc`).
