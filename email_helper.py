import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

GMAIL_USER = 'venurao049@gmail.com'
GMAIL_PASS = 'kniv apph fccw erun'  # App Password

def send_email(to_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_PASS)
            server.send_message(msg)
        print(f"✅ Email sent to: {to_email}")
    except Exception as e:
        print(f"❌ Error sending email to {to_email}:", e)
