import os

# === CONFIG ===
RADIO_DIRS = {
    "Radio Djey": r"D:\Program Files (x86)\Atari\Test Drive Unlimited\Euro\Radio\Radio Djey",
    "Radio Bot": r"D:\Program Files (x86)\Atari\Test Drive Unlimited\Euro\Radio\Radio Bot",
    "Radio Classik": r"D:\Program Files (x86)\Atari\Test Drive Unlimited\Euro\Radio\Radio Classik",
    "Sweet Radio": r"D:\Program Files (x86)\Atari\Test Drive Unlimited\Euro\Radio\Sweet Radio",
}

OUTPUT_BASE = r"D:\Program Files (x86)\Atari\Test Drive Unlimited\Euro\Bnk\Sound\Radio"

MUSIC_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".m4a"}  # adjust if needed
# ==============


def parse_filename(filename: str):
    """
    Try to split filename into artist and title.
    Expected format: Artist - Title.ext
    If it can't split, return filename without extension as title, artist as 'Unknown'.
    """
    name, _ = os.path.splitext(filename)

    if " - " in name:
        artist, title = name.split(" - ", 1)
    elif "-" in name:
        # fallback for cases without spaces
        artist, title = name.split("-", 1)
    else:
        artist, title = "Unknown", name

    return artist.strip(), title.strip()


def process_radio(radio_name: str, source_dir: str, output_base: str):
    """Generate a .station file for one radio directory."""
    if not os.path.exists(source_dir):
        print(f"⚠ Source directory does not exist: {source_dir}")
        return

    # Collect music files
    files = [
        f for f in os.listdir(source_dir)
        if os.path.splitext(f)[1].lower() in MUSIC_EXTENSIONS
    ]

    files.sort()

    # Destination file
    dest_file = os.path.join(output_base, f"{radio_name}.station")

    os.makedirs(os.path.dirname(dest_file), exist_ok=True)

    with open(dest_file, "w", encoding="utf-16") as out:
        # First line special case for Radio Bot
        if radio_name == "Radio Bot":
            out.write(f"\"{radio_name}\"\"{radio_name}\"\n")
        else:
            out.write(f"\"{radio_name}\"\n")

        out.write(f"{len(files)}\n")

        for f in files:
            artist, title = parse_filename(f)
            line = f"\"{f}\"\t\t\"{title}\"\t\t\"{artist}\"\n"
            out.write(line)

    print(f"✅ Created {dest_file} with {len(files)} entries.")


def main():
    for radio_name, src_dir in RADIO_DIRS.items():
        process_radio(radio_name, src_dir, OUTPUT_BASE)


if __name__ == "__main__":
    main()
