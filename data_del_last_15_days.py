import os
import time
from datetime import datetime, timedelta

# Root directory containing your date‐named folders
ROOT_DIR = r"C:\Insightzz\ALGOITHM\INFERENCE_PATH"
row_image_dir = r"C:\Insightzz\DATA"
row_day = 2
DAYS_THRESHOLD = 10  # Files older than this (in days) will be deleted
SLEEP_INTERVAL = 3600  # How often to run cleanup (in seconds) — 3600s = 1 hour

def cleanup_old_jpgs():
    now = time.time()
    cutoff = now - (DAYS_THRESHOLD * 86400)  # 86400 seconds = 1 day

    for date_folder in os.listdir(ROOT_DIR):
        date_folder_path = os.path.join(ROOT_DIR, date_folder)
        if not os.path.isdir(date_folder_path):
            continue

        # Try parsing folder name as date
        try:
            folder_date = datetime.strptime(date_folder, "%Y_%m_%d")
            if folder_date >= datetime.now() - timedelta(days=DAYS_THRESHOLD):
                continue  # Skip recent folders
        except ValueError:
            pass  # Ignore if folder name isn't date-formatted

        for eng_folder in os.listdir(date_folder_path):
            eng_folder_path = os.path.join(date_folder_path, eng_folder)
            if not os.path.isdir(eng_folder_path):
                continue

            for fname in os.listdir(eng_folder_path):
                if not fname.lower().endswith(".jpg"):
                    continue
                full_path = os.path.join(eng_folder_path, fname)
                try:
                    mtime = os.path.getmtime(full_path)
                    if mtime < cutoff:
                        os.remove(full_path)
                        print(f"Deleted: {full_path}")
                except Exception as e:
                    print(f"Error deleting {full_path}: {e}")


def cleanup_row_jpgs():
    now = time.time()
    cutoff = now - (row_day * 86400)  # 86400 seconds = 1 day
    import shutil
    for date_folder in os.listdir(row_image_dir):
        date_folder_path = os.path.join(row_image_dir, date_folder)
        if not os.path.isdir(date_folder_path):
            continue

        # Try parsing folder name as date
        try:
            folder_date = datetime.strptime(date_folder, "%Y_%m_%d")
            if folder_date >= datetime.now() - timedelta(days=row_day):
                continue  # Skip recent folders

            try:
                shutil.rmtree(date_folder_path)  # <-- remove directory and its contents
                print(f"Deleted: {date_folder_path}")
            except Exception as e:
                print(f"Error deleting {date_folder_path}: {e}")
        except ValueError:
            pass  # Ignore if folder name isn't date-formatted

        # for eng_folder in os.listdir(date_folder_path):
        #     eng_folder_path = os.path.join(date_folder_path, eng_folder)
        #     if not os.path.isdir(eng_folder_path):
        #         continue

        #     for fname in os.listdir(eng_folder_path):
        #         if not fname.lower().endswith(".jpg"):
        #             continue
        #         full_path = os.path.join(eng_folder_path, fname)
            

# Run continuously
while True:
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running cleanup...")
    cleanup_old_jpgs()
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Cleanup done. Sleeping...\n")
    cleanup_row_jpgs()
    time.sleep(SLEEP_INTERVAL)
