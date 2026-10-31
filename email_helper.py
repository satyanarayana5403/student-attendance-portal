import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import socket
from dotenv import load_dotenv

load_dotenv()

GMAIL_USER = os.getenv('GMAIL_USER', '')
GMAIL_PASS = os.getenv('GMAIL_PASS', '')

def send_email(to_email, subject, body, html_body=None):
    """Send email with timeout protection and optional HTML support"""
    if not GMAIL_USER or not GMAIL_PASS:
        print(f"INFO: [Email Simulated] To: {to_email} | Subject: {subject}")
        return True

    msg = MIMEMultipart('alternative')
    msg['From'] = GMAIL_USER
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    if html_body:
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

    try:
        # Set socket timeout to 5 seconds to prevent hanging
        socket.setdefaulttimeout(5)
        with smtplib.SMTP('smtp.gmail.com', 587, timeout=5) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_PASS)
            server.send_message(msg)
        print(f"SUCCESS: Email sent to: {to_email}")
        return True
    except socket.timeout:
        print(f"WARNING: Email timeout for {to_email} (network slow)")
        return False
    except Exception as e:
        print(f"ERROR: Error sending email to {to_email}: {str(e)[:100]}")
        return False
