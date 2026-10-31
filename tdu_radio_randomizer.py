#!/usr/bin/env python3
"""
tdu_radio_randomizer.py - Random Music Selector for Test Drive Unlimited Custom Radio

Picks a random selection of songs from your music library and copies them into
your TDU savegame profile's custom radio directory.
"""

from __future__ import annotations

import argparse
import os
import random
import shutil
import sys
from pathlib import Path
from typing import List, Optional, Set

import tdu_common as common

DEFAULT_SONG_COUNT = 30
DEFAULT_STATION_NAME = "randomizer"


def collect_songs(root_dir: Path, extensions: Set[str]) -> List[Path]:
    """Recursively search for music files in root_dir."""
    songs: List[Path] = []
    if not root_dir.is_dir():
        return songs

    for dirpath, _, filenames in os.walk(root_dir):
        for fname in filenames:
            ext = os.path.splitext(fname)[1].lower()
            if ext in extensions:
                songs.append(Path(dirpath) / fname)
    return songs


def resolve_profile(savegame_dir: Path, requested_profile: Optional[str]) -> Optional[str]:
    """Determine which profile to use."""
    profiles = common.get_savegame_profiles(savegame_dir)

    if not profiles:
        common.print_error(f"No player profiles found in '{savegame_dir}'.")
        return None

    if requested_profile:
        if requested_profile in profiles:
            return requested_profile
        common.print_warning(f"Profile '{requested_profile}' not found in '{savegame_dir}'.")

    # If only one profile exists, pick it automatically
    if len(profiles) == 1:
        chosen = profiles[0]
        common.print_info(f"Auto-selected sole profile: '{chosen}'")
        return chosen

    # If multiple profiles exist and running interactively, prompt
    if sys.stdin.isatty():
        print("\nAvailable profiles:")
        for idx, prof in enumerate(profiles, start=1):
            print(f"  [{idx}] {prof}")
        try:
            choice = input(f"Select profile [1-{len(profiles)}]: ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(profiles):
                return profiles[int(choice) - 1]
        except (EOFError, KeyboardInterrupt):
            print()
            return None

    common.print_error(f"Multiple profiles exist ({', '.join(profiles)}). Please specify with --profile.")
    return None


def resolve_source_dir(cli_source: Optional[str]) -> Optional[Path]:
    """Find the music source directory."""
    if cli_source:
        p = Path(cli_source).resolve()
        if p.is_dir():
            return p
        common.print_error(f"Specified source folder does not exist: {cli_source}")
        return None

    config = common.load_config()
    cfg_source = config.get("music_source_dir")
    if cfg_source:
        p = Path(cfg_source).resolve()
        if p.is_dir():
            return p

    # Default Music folder check
    default_music = Path.home() / "Music"
    if default_music.is_dir():
        common.print_info(f"Defaulting to system Music folder: {default_music}")
        return default_music

    # Interactive prompt fallback
    return common.prompt_for_directory("Enter path to your music folder")


def resolve_dest_dir(args: argparse.Namespace) -> Optional[Path]:
    """Determine the destination radio folder."""
    # Direct destination override
    if args.dest:
        return Path(args.dest).resolve()

    # Savegame directory
    savegame_dir = common.find_tdu_savegame_dir(args.savegame_dir)
    if not savegame_dir:
        common.print_warning("Could not automatically locate the TDU savegame folder.")
        savegame_dir = common.prompt_for_directory("Enter path to your 'savegame' directory")
        if not savegame_dir:
            return None

    config = common.load_config()
    requested_profile = args.profile or config.get("profile_name")
    profile = resolve_profile(savegame_dir, requested_profile)
    if not profile:
        return None

    station_name = args.station or config.get("radio_station_name") or DEFAULT_STATION_NAME
    dest_dir = savegame_dir / profile / "Radio" / station_name
    return dest_dir


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Randomly select and copy songs to your Test Drive Unlimited custom radio folder."
    )
    parser.add_argument(
        "-s", "--source",
        help="Path to folder containing your music library."
    )
    parser.add_argument(
        "-d", "--dest",
        help="Explicit destination directory (overrides profile/station resolution)."
    )
    parser.add_argument(
        "-p", "--profile",
        help="TDU profile name. Auto-detected if only one profile exists."
    )
    parser.add_argument(
        "--station",
        help=f"Radio station folder name inside profile (default: '{DEFAULT_STATION_NAME}')."
    )
    parser.add_argument(
        "--savegame-dir",
        help="Path to TDU savegame directory (default: Documents/Test Drive Unlimited/savegame)."
    )
    parser.add_argument(
        "-n", "--count",
        type=int,
        help=f"Number of songs to pick (default: {DEFAULT_SONG_COUNT} or from config.json)."
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Do not clear existing files in destination directory before copying."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the selection and output tracklist without copying files."
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Optional random seed for reproducible picks."
    )

    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    config = common.load_config()
    count = args.count or config.get("random_song_count") or DEFAULT_SONG_COUNT

    # 1. Resolve source
    source_dir = resolve_source_dir(args.source)
    if not source_dir:
        common.print_error("No valid music source directory provided. Use -s/--source or config.json.")
        return 1

    # 2. Resolve destination
    dest_dir = resolve_dest_dir(args)
    if not dest_dir:
        common.print_error("Could not determine destination folder.")
        return 1

    common.print_info(f"Music source: {source_dir}")
    common.print_info(f"Destination:  {dest_dir}")
    common.print_info(f"Target count: {count} songs")

    # 3. Collect songs
    common.print_info("Scanning source directory for audio files...")
    all_songs = collect_songs(source_dir, common.AUDIO_EXTENSIONS)

    if not all_songs:
        common.print_error(f"No audio files found in '{source_dir}'.")
        return 1

    common.print_info(f"Found {len(all_songs)} total audio file(s).")

    # 4. Pick random songs
    num_to_pick = min(count, len(all_songs))
    selected = random.sample(all_songs, num_to_pick)

    if args.dry_run:
        common.print_info("--- [DRY RUN] Selected tracks: ---")
        for i, song in enumerate(selected, start=1):
            print(f"  {i:02d}. {song.name}")
        common.print_success(f"[DRY RUN] {len(selected)} songs selected (no files were copied).")
        return 0

    # 5. Prepare destination folder
    dest_dir.mkdir(parents=True, exist_ok=True)

    if not args.no_clean:
        common.print_info("Cleaning existing files in destination folder...")
        removed_count = 0
        for item in dest_dir.iterdir():
            if item.is_file():
                try:
                    item.unlink()
                    removed_count += 1
                except Exception as e:
                    common.print_warning(f"Could not remove '{item.name}': {e}")
        if removed_count:
            common.print_info(f"Removed {removed_count} old file(s).")

    # 6. Copy files
    common.print_info("Copying selected tracks...")
    copied_count = 0
    for i, song_path in enumerate(selected, start=1):
        target_name = f"{i:02d}_{song_path.name}"
        target_path = dest_dir / target_name
        try:
            shutil.copy2(song_path, target_path)
            copied_count += 1
            print(f"  [{i:02d}/{num_to_pick:02d}] {song_path.name}")
        except Exception as e:
            common.print_error(f"Failed to copy '{song_path.name}': {e}")

    print()
    common.print_success(f"Successfully copied {copied_count} song(s) to '{dest_dir}'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
