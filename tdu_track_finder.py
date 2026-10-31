#!/usr/bin/env python3
"""
tdu_track_finder.py - Search .IGE Track Files by Race Name

Scans a directory of Test Drive Unlimited .IGE files to find which file
contains a given track or challenge name.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import tdu_common as common


def search_in_binary(data: bytes, query: str) -> List[Tuple[int, str]]:
    """
    Search for query text inside binary data with case-insensitivity.
    Searches both UTF-8/ASCII and UTF-16LE representations.
    Returns a list of (offset, matched_encoding) tuples.
    """
    matches: List[Tuple[int, str]] = []
    data_lower = data.lower()

    # 1. UTF-8 / ASCII
    try:
        query_bytes = query.lower().encode("utf-8")
        start = 0
        while True:
            pos = data_lower.find(query_bytes, start)
            if pos == -1:
                break
            matches.append((pos, "ASCII/UTF-8"))
            start = pos + len(query_bytes)
    except UnicodeEncodeError:
        pass

    # 2. UTF-16LE (wide strings)
    try:
        query_bytes_16 = query.lower().encode("utf-16le")
        start = 0
        while True:
            pos = data_lower.find(query_bytes_16, start)
            if pos == -1:
                break
            matches.append((pos, "UTF-16LE"))
            start = pos + len(query_bytes_16)
    except UnicodeEncodeError:
        pass

    matches.sort(key=lambda m: m[0])
    return matches


def resolve_ige_dir(cli_dir: Optional[str]) -> Optional[Path]:
    """Find the directory containing .IGE files."""
    if cli_dir:
        p = Path(cli_dir).resolve()
        if p.is_dir():
            return p
        common.print_error(f"Specified directory does not exist: {cli_dir}")
        return None

    # Check config or auto-detect TDU installation
    tdu_dir = common.find_tdu_install_dir()
    if tdu_dir:
        candidate = tdu_dir / "Euro" / "Bnk" / "IGE"
        if candidate.is_dir():
            return candidate

        # Also check Euro/Bnk
        candidate_bnk = tdu_dir / "Euro" / "Bnk"
        if candidate_bnk.is_dir():
            return candidate_bnk

    # Check current working directory
    cwd = Path.cwd()
    if list(cwd.glob("*.ige")) or list(cwd.glob("*.IGE")):
        return cwd

    # Interactive prompt fallback
    return common.prompt_for_directory("Enter path to folder with .IGE files")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Search for a race or track name inside Test Drive Unlimited .IGE files."
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="Race name or keyword to search for (e.g., 'Ride in hickam village')."
    )
    parser.add_argument(
        "-d", "--dir",
        dest="directory",
        help="Directory containing .IGE files (default: auto-detected <tdu>/Euro/Bnk/IGE)."
    )
    parser.add_argument(
        "-1", "--first",
        action="store_true",
        help="Stop searching after finding the first matching file."
    )

    args = parser.parse_args()

    # Query prompt if missing
    query = args.query
    if not query:
        if sys.stdin.isatty():
            query = input("Enter race/track name to search for: ").strip()
        if not query:
            common.print_error("Search query cannot be empty.")
            parser.print_help()
            return 1

    # Directory resolution
    ige_dir = resolve_ige_dir(args.directory)
    if not ige_dir or not ige_dir.is_dir():
        common.print_error("No valid .IGE directory found. Please specify using -d/--dir.")
        return 1

    common.print_info(f"Searching for: \"{query}\"")
    common.print_info(f"Directory:      {ige_dir}\n")

    # Collect .IGE files
    ige_files = [
        f for f in ige_dir.iterdir()
        if f.is_file() and f.suffix.lower() == ".ige"
    ]

    if not ige_files:
        common.print_warning(f"No .IGE files found in '{ige_dir}'.")
        return 0

    matches_found = 0
    scanned_count = 0

    for file_path in ige_files:
        scanned_count += 1
        try:
            data = file_path.read_bytes()
        except Exception as e:
            common.print_warning(f"Could not read '{file_path.name}': {e}")
            continue

        results = search_in_binary(data, query)
        if results:
            matches_found += 1
            offsets_str = ", ".join(f"0x{pos:X} ({enc})" for pos, enc in results[:3])
            if len(results) > 3:
                offsets_str += f" and {len(results) - 3} more"

            common.print_success(f"Found in: {file_path.name}")
            print(f"    Offset(s): {offsets_str}")

            if args.first:
                break

    print()
    if matches_found > 0:
        common.print_success(f"Search complete: found in {matches_found} file(s) (scanned {scanned_count} files).")
    else:
        common.print_warning(f"No matches found for \"{query}\" in {scanned_count} file(s).")

    return 0


if __name__ == "__main__":
    sys.exit(main())
