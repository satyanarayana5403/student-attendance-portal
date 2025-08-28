import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Update spreadsheet name if needed
SPREADSHEET_NAME = "SmartAttendance"

def append_to_gsheet(timestamp, uid, name):
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)

        sheet = client.open(SPREADSHEET_NAME).sheet1
        sheet.append_row([timestamp, uid, name])
        print(f"✅ Appended to Google Sheet: {uid}, {name}")
    except Exception as e:
        print("❌ Error appending to Google Sheet:", e)
