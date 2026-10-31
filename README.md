# 🏎️ TDU Toolkit

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![No Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen.svg)]()

A lightweight, standalone collection of Python utilities for **Test Drive Unlimited (2006 / Platinum)**.
Designed for modders and players to easily manage custom radio stations and inspect binary race track (`.IGE`) files.

---

## ✨ Features

| Script | Purpose |
| :--- | :--- |
| **[`tdu_station_builder.py`](tdu_station_builder.py)** | Scans radio music folders, cleans up track numbers (`01. Artist - Title`), and automatically generates valid UTF-16 `.station` playlist files for in-game radio stations. |
| **[`tdu_radio_randomizer.py`](tdu_radio_randomizer.py)** | Shuffles and selects a random batch of tracks from your music library and copies them into your TDU savegame profile's custom radio station. |
| **[`tdu_track_analyzer.py`](tdu_track_analyzer.py)** | Inspects binary `.IGE` track files, parses `CHPT` (checkpoint), `CARP`, and `ENTI` chunks, and compares online vs. offline track differences side-by-side. |
| **[`tdu_track_finder.py`](tdu_track_finder.py)** | Searches `.IGE` files to find which file corresponds to a given race or challenge name (supporting both ASCII and UTF-16LE binary encodings). |

---

## 📋 Requirements

- **Python 3.8+**
- **Zero external dependencies** (uses standard library only — download and run immediately).

---

## ⚙️ Configuration (Optional)

All scripts feature **smart auto-detection**:
- Locates game directory via CLI flags, environment variables (`TDU_DIR`), Windows Registry, Steam paths, and standard install locations (`C:`, `D:`).
- Locates savegame directory via `Documents/Test Drive Unlimited/savegame` (including OneDrive).
- Automatically selects your player profile if only one profile exists.

If you prefer setting default paths once without passing flags each time, copy `config.example.json`:

```bash
cp config.example.json config.json
```

Example `config.json`:
```json
{
  "tdu_install_dir": "C:\\Program Files (x86)\\Atari\\Test Drive Unlimited",
  "savegame_dir": "",
  "profile_name": "MyProfile",
  "music_source_dir": "D:\\Music",
  "radio_station_name": "randomizer",
  "random_song_count": 30
}
```

---

## 🛠️ Usage

### 1. Generate Radio Station Playlists (`tdu_station_builder.py`)

Generates `.station` files for stations located in `<TDU>/Euro/Radio/` into `<TDU>/Euro/Bnk/Sound/Radio/`.

```bash
# Auto-detect TDU installation and generate playlists for all stations:
python tdu_station_builder.py

# Specify game directory explicitly:
python tdu_station_builder.py --tdu-dir "D:\Games\Test Drive Unlimited"

# Process specific stations only:
python tdu_station_builder.py --stations "Radio Djey" "Sweet Radio"
```

Expected audio file naming convention:
- `Artist - Title.mp3`
- `01. Artist - Title.mp3`
- `01 - Artist - Title.mp3`

---

### 2. Custom Radio Randomizer (`tdu_radio_randomizer.py`)

Shuffles and copies songs from your music library to your TDU savegame profile's custom radio folder.

```bash
# Basic usage (auto-detects savegame profile):
python tdu_radio_randomizer.py --source "D:\My Music"

# Pick 50 songs for a specific profile and station:
python tdu_radio_randomizer.py --source "D:\My Music" --profile "DefaultPlayer" --station "RockRadio" -n 50

# Dry-run (preview selected songs without copying):
python tdu_radio_randomizer.py --source "D:\My Music" --dry-run

# Keep existing files in destination (do not wipe before copying):
python tdu_radio_randomizer.py --source "D:\My Music" --no-clean
```

---

### 3. Track File Analyzer & Comparator (`tdu_track_analyzer.py`)

Inspects binary `.IGE` files or compares two track files to detect differences in checkpoint count, chunk size, or IDs.

```bash
# Inspect a single track file:
python tdu_track_analyzer.py "RMFE0049.IGE"

# Compare online vs offline versions side-by-side:
python tdu_track_analyzer.py "online RMFE0049.IGE" "offline RMFE0049.IGE"
```

Example comparison output:
```text
  # | Offset 1   | Offset 2   | Size 1   | Size 2   | ID 1  | ID 2  | Match?
----------------------------------------------------------------------------
  1 | 0x000140   | 0x000140   | 128      | 128      | 0     | 0     | MATCH
  2 | 0x0001C4   | 0x0001C4   | 132      | 132      | 1     | 1     | MATCH
```

---

### 4. Track Name Finder (`tdu_track_finder.py`)

Scans `.IGE` files in your game directory to find which file corresponds to a specific race or challenge name.

```bash
# Search across auto-detected <TDU>/Euro/Bnk/IGE folder:
python tdu_track_finder.py "Ride in hickam village"

# Search in a specific directory and stop at the first match:
python tdu_track_finder.py "Conquest of the west" --dir "D:\TDU_Mods\IGE" --first
```

---

## 📄 License

Distributed under the [MIT License](LICENSE). Feel free to use, modify, and share!
