"""Scheduler CLI.

Modes:
    once        Run a single refresh; rebuild the corpus only if a page changed.
    check       Fetch and compare only; report what would change, write nothing.
    daemon      Loop every --interval-hours, refreshing when needed.

Exit codes:
    0   ok (fresh, or rebuilt successfully)
    1   refresh failed
    2   check mode: changes are available (would be rebuilt)

The daemon does not require MISTRAL_API_KEY; only answer generation does.
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def run_once(force: bool, check_only: bool = False) -> int:
    from code.scheduler.refresh import RefreshError, refresh

    try:
        report = refresh(check_only=check_only, force=force)
    except RefreshError as exc:
        print(f"REFRESH FAILED: {exc}", file=sys.stderr)
        return 1

    print(f"At {report.refetched_at}")
    if check_only:
        if report.any_change:
            print(f"CHANGES AVAILABLE: {len(report.changed)} document(s) would be rebuilt.")
            return 2
        print("UP TO DATE: no changes available.")
        return 0

    if not report.any_change:
        return 0

    print("REBUILT:")
    for name, meta in report.stages.items():
        print(f"  - {name}: {meta}")
    return 0


def run_daemon(interval_hours: float, force_first: bool) -> int:
    from code.scheduler.refresh import RefreshError, refresh

    interval_seconds = max(30, int(interval_hours * 3600))
    tick = 0
    print(f"DAEMON START: polling every {interval_hours:g}h (first run force={force_first})")
    while True:
        tick += 1
        print(f"[{_now()}] check #{tick}")
        try:
            report = refresh(check_only=False, force=force_first and tick == 1)
        except RefreshError as exc:
            print(f"[{_now()}] REFRESH FAILED: {exc}", file=sys.stderr)
        else:
            if report.rebuilt:
                print(f"[{_now()}] REBUILT: {report.changed}")
            else:
                print(f"[{_now()}] up to date")
        print(f"[{_now()}] sleeping {interval_seconds}s…")
        time.sleep(interval_seconds)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="code.scheduler",
        description="Refresh and schedule the Groww FAQ corpus.",
    )
    parser.add_argument(
        "--mode",
        choices=("once", "check", "daemon"),
        default="once",
        help="once=rebuild if changed; check=report only; daemon=loop",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="rebuild the corpus even when no source text changed",
    )
    parser.add_argument(
        "--interval-hours",
        type=float,
        default=24.0,
        help="polling interval for --mode daemon (default 24h)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.mode == "check":
        return run_once(force=False, check_only=True)
    if args.mode == "daemon":
        run_daemon(args.interval_hours, force_first=args.force)
        return 0  # unreachable
    return run_once(force=args.force)

if __name__ == "__main__":
    raise SystemExit(main())