# Robotics App Directory integration readiness

Prepared on `integration/robotics-directory-latest-dev` in an isolated worktree,
based on freshly fetched `origin/dev` at
`18e2adb1052eda7dc54f0c78253997b588567984`. This is a forward application of the
Robotics directory change from `64ddfc4e`; no existing branch is overwritten,
rebased, merged into dev, pushed, or deployed.

## Integration decisions

- Preserve all six existing AppDefinition calls exactly (verified by AST
  comparison with the fetched dev). Append Robotics as the seventh app.
- Keep dev's approved-logo rendering path, original asset bytes, parent branding,
  welcome banner, and Music picker/workspace launch semantics. Register the
  unchanged official Robotics PNG in that same product-logo system.
- Keep dev's existing deployment override helper. Robotics also accepts the
  shared `SUITE_APP_URL_ROBOTICS` convention, with `ROBOTICS_APP_URL` and
  `[suite_apps] robotics_url` compatibility. Only real non-loopback HTTPS URLs
  are accepted for deployed configuration.
- Render the grid in groups of three, yielding rows of 3, 3, and 1. Existing
  Streamlit mobile behavior and responsive styles are retained unchanged.
- Missing deployment configuration keeps the Robotics card visible and Open
  disabled. No deployed Robotics address is invented.
- Authentication and all other application state/behavior remain unchanged.

## Local navigation configuration

Start Command Center from this integration worktree with the existing Robotics
virtual environment (absolute path shown to avoid another installation):

```powershell
Set-Location C:\Users\danie\Documents\GitHub\daniel-ai-robotics\.worktrees\command-center-integration
$env:ROBOTICS_LOCAL_DEV = "1"
$env:ROBOTICS_DEV_URL = "http://127.0.0.1:8501/"
C:\Users\danie\Documents\GitHub\daniel-ai-robotics\.venv\Scripts\python.exe -m streamlit run ai_command_center.py --server.address 127.0.0.1 --server.port 8502 --server.headless true --browser.gatherUsageStats false
```

Open `http://127.0.0.1:8502`. Keep the existing Robotics server on port 8501
running. Explicit local mode produces an Open target on port 8501 and a notice
that its server must be running. Do not enable local mode on the public deployment.

Robotics' ignored local navigation setting was verified to point to the user's
current **deployed** Command Center:
`https://daniel-ai-command-center-ion4vh2cvo7bgdnkuktrb3.streamlit.app/`.
It has not been silently redirected to an unstarted local server. For an eventual
two-way local test, set `[suite_navigation] command_center_url` in the Robotics
ignored secrets file to `http://127.0.0.1:8502/` and `local_development = true`,
then restore the deployed destination afterward if desired. Do not copy Supabase
secrets into this worktree or tracked files.

## Validation and blockers

Final focused run: **30 tests passed in 5.36 seconds**.

Focused directory tests cover the actual card builder, complete seven-card grid,
approved artwork, configured Open action, disabled state, future HTTPS URLs,
Suite URL overrides, and workspace context. Additional regression checks cover
dev's existing approved logos, Music directory entry behavior, and deployment
overrides. A pytest temporary-directory permission error was resolved by rerunning
the affected test with a new workspace-owned temporary directory; no code fix or
system permission change was needed.

The existing Robotics server returned HTTP 200; the local Open target was verified
programmatically as port 8501. **No Command Center server was started on port
8502 and no browser clicks or desktop/mobile visual acceptance were completed.**
Available RAM was only 0.76–0.94 GiB during checks, with 94–95% system memory use;
starting another app/browser was deferred. Prior browser access was also blocked.
No unrelated process was stopped, and the user's Robotics server was preserved.

Ready for code review; live navigation and visual acceptance remain pending memory
headroom/browser access. After approval, integration/publication into the deployed
dev branch and a real Robotics HTTPS URL are still required for public Open.
