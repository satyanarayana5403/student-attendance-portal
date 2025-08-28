import gspread
from oauth2client.service_account import ServiceAccountCredentials

def append_to_gsheet(timestamp, uid, name):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)

    sheet = client.open("Attendance").sheet1  # Must match exact Sheet name
    sheet.append_row([timestamp, uid, name])
