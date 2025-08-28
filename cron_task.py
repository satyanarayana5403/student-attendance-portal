import csv
from datetime import datetime, timedelta
from absent_notifier import notify_absentees  # Optional: if you want to trigger email
import os

ATTENDANCE_FILE = 'attendance_log.csv'
DAYS_TO_KEEP = 30

def cleanup_old_logs():
    try:
        with open(ATTENDANCE_FILE, 'r') as infile:
            reader = csv.DictReader(infile)
            rows = list(reader)
            fieldnames = reader.fieldnames
    except FileNotFoundError:
        print("📁 Attendance file not found. No cleanup needed.")
        return

    cutoff_date = datetime.now() - timedelta(days=DAYS_TO_KEEP)
    updated_rows = []

    for row in rows:
        try:
            row_date = datetime.strptime(row['Date'], '%Y-%m-%d')
            if row_date >= cutoff_date:
                updated_rows.append(row)
        except Exception as e:
            print(f"⚠️ Skipping row due to date error: {e}")

    with open(ATTENDANCE_FILE, 'w', newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_rows)

    print(f"🧹 Cleanup complete. {len(rows) - len(updated_rows)} old entries removed.")

if __name__ == '__main__':
    print("🔁 Running scheduled tasks...")
    cleanup_old_logs()
    notify_absentees()  # You can remove this if not needed here
    print("✅ All scheduled tasks completed.")
