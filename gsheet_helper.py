import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

def append_to_gsheet(timestamp, uid, name):
    """
    Append attendance record to Google Sheets
    If credentials.json is not found, silently skip (Google Sheets integration is optional)
    """
    try:
        # Check if credentials.json exists
        if not os.path.exists("credentials.json"):
            print("⚠️  credentials.json not found - Google Sheets sync skipped (optional feature)")
            return
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)

        sheet = client.open("Attendance").sheet1  # Must match exact Sheet name
        sheet.append_row([timestamp, uid, name])
        print(f"✓ Synced to Google Sheets: {uid}")
    except FileNotFoundError:
        print("⚠️  credentials.json not found - Google Sheets sync skipped")
    except Exception as e:
        print(f"⚠️  Google Sheets sync failed: {e} - continuing without sync...")

