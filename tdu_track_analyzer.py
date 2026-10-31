#!/usr/bin/env python3
"""
tdu_track_analyzer.py - Test Drive Unlimited .IGE Track File Inspector & Comparator

Parses binary .IGE track files, extracts CHPT (checkpoint), CARP, and ENTI chunks,
and either displays a structured breakdown of a single file or compares two files
(e.g., online vs offline track versions).
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import tdu_common as common

KNOWN_TAGS = [b"CHPT", b"CARP", b"ENTI"]


@dataclass
class CheckpointInfo:
    index: int
    offset: int
    size: int
    checkpoint_id: Optional[int]


def parse_checkpoints(data: bytes) -> List[CheckpointInfo]:
    """Extract checkpoint chunks and their metadata from binary IGE data."""
    results: List[CheckpointInfo] = []

    for idx, match in enumerate(re.finditer(b"CHPT", data), start=1):
        pos = match.start()
        data_start = pos + 4

        # Find the next boundary among known tags
        next_pos = None
        for tag in KNOWN_TAGS:
            for next_match in re.finditer(re.escape(tag), data[pos + 1:]):
                candidate_pos = pos + 1 + next_match.start()
                if candidate_pos > pos:
                    if next_pos is None or candidate_pos < next_pos:
                        next_pos = candidate_pos

        data_end = next_pos if next_pos is not None else len(data)
        size = data_end - data_start
        last_byte = data[data_end - 1] if data_end > data_start else None

        results.append(CheckpointInfo(
            index=idx,
            offset=pos,
            size=size,
            checkpoint_id=last_byte
        ))

    return results


def print_single_file_analysis(file_path: Path, data: bytes) -> None:
    """Print detailed inspection of a single .IGE file."""
    common.print_info(f"Analyzing: {file_path.name} ({len(data)} bytes)")

    # Count known tags
    tag_counts = {tag.decode("ascii"): len(list(re.finditer(re.escape(tag), data))) for tag in KNOWN_TAGS}
    tag_summary = ", ".join(f"{t}: {c}" for t, c in tag_counts.items())
    print(f"  Detected chunks: {tag_summary}\n")

    checkpoints = parse_checkpoints(data)
    if not checkpoints:
        common.print_warning("No CHPT (checkpoint) tags found in file.")
        return

    # Print table header
    header = f"{'#':>3} | {'Offset (Hex)':<14} | {'Size (bytes)':<12} | {'Checkpoint ID':<13}"
    separator = "-" * len(header)
    print(header)
    print(separator)

    for chpt in checkpoints:
        chpt_id_str = str(chpt.checkpoint_id) if chpt.checkpoint_id is not None else "N/A"
        print(f"{chpt.index:>3} | 0x{chpt.offset:08X}     | {chpt.size:<12} | {chpt_id_str:<13}")

    print(separator)
    common.print_success(f"Total checkpoints: {len(checkpoints)}")


def print_comparison(file1_path: Path, data1: bytes, file2_path: Path, data2: bytes) -> None:
    """Compare checkpoints between two .IGE files side-by-side."""
    common.print_info(f"Comparing:")
    print(f"  File 1: {file1_path.name} ({len(data1)} bytes)")
    print(f"  File 2: {file2_path.name} ({len(data2)} bytes)\n")

    chpts1 = parse_checkpoints(data1)
    chpts2 = parse_checkpoints(data2)

    max_len = max(len(chpts1), len(chpts2))
    if max_len == 0:
        common.print_warning("No checkpoints found in either file.")
        return

    # Table header
    header = (
        f"{'#':>3} | {'Offset 1':<10} | {'Offset 2':<10} | "
        f"{'Size 1':<8} | {'Size 2':<8} | {'ID 1':<5} | {'ID 2':<5} | {'Match?'}"
    )
    separator = "-" * len(header)
    print(header)
    print(separator)

    differences = 0
    for i in range(max_len):
        c1 = chpts1[i] if i < len(chpts1) else None
        c2 = chpts2[i] if i < len(chpts2) else None

        idx_str = f"{i + 1:>3}"
        off1_str = f"0x{c1.offset:06X}" if c1 else "-"
        off2_str = f"0x{c2.offset:06X}" if c2 else "-"
        size1_str = str(c1.size) if c1 else "-"
        size2_str = str(c2.size) if c2 else "-"
        id1_str = str(c1.checkpoint_id) if c1 and c1.checkpoint_id is not None else "-"
        id2_str = str(c2.checkpoint_id) if c2 and c2.checkpoint_id is not None else "-"

        # Compare attributes
        match = (c1 is not None and c2 is not None and c1.size == c2.size and c1.checkpoint_id == c2.checkpoint_id)
        if match:
            status = "MATCH"
        else:
            status = "DIFF"
            differences += 1

        print(
            f"{idx_str} | {off1_str:<10} | {off2_str:<10} | "
            f"{size1_str:<8} | {size2_str:<8} | {id1_str:<5} | {id2_str:<5} | {status}"
        )

    print(separator)
    if differences == 0:
        common.print_success(f"All {max_len} checkpoints match in size and ID!")
    else:
        common.print_warning(f"Found {differences} checkpoint difference(s) between the two files.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze or compare binary .IGE track files from Test Drive Unlimited."
    )
    parser.add_argument(
        "file1",
        nargs="?",
        help="Path to the primary .IGE file."
    )
    parser.add_argument(
        "file2",
        nargs="?",
        help="Optional path to a second .IGE file for comparison."
    )

    args = parser.parse_args()

    # Handle missing file arguments
    file1_path: Optional[Path] = None
    if args.file1:
        file1_path = Path(args.file1).resolve()
    else:
        # Check current directory for any .ige files
        ige_files = list(Path(".").glob("*.ige")) + list(Path(".").glob("*.IGE"))
        if ige_files:
            common.print_info(f"Auto-selected file in current folder: {ige_files[0].name}")
            file1_path = ige_files[0].resolve()
        elif sys.stdin.isatty():
            file1_input = input("Enter path to .IGE file: ").strip()
            if file1_input:
                file1_path = Path(file1_input).resolve()

    if not file1_path or not file1_path.is_file():
        common.print_error("A valid .IGE file is required.")
        parser.print_help()
        return 1

    try:
        data1 = file1_path.read_bytes()
    except Exception as e:
        common.print_error(f"Failed to read '{file1_path}': {e}")
        return 1

    # Single file analysis or comparison?
    if args.file2:
        file2_path = Path(args.file2).resolve()
        if not file2_path.is_file():
            common.print_error(f"Comparison file does not exist: {file2_path}")
            return 1
        try:
            data2 = file2_path.read_bytes()
        except Exception as e:
            common.print_error(f"Failed to read '{file2_path}': {e}")
            return 1

        print_comparison(file1_path, data1, file2_path, data2)
    else:
        print_single_file_analysis(file1_path, data1)

    return 0


if __name__ == "__main__":
    sys.exit(main())
