# Screenshot capture tool

Produces the real, masked SAP screenshots referenced by the project README, so the
evidence is genuine (from your own trial session) rather than mocked up.

Built with [Playwright](https://playwright.dev/python/) (pinned in
`requirements.txt`). Two steps: log in once manually, then capture repeatedly.

## Setup

```bash
cd tools/capture
./setup.sh          # creates .venv, installs Playwright + Chromium
```

## 1. Configure targets

Edit [`targets.yaml`](targets.yaml). From a live AI Launchpad session, fill in:

- `login.url` — your AI Launchpad URL.
- each `targets[].url` — the page to screenshot.
- each `targets[].wait_for` — a selector proving the page rendered.
- each `targets[].mask` — selectors to hide (your email/username in the header,
  tenant ids, etc.). These are set to `visibility:hidden` before the shot.

Entries still containing `REPLACE-ME` are **skipped**, so you can fill them in one
at a time.

## 2. Log in (manual, headed)

```bash
./capture login
```

A real browser opens. Sign in with your SAP Universal ID (and MFA if prompted).
Back in the terminal, press **Enter** to save the authenticated session to
`.auth/state.json`.

## 3. Capture

```bash
./capture shoot            # headless, uses the saved session
./capture shoot --headed   # watch it run
```

Each target is visited, masked, and saved as a 1600×900 PNG in
`../../docs/screenshots/`. If a page fails to load or a selector times out, that
target is marked `FAIL` and the run continues; a summary table prints at the end.

## Security

- **Credentials are never handled or logged** by this tool — you type them into the
  browser yourself.
- `.auth/` (the saved cookies/tokens) and any `*cookies*.json` are **gitignored**.
  Never commit them.
