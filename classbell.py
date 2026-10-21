#!/usr/bin/env python3
"""ClassBell: push tomorrow's class schedule to WeChat via ServerChan.

Reads a schedule JSON file, computes tomorrow's teaching week from the
semester start date, and sends the class list (time, classroom, course
name) through ServerChan (https://sct.ftqq.com).

The ServerChan SendKey is read from the environment variable
SERVERCHAN_SENDKEY. It is never stored in this repo.

Usage:
    export SERVERCHAN_SENDKEY=SCTxxxxxxxxxxxxxxxx
    python3 classbell.py                      # push tomorrow's classes
    python3 classbell.py --dry-run            # print the message, do not send
    python3 classbell.py --for-date 2026-10-20 --dry-run
"""
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

WEEKDAY_CN = {1: "周一", 2: "周二", 3: "周三", 4: "周四", 5: "周五", 6: "周六", 7: "周日"}
DEFAULT_SCHEDULE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schedule.json")


def load_schedule(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def tomorrow_classes(sched, today):
    tomorrow = today + timedelta(days=1)
    start = date.fromisoformat(sched["semester_start"])
    week = (tomorrow - start).days // 7 + 1
    weekday = tomorrow.isoweekday()
    classes = []
    if 1 <= week <= sched["max_week"]:
        for c in sched["days"].get(str(weekday), []):
            if week in c["weeks"]:
                classes.append(c)
    return tomorrow, week, weekday, classes


def build_message(tomorrow, weekday, classes):
    wd = WEEKDAY_CN[weekday]
    if not classes:
        return f"明日（{wd}）无课", ""
    parts = [f"{c['periods']} {c['course']} @ {c['room']}" for c in classes]
    title = f"明日课程（{wd}）： " + "；".join(parts)
    desp_lines = [f"- **{c['periods']}** {c['course']}｜{c['room']}" for c in classes]
    desp = f"## 明日（{tomorrow:%m月%d日} {wd}）课程\n" + "\n".join(desp_lines)
    return title, desp


def send_serverchan(sendkey, title, desp):
    """POST to ServerChan. Returns True on success."""
    url = f"https://sctapi.ftqq.com/{sendkey}.send"
    data = urllib.parse.urlencode({"title": title, "desp": desp}).encode()
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    return result.get("code") == 0


def main():
    ap = argparse.ArgumentParser(description="Push tomorrow's classes to WeChat via ServerChan.")
    ap.add_argument("--schedule", default=DEFAULT_SCHEDULE, help="path to schedule JSON")
    ap.add_argument("--tz", default="Asia/Shanghai", help="timezone for 'today' (default Asia/Shanghai)")
    ap.add_argument("--dry-run", action="store_true", help="print the message only, do not send")
    ap.add_argument("--for-date", default=None, help="YYYY-MM-DD to treat as today (testing)")
    args = ap.parse_args()

    sched = load_schedule(args.schedule)
    if args.for_date:
        today = date.fromisoformat(args.for_date)
    else:
        today = datetime.now(ZoneInfo(args.tz)).date()
    tomorrow, week, weekday, classes = tomorrow_classes(sched, today)
    title, desp = build_message(tomorrow, weekday, classes)
    print(f"date={tomorrow} week={week} weekday={WEEKDAY_CN[weekday]} classes={len(classes)}")
    print(f"TITLE: {title}")
    if args.dry_run:
        print(desp)
        return
    sendkey = os.environ.get("SERVERCHAN_SENDKEY", "")
    if not sendkey:
        print("ERROR: environment variable SERVERCHAN_SENDKEY is not set.", file=sys.stderr)
        sys.exit(2)
    ok = send_serverchan(sendkey, title, desp)
    print("PUSH_OK" if ok else "PUSH_FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
