"""CLI for waybar-salah — Islamic prayer times in your Waybar."""

import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

import requests

DIR = Path.home() / ".config" / "waybar-salah"
CACHE_FILE = DIR / "cache.json"
CONFIG_FILE = DIR / "config.json"

API = "https://api.aladhan.com/v1/timingsByCity"
IP_API = "http://ip-api.com/json/?fields=city,country"

METHOD = 1
SUNRISE_FORBIDDEN = 15
ZENITH_FORBIDDEN = 5
ORDER = ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]


def load_config():
    if not CONFIG_FILE.exists():
        return None
    try:
        return json.loads(CONFIG_FILE.read_text())
    except Exception:
        return None


def save_config(city, country):
    DIR.mkdir(parents=True, exist_ok=True)
    data = {"city": city, "country": country}
    old = load_config()
    if old and "mode" in old:
        data["mode"] = old["mode"]
    CONFIG_FILE.write_text(json.dumps(data, indent=2))


def load_mode():
    cfg = load_config()
    return cfg.get("mode", "0") if cfg else "0"


def toggle_mode():
    cfg = load_config() or {}
    cur = cfg.get("mode", "0")
    cfg["mode"] = "1" if cur == "0" else "0"
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))


def detect_location():
    try:
        r = requests.get(IP_API, timeout=10)
        r.raise_for_status()
        d = r.json()
        return d.get("city"), d.get("country")
    except Exception:
        return None, None


def load_cache():
    if not CACHE_FILE.exists():
        return None
    try:
        d = json.loads(CACHE_FILE.read_text())
        if d.get("date") == str(date.today()):
            return d["timings"]
    except Exception:
        pass
    return None


def fetch(city, country):
    try:
        r = requests.get(
            API,
            params={"city": city, "country": country, "method": METHOD},
            timeout=10,
        )
        r.raise_for_status()
        raw = r.json()["data"]["timings"]
        wanted = {k: raw[k] for k in ORDER if k in raw}
        DIR.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(
            json.dumps({"date": str(date.today()), "timings": wanted}, indent=2)
        )
        return wanted
    except Exception:
        return None


def mins(t):
    t = datetime.strptime(t.strip(), "%H:%M").time()
    return t.hour * 60 + t.minute


def now_mins():
    n = datetime.now()
    return n.hour * 60 + n.minute


def fmt_dur(m):
    if m >= 60:
        h, r = divmod(m, 60)
        return f"{h}h{r}m" if r else f"{h}h"
    return f"{m}m"


def fmt_time(t):
    h, m = t.strip().split(":")
    return f"{int(h)}:{m}"


def state(timings):
    now = now_mins()
    p = {k: mins(timings[k]) for k in ORDER if k in timings}

    f, r, d, a, g, i = (
        p["Fajr"],
        p["Sunrise"],
        p["Dhuhr"],
        p["Asr"],
        p["Maghrib"],
        p["Isha"],
    )
    re = r + SUNRISE_FORBIDDEN
    ds = d - ZENITH_FORBIDDEN

    slots = [
        ("Fajr", f, r, "current"),
        ("Sunrise", r, re, "forbidden"),
        ("Morning", re, ds, "next"),
        ("Zenith", ds, d, "forbidden"),
        ("Dhuhr", d, a, "current"),
        ("Asr", a, g, "current"),
        ("Maghrib", g, i, "current"),
        ("Isha", i, 1440, "current"),
    ]
    for label, start, end, cls in slots:
        if start <= now < end:
            return label, end - now, cls
    if now < f:
        return "Isha", f - now, "current"
    return "Unknown", 0, "unknown"


def next_prayer(timings):
    now = now_mins()
    p = {k: mins(timings[k]) for k in ORDER if k in timings}
    for k in ORDER:
        if k in p and now < p[k]:
            return k, p[k] - now
    return "Fajr", 1440 - now + p["Fajr"]


def schedule(timings):
    return [(k, timings[k]) for k in ORDER if k in timings]


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--toggle":
        toggle_mode()
        os.system("pkill -RTMIN+14 waybar 2>/dev/null")
        return

    if len(sys.argv) > 1 and sys.argv[1] == "--reconfigure":
        city, country = detect_location()
        if city and country:
            save_config(city, country)
            print(f"Location set to {city}, {country}")
        else:
            print("Could not detect location. Check internet.")
        return

    # Load or auto-detect location
    config = load_config()
    if config is None:
        city, country = detect_location()
        if city and country:
            save_config(city, country)
        else:
            print(json.dumps({"text": "?", "class": "error", "tooltip": "Could not detect location. Run --reconfigure", "alt": "error"}))
            sys.exit(1)
    else:
        city = config["city"]
        country = config["country"]

    mode = load_mode()

    timings = load_cache()
    if timings is None:
        timings = fetch(city, country)
    if timings is None:
        print(
            json.dumps(
                {
                    "text": "?",
                    "class": "error",
                    "tooltip": "Prayer times unavailable\nCheck internet",
                    "alt": "error",
                }
            )
        )
        sys.exit(1)

    label, remaining, cls = state(timings)

    if mode == "1":
        n, nr = next_prayer(timings)
        text = f"{n} in {fmt_dur(nr)}"
        cls = "next"
        detail = f"Next: {n}"
    else:
        if cls == "current":
            text = f"{label} {fmt_dur(remaining)} remaining"
            detail = f"{label} {fmt_dur(remaining)} left"
        elif cls == "forbidden":
            text = f"Forbidden {fmt_dur(remaining)}"
            detail = f"Forbidden — {fmt_dur(remaining)} left"
        else:
            n, nr = next_prayer(timings)
            text = f"{n} in {fmt_dur(nr)}"
            detail = f"Next: {n}"

    lines = [detail, ""]
    for n, t in schedule(timings):
        lines.append(f"{n}: {fmt_time(t)}")

    print(
        json.dumps(
            {
                "text": text,
                "class": cls,
                "tooltip": "\n".join(lines),
                "alt": label,
            }
        )
    )


if __name__ == "__main__":
    main()
