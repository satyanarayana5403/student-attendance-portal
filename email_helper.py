import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import socket

GMAIL_USER = 'venurao049@gmail.com'
GMAIL_PASS = 'kniv apph fccw erun'  # App Password

def send_email(to_email, subject, body):
    """Send email with timeout protection"""
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Set socket timeout to 5 seconds to prevent hanging
        socket.setdefaulttimeout(5)
        with smtplib.SMTP('smtp.gmail.com', 587, timeout=5) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_PASS)
            server.send_message(msg)
        print(f"✅ Email sent to: {to_email}")
        return True
    except socket.timeout:
        print(f"⚠️  Email timeout for {to_email} (network slow)")
        return False
    except Exception as e:
        print(f"❌ Error sending email to {to_email}: {str(e)[:100]}")
        return False
