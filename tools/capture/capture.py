#!/usr/bin/env python3
"""Screenshot capture tool for SAP AI Launchpad / Generative AI Hub evidence.

Two subcommands:

  login   Open a HEADED browser at the configured login URL. You sign in manually
          (SAP Universal ID, possibly MFA). Press Enter in the terminal and the
          authenticated browser storage state is saved to ``.auth/state.json``.

  shoot   Reuse that saved state to visit every target in ``targets.yaml``, wait
          for network idle + a selector, hide any per-target "mask" elements
          (PII such as your email), and save 1600x900 PNGs into docs/screenshots/.

Security: this tool never handles or logs your credentials — you type them into
the browser yourself. The saved storage state (cookies/tokens) lives in
``tools/capture/.auth/`` which is gitignored. Do not commit it.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
AUTH_DIR = HERE / ".auth"
STATE_PATH = AUTH_DIR / "state.json"
DEFAULT_TARGETS = HERE / "targets.yaml"
SCREENSHOTS_DIR = REPO_ROOT / "docs" / "screenshots"

_PLACEHOLDER = "REPLACE-ME"


def _require_deps() -> tuple:
    """Import third-party deps lazily with a friendly message if missing."""
    try:
        import yaml
        from playwright.sync_api import Error as PWError
        from playwright.sync_api import TimeoutError as PWTimeout
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # pragma: no cover - exercised only before setup
        sys.exit(
            f"Missing dependency ({exc.name}). Set the tool up first:\n"
            f"    cd {HERE}\n"
            "    ./setup.sh\n"
        )
    return yaml, sync_playwright, PWError, PWTimeout


def load_config(path: Path) -> dict:
    yaml, *_ = _require_deps()
    if not path.is_file():
        sys.exit(f"Config not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        sys.exit(f"Config must be a YAML mapping: {path}")
    return data


def _viewport(cfg: dict) -> dict:
    vp = cfg.get("viewport") or {}
    return {"width": int(vp.get("width", 1600)), "height": int(vp.get("height", 900))}


def _is_placeholder(value: str | None) -> bool:
    return not value or _PLACEHOLDER in value


def _apply_masks(page, selectors: list[str]) -> int:
    """Hide each mask selector via visibility:hidden. Returns count applied."""
    sels = [s for s in selectors if s]
    if not sels:
        return 0
    css = ", ".join(sels) + " { visibility: hidden !important; }"
    page.add_style_tag(content=css)
    return len(sels)


def cmd_login(cfg: dict) -> int:
    _, sync_playwright, _, PWTimeout = _require_deps()
    login_cfg = cfg.get("login") or {}
    url = login_cfg.get("url")
    if _is_placeholder(url):
        sys.exit("Set `login.url` in targets.yaml to your AI Launchpad URL first.")

    AUTH_DIR.mkdir(parents=True, exist_ok=True)
    viewport = _viewport(cfg)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        print(f"Opening {url}")
        page.goto(url, wait_until="domcontentloaded")
        print(
            "\nLog in manually in the browser window (SAP Universal ID / MFA).\n"
            "Leave the browser open and come back here when you're fully signed in."
        )
        try:
            input("\nPress Enter to save the session... ")
        except (EOFError, KeyboardInterrupt):
            browser.close()
            print("\nCancelled — no state saved.")
            return 1

        ready = login_cfg.get("ready_selector")
        if ready:
            try:
                page.wait_for_selector(ready, timeout=5000)
                print("Confirmed: logged-in element is present.")
            except PWTimeout:
                print("Warning: ready_selector not found — saving state anyway.")

        context.storage_state(path=str(STATE_PATH))
        browser.close()

    print(f"\nSaved auth state -> {STATE_PATH.relative_to(REPO_ROOT)} (gitignored).")
    print("Next: ./capture shoot")
    return 0


def cmd_shoot(cfg: dict, *, headed: bool) -> int:
    _, sync_playwright, PWError, PWTimeout = _require_deps()
    if not STATE_PATH.is_file():
        sys.exit("No saved auth state. Run `./capture login` first.")

    targets = cfg.get("targets") or []
    if not targets:
        sys.exit("No `targets` defined in targets.yaml.")

    viewport = _viewport(cfg)
    timeout = int(cfg.get("timeout_ms", 30000))
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    results: list[tuple[str, str, str]] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not headed)
        context = browser.new_context(viewport=viewport, storage_state=str(STATE_PATH))
        page = context.new_page()

        for target in targets:
            name = target.get("name", "(unnamed)")
            url = target.get("url", "")
            output = target.get("output")

            if _is_placeholder(url) or not output:
                results.append((name, "SKIP", "url/output not set yet"))
                continue

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=timeout)
                # Best-effort network idle; SPAs may never fully settle, so don't fail on it.
                try:
                    page.wait_for_load_state("networkidle", timeout=timeout)
                except PWTimeout:
                    pass

                wait_for = target.get("wait_for")
                if wait_for:
                    page.wait_for_selector(wait_for, timeout=timeout)

                masked = _apply_masks(page, target.get("mask") or [])
                dest = SCREENSHOTS_DIR / output
                page.screenshot(path=str(dest), full_page=False)
                detail = str(dest.relative_to(REPO_ROOT))
                if masked:
                    detail += f"  (masked {masked})"
                results.append((name, "OK", detail))
            except (PWTimeout, PWError) as exc:
                results.append((name, "FAIL", str(exc).splitlines()[0][:80]))
                continue

        browser.close()

    _print_summary(results)
    return 1 if any(status == "FAIL" for _, status, _ in results) else 0


def _print_summary(results: list[tuple[str, str, str]]) -> None:
    width = max((len(name) for name, _, _ in results), default=4)
    print("\nCapture summary")
    print("-" * (width + 30))
    for name, status, detail in results:
        print(f"  {name.ljust(width)}  {status.ljust(4)}  {detail}")
    ok = sum(1 for _, s, _ in results if s == "OK")
    print("-" * (width + 30))
    print(f"  {ok}/{len(results)} captured")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="capture",
        description="Capture masked SAP GenAI Hub screenshots into docs/screenshots/.",
    )
    parser.add_argument(
        "--config", type=Path, default=DEFAULT_TARGETS, help="Path to targets.yaml"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("login", help="Headed manual login; saves auth state.")
    shoot = sub.add_parser("shoot", help="Capture screenshots using saved state.")
    shoot.add_argument(
        "--headed", action="store_true", help="Run the capture browser visibly."
    )

    args = parser.parse_args(argv)
    cfg = load_config(args.config)

    if args.command == "login":
        return cmd_login(cfg)
    return cmd_shoot(cfg, headed=args.headed)


if __name__ == "__main__":
    raise SystemExit(main())
