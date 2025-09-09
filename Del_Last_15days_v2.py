import os
import time
import shutil
import pymysql
from datetime import datetime, timedelta, date

# DB config
DB_USER = "root"
DB_PASS = "insightzz123"
DB_HOST = "localhost"
DB_NAME = "hla_cam_cap_db"

# Main folder path
main_folder_path = "C:/insightzz/CAM_CAP/DefectData/"
SLEEP_INTERVAL = 86400  # Run once per day

row_image_dir = "C:/insightzz/CAM_CAP/DATA/"
row_day = 2
notok_image_dir = "C:/insightzz/CAM_CAP/HLA_NOT_OK_DEFECT_DATA/"
notok_day = 7

def getInferenceTrigger_2(date_value):
    """Check if data for a given date is synced in DB"""
    result = 0
    try:
        conn = pymysql.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
        cur = conn.cursor()
        query = """
            SELECT * 
            FROM hla_cam_cap_db.hla_cam_cap_temp_pdf_path_table 
            WHERE (STATUS = 'NOT OK' OR STATUS = 'OK')  
            AND DATE(CREATE_DATETIME) = %s;
        """
        cur.execute(query, (date_value,))
        data_set = cur.fetchall()

        if data_set:  # if not empty
            result = 1
    except Exception as e:
        print("DB Exception:", e)
    finally:
        try:
            cur.close()
            conn.close()
        except:
            pass

    return result


def delfun():
    """Delete folders older than 15 days if synced in DB"""
    today = date.today()
    start_date = today - timedelta(days=15)

    for folder_name in os.listdir(main_folder_path):
        folder_path = os.path.join(main_folder_path, folder_name)

        if not os.path.isdir(folder_path):
            continue

        # Parse folder name as date
        try:
            folder_date = datetime.strptime(folder_name, "%Y_%m_%d").date()
        except ValueError:
            print(f"Skipping non-date folder: {folder_name}")
            continue

        # Process only folders older than 15 days
        if folder_date < start_date:
            print(f"Checking folder {folder_name} (date: {folder_date})")

            # Check if data is synced in DB
            if getInferenceTrigger_2(folder_date) == 1:
                try:
                    shutil.rmtree(folder_path)
                    print(f"Deleted folder: {folder_path}")
                except Exception as e:
                    print(f"Error deleting {folder_path}: {e}")
            else:
                print(f"Data not synced for {folder_date}, keeping folder.")
        else:
            print(f"Keeping recent folder: {folder_name}")

def cleanup_row_jpgs():
    now = time.time()
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



def cleanup_row_jpgs():
    now = time.time()
    import shutil
    for date_folder in os.listdir(row_image_dir):
        date_folder_path = os.path.join(row_image_dir, date_folder)
        if not os.path.isdir(date_folder_path):
            continue

        # Try parsing folder name as date
        try:
            folder_date = datetime.strptime(date_folder, "%Y-%m-%d")
            if folder_date >= datetime.now() - timedelta(days=row_day):
                continue  # Skip recent folders

            try:
                shutil.rmtree(date_folder_path)  # <-- remove directory and its contents
                print(f"Deleted: {date_folder_path}")
            except Exception as e:
                print(f"Error deleting {date_folder_path}: {e}")
        except ValueError:
            pass  # Ignore if folder name isn't date-formatted



def cleanup_notok_jpgs():
    now = time.time()
    import shutil
    for date_folder in os.listdir(notok_image_dir):
        date_folder_path = os.path.join(notok_image_dir, date_folder)
        if not os.path.isdir(date_folder_path):
            continue

        # Try parsing folder name as date
        try:
            folder_date = datetime.strptime(date_folder, "%Y_%m_%d")
            if folder_date >= datetime.now() - timedelta(days=notok_day):
                print(folder_date)
                continue  # Skip recent folders

            try:
                shutil.rmtree(date_folder_path)  # <-- remove directory and its contents
                print(f"Deleted: {date_folder_path}")
            except Exception as e:
                print(f"Error deleting {date_folder_path}: {e}")
        except ValueError:
            pass  # Ignore if folder name isn't date-formatted

# Run once per day
while True:
    print("\n=== Cleanup cycle started ===")
    delfun()
    print("=== Cleanup cycle finished. Sleeping 1 day. ===\n")
    cleanup_row_jpgs()
    print("=== cleanup_row_jpgs 1 day. ===\n")
    cleanup_notok_jpgs()
    print("=== cleanup_notok_jpgs 1 day. ===\n")
    time.sleep(SLEEP_INTERVAL)
