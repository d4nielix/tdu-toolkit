#!/usr/bin/env python3
"""
tdu_station_builder.py - Test Drive Unlimited Station Playlist Generator

Scans radio station directories for audio files, parses artist/title metadata,
and generates the corresponding .station playlist files in the game's sound directory.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import tdu_common as common

# Default radio stations in TDU (inside Euro/Radio/)
DEFAULT_STATIONS = ["Radio Djey", "Radio Bot", "Radio Classik", "Sweet Radio"]


def parse_filename(filename: str) -> Tuple[str, str]:
    """
    Parse audio filename into (artist, title).
    Handles patterns like:
    - "01. Artist - Title.mp3"
    - "01 - Artist - Title.mp3"
    - "Artist - Title.mp3"
    - "Title.mp3" (returns 'Unknown', 'Title')
    """
    stem, _ = os.path.splitext(filename)

    # Strip leading track numbers like "01. ", "01 - ", "01_ ", "1. "
    cleaned = re.sub(r"^\d+[\s\.\-_]+\s*", "", stem).strip()
    if not cleaned:
        cleaned = stem

    if " - " in cleaned:
        parts = cleaned.split(" - ", 1)
        artist, title = parts[0].strip(), parts[1].strip()
    elif "-" in cleaned:
        parts = cleaned.split("-", 1)
        artist, title = parts[0].strip(), parts[1].strip()
    else:
        artist, title = "Unknown", cleaned

    return artist or "Unknown", title or stem


def collect_audio_files(directory: Path, extensions: Set[str]) -> List[str]:
    """Return sorted list of audio filenames in the specified directory."""
    if not directory.is_dir():
        return []

    files = [
        f.name for f in directory.iterdir()
        if f.is_file() and f.suffix.lower() in extensions
    ]
    files.sort(key=lambda s: s.lower())
    return files


def generate_station_file(
    station_name: str,
    audio_files: List[str],
    output_dir: Path
) -> Path:
    """
    Generate a UTF-16 encoded .station file for a radio station.

    TDU Format specifications:
    - Line 1: Station name in quotes (special case for "Radio Bot": `"Radio Bot""Radio Bot"`)
    - Line 2: Track count
    - Following lines: "<filename>"\t\t"<title>"\t\t"<artist>"
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    dest_path = output_dir / f"{station_name}.station"

    with open(dest_path, "w", encoding="utf-16") as out:
        if station_name == "Radio Bot":
            out.write(f'"{station_name}""{station_name}"\n')
        else:
            out.write(f'"{station_name}"\n')

        out.write(f"{len(audio_files)}\n")

        for fname in audio_files:
            artist, title = parse_filename(fname)
            out.write(f'"{fname}"\t\t"{title}"\t\t"{artist}"\n')

    return dest_path


def resolve_paths(args: argparse.Namespace) -> Tuple[Optional[Path], Optional[Path]]:
    """Resolve radio source directory and output directory."""
    tdu_dir: Optional[Path] = None

    if args.tdu_dir:
        tdu_dir = Path(args.tdu_dir).resolve()
    else:
        tdu_dir = common.find_tdu_install_dir()

    # If TDU directory is still not resolved, try interactive prompt
    if not tdu_dir and not (args.radio_dir and args.output_dir):
        common.print_warning("Could not automatically locate the Test Drive Unlimited installation folder.")
        tdu_dir = common.prompt_for_directory("Enter path to your Test Drive Unlimited folder")

    # Radio source directory
    if args.radio_dir:
        radio_dir = Path(args.radio_dir).resolve()
    elif tdu_dir:
        radio_dir = tdu_dir / "Euro" / "Radio"
    else:
        radio_dir = None

    # Output directory for .station files
    if args.output_dir:
        output_dir = Path(args.output_dir).resolve()
    elif tdu_dir:
        output_dir = tdu_dir / "Euro" / "Bnk" / "Sound" / "Radio"
    else:
        output_dir = None

    return radio_dir, output_dir


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate .station playlist files for Test Drive Unlimited radio stations."
    )
    parser.add_argument(
        "-t", "--tdu-dir",
        help="Path to the Test Drive Unlimited game directory."
    )
    parser.add_argument(
        "-r", "--radio-dir",
        help="Path to folder containing station music folders (default: <tdu-dir>/Euro/Radio)."
    )
    parser.add_argument(
        "-o", "--output-dir",
        help="Path where .station files should be saved (default: <tdu-dir>/Euro/Bnk/Sound/Radio)."
    )
    parser.add_argument(
        "-s", "--stations",
        nargs="+",
        help="Specific station names to process. If omitted, scans all subdirectories or standard stations."
    )

    args = parser.parse_args()

    radio_dir, output_dir = resolve_paths(args)

    if not radio_dir or not radio_dir.is_dir():
        common.print_error(f"Radio source directory not found: {radio_dir}")
        common.print_info("Use --tdu-dir or --radio-dir to specify the correct path, or configure config.json.")
        return 1

    if not output_dir:
        common.print_error("Output directory could not be determined.")
        common.print_info("Use --output-dir or --tdu-dir to specify.")
        return 1

    common.print_info(f"Radio folder: {radio_dir}")
    common.print_info(f"Output folder: {output_dir}")

    # Determine which stations to process
    if args.stations:
        stations_to_process = args.stations
    else:
        # Find all subdirectories in radio_dir, or fall back to default station names
        found_dirs = [d.name for d in radio_dir.iterdir() if d.is_dir()]
        stations_to_process = found_dirs if found_dirs else DEFAULT_STATIONS

    if not stations_to_process:
        common.print_warning("No station folders found to process.")
        return 0

    processed_count = 0
    total_tracks = 0

    for station in stations_to_process:
        station_path = radio_dir / station
        if not station_path.is_dir():
            common.print_warning(f"Station directory does not exist, skipping: {station_path}")
            continue

        audio_files = collect_audio_files(station_path, common.AUDIO_EXTENSIONS)
        dest_file = generate_station_file(station, audio_files, output_dir)

        common.print_success(f"Generated '{dest_file.name}' with {len(audio_files)} track(s).")
        processed_count += 1
        total_tracks += len(audio_files)

    print()
    common.print_success(f"Done! Processed {processed_count} station(s) with {total_tracks} total track(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
