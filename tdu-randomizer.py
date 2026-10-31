import os
import random
import shutil

# Source and destination paths
SOURCE_DIR = r"E:\Muzyka"
DEST_DIR = r"C:\Users\danie\Documents\Test Drive Unlimited\savegame\d4nielix\Radio\randomizer"

# File extensions considered as music
MUSIC_EXTENSIONS = {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"}

# Number of random songs
NUM_SONGS = 30

def collect_songs(root_dir):
    songs = []
    for dirpath, _, filenames in os.walk(root_dir):
        for file in filenames:
            ext = os.path.splitext(file)[1].lower()
            if ext in MUSIC_EXTENSIONS:
                songs.append(os.path.join(dirpath, file))
    return songs

def main():
    # Make sure destination exists
    os.makedirs(DEST_DIR, exist_ok=True)

    # Collect songs recursively
    all_songs = collect_songs(SOURCE_DIR)

    if not all_songs:
        print("No songs found in source directory.")
        return

    # If fewer than requested, take all
    selected_songs = random.sample(all_songs, min(NUM_SONGS, len(all_songs)))

    # Clear destination folder first (optional)
    for f in os.listdir(DEST_DIR):
        file_path = os.path.join(DEST_DIR, f)
        if os.path.isfile(file_path):
            os.remove(file_path)

    # Copy selected songs
    for i, song in enumerate(selected_songs, start=1):
        dest_file = os.path.join(DEST_DIR, f"{i:02d}_{os.path.basename(song)}")
        shutil.copy2(song, dest_file)

    print(f"Copied {len(selected_songs)} songs to {DEST_DIR}")

if __name__ == "__main__":
    main()
