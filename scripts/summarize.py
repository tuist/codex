#!/usr/bin/env python3
"""Turn Once or Bazel logs into a job summary and a JSON record."""

import argparse
import collections
import json
import re
from pathlib import Path

# Once renders one line per action: "  <glyph> <target> <status> <duration>".
ONCE_ACTION = re.compile(r"^\s+[✓✗]\s+(\S+)\s+(\S+)\s+(\S+)\s*$")
# Bazel prints "//pkg:target    (cached) " or with a mnemonic suffix.
BAZEL_TARGET = re.compile(r"^(\S+)\s+(\(cached\)|\(cache hit\)|\(remote cache hit\))")
BAZEL_ELAPSED = re.compile(r"^INFO: Elapsed time: ([\d.]+)s")


def duration_seconds(value):
    match = re.fullmatch(r"([\d.]+)(ms|s|m)", value)
    if not match:
        return 0.0
    number, unit = float(match.group(1)), match.group(2)
    return {"ms": number / 1000, "s": number, "m": number * 60}[unit]


def parse_once(path):
    statuses = collections.Counter()
    seconds = collections.Counter()
    actions = []
    log = Path(path) if path else None
    if not log or not log.is_file():
        return {"statuses": {}, "action_seconds": {}, "slowest": [], "trailer": None, "cache_hits": 0}
    trailer = None
    cache_hits = 0
    for line in log.read_text(errors="replace").splitlines():
        match = ONCE_ACTION.match(line)
        if match:
            name, status, duration = match.groups()
            statuses[status] += 1
            seconds[status] += duration_seconds(duration)
            actions.append((duration_seconds(duration), name, status))
            if status in ("hit", "cached"):
                cache_hits += 1
        elif re.match(r"^\s+(Done|Failed)\s", line) or line.startswith("once: ran "):
            trailer = line.strip()
    actions.sort(reverse=True)
    return {
        "statuses": dict(statuses),
        "action_seconds": {k: round(v, 1) for k, v in seconds.items()},
        "slowest": [{"name": n, "status": s, "seconds": round(d, 1)} for d, n, s in actions[:10]],
        "trailer": trailer,
        "cache_hits": cache_hits,
    }


def parse_bazel(path):
    log = Path(path) if path else None
    if not log or not log.is_file():
        return {"cached": 0, "total": 0, "elapsed_seconds": 0.0, "trailer": None}
    cached = 0
    total = 0
    elapsed = 0.0
    for line in log.read_text(errors="replace").splitlines():
        if BAZEL_TARGET.match(line):
            total += 1
            cached += 1
        match = BAZEL_ELAPSED.match(line)
        if match:
            elapsed = float(match.group(1))
    return {"cached": cached, "total": total, "elapsed_seconds": elapsed, "trailer": None}


def minutes(value):
    return f"{int(value) / 60:.1f} min" if value else "n/a"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tool", choices=["once", "bazel"], default="once")
    for flag in [
        "os", "sha", "remote-cache", "graph-seconds", "build-seconds",
        "test-seconds", "test-status", "build-log", "test-log", "json",
    ]:
        parser.add_argument(f"--{flag}", default="")
    args = parser.parse_args()

    if args.tool == "once":
        build, test = parse_once(args.build_log), parse_once(args.test_log)
    else:
        build, test = parse_bazel(args.build_log), parse_bazel(args.test_log)

    record = {
        "tool": args.tool,
        "os": args.os,
        "sha": args.sha,
        "remote_cache": args.remote_cache == "true",
        "graph_seconds": int(args.graph_seconds or 0),
        "build_seconds": int(args.build_seconds or 0),
        "test_seconds": int(args.test_seconds or 0),
        "test_status": args.test_status,
        "build": build,
        "test": test,
    }
    if args.json:
        Path(args.json).write_text(json.dumps(record, indent=2))

    def counts(section):
        found = ", ".join(f"{v} {k}" for k, v in sorted(section["statuses"].items()))
        return found or section["trailer"] or "n/a"

    label = "Once" if args.tool == "once" else "Bazel"
    print(f"## {label} on `{args.os}` for openai/codex@{args.sha[:10]}\n")
    if args.tool == "once":
        print(f"Remote cache: **{'on' if record['remote_cache'] else 'off (cold baseline)'}**\n")
        print(
            "| Phase | Wall time | Actions |\n| --- | --- | --- |\n"
            f"| Graph load | {minutes(args.graph_seconds)} | |\n"
            f"| `once build` | {minutes(args.build_seconds)} | {counts(build)} |\n"
            f"| `once test` | {minutes(args.test_seconds)} | {counts(test)} |"
        )
    else:
        print(
            "| Phase | Wall time | Targets |\n| --- | --- | --- |\n"
            f"| `bazel build` | {minutes(args.build_seconds)} | "
            f"{build['cached']}/{build['total']} cached |\n"
            f"| `bazel test` | {minutes(args.test_seconds)} | "
            f"{test['cached']}/{test['total']} cached |"
        )
    if args.test_status not in ("", "0"):
        print(f"\n`{label.lower()} test` exited with status {args.test_status}.")
    for title, section in [("build", build), ("test", test)]:
        if section.get("slowest"):
            print(f"\n<details><summary>Slowest {title} actions</summary>\n")
            print("| Action | Status | Seconds |\n| --- | --- | --- |")
            for item in section["slowest"]:
                print(f"| `{item['name']}` | {item['status']} | {item['seconds']} |")
            print("\n</details>")


if __name__ == "__main__":
    main()
