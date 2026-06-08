# Prayer Times — Waybar Widget

Shows Islamic prayer times in your status bar — auto-detects location via IP.

## What it does

- Displays how much time is left in the current prayer (e.g. "Isha 20m remaining")
- Shows "Forbidden 12m" during sunrise and midday periods when prayer isn't allowed
- Shows time until the next prayer when nothing is active (e.g. "Dhuhr in 1h")

## How to use

- **Left-click** the prayer time to switch between two display modes:
  - Context-aware (shows what matters right now)
  - Always show time until next prayer
- **Hover** over it to see the complete daily timetable

## Installation

### From PyPI (recommended)

```bash
uv tool install waybar-salah
```

Or with pip:

```bash
pip install waybar-salah
```

### From source

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv tool install git+https://github.com/shahriyardx/waybar-salah
```

Or from a local copy:

```bash
cd /path/to/prayer-times
uv tool install .
```

Then add to your Waybar config:

```json
"custom/prayer": {
    "exec": "waybar-salah",
    "return-type": "json",
    "interval": 30,
    "on-click": "waybar-salah --toggle",
    "tooltip": true
}
```

Add some CSS to colour the states:

```css
#custom-prayer.current { color: #a6e3a1; }
#custom-prayer.forbidden { color: #f38ba8; }
#custom-prayer.next { color: #89b4fa; }
```

## Customisation

Open `src/waybar_salah/main.py` and change `CITY`, `COUNTRY`, or `METHOD` at the top.

| Method | Organisation |
|--------|-------------|
| 1 | University of Islamic Sciences, Karachi |
| 2 | Islamic Society of North America |
| 3 | Muslim World League |
| 4 | Umm Al-Qura, Makkah |
| 8 | University of Tehran |

## Files

```
src/waybar_salah/main.py     # main logic
pyproject.toml               # package config
cache.json                   # daily timings (auto-generated)
```
