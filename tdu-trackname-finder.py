import os

# --- konfiguracja ---
folder_path = r"D:\Program Files (x86)\Atari\Test Drive Unlimited\Euro\Bnk\IGE"  # 👈 podmień na swój folder z plikami .IGE
search_text = "Ride in hickam village"

# --- wyszukiwanie ---
search_bytes = search_text.lower().encode("ascii")

for filename in os.listdir(folder_path):
    if not filename.lower().endswith(".ige"):
        continue

    file_path = os.path.join(folder_path, filename)

    try:
        with open(file_path, "rb") as f:
            data = f.read()

        if search_bytes in data.lower():
            print(f"Znaleziono w pliku: {filename}")
            break

    except Exception as e:
        print(f"Błąd podczas czytania {filename}: {e}")
else:
    print("Nie znaleziono wyścigu o tytule 'Conquest of the west'.")
