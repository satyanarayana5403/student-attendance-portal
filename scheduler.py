import time
import threading
import logging
from datetime import datetime
import schedule
from extensions import db
from models import Student, Teacher, Attendance, TeacherAttendance, AppSetting
from email_helper import send_email
from utils import get_settings

logger = logging.getLogger('NexusScheduler')

_scheduler_thread = None
_scheduler_running = False
_flask_app = None

def get_html_absentee_template(name, uid, date_str):
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #0b0d14; color: #e2e8f0; margin: 0; padding: 24px; }}
  .card {{ max-width: 560px; margin: 0 auto; background: #131622; border: 1px solid #23283e; border-radius: 14px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }}
  .header {{ background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); padding: 28px 24px; text-align: center; }}
  .header h1 {{ margin: 0; color: #ffffff; font-size: 22px; font-weight: 700; letter-spacing: -0.5px; }}
  .header p {{ margin: 6px 0 0; color: #e0e7ff; font-size: 13px; font-family: monospace; }}
  .content {{ padding: 28px 24px; font-size: 14px; line-height: 1.6; color: #cbd5e1; }}
  .alert-box {{ background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.3); border-left: 4px solid #ef4444; border-radius: 8px; padding: 16px; margin: 20px 0; }}
  .info-row {{ display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 13px; }}
  .info-label {{ color: #94a3b8; font-family: monospace; }}
  .info-val {{ color: #f8fafc; font-weight: 600; }}
  .badge-absent {{ display: inline-block; background: #ef4444; color: #fff; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; text-transform: uppercase; }}
  .footer {{ padding: 18px 24px; background: #0e101a; border-top: 1px solid #1a1e30; font-size: 12px; color: #64748b; text-align: center; }}
</style>
</head>
<body>
<div class="card">
  <div class="header">
    <h1>Nexus Attendance Portal</h1>
    <p>DAILY ATTENDANCE MONITORING NOTICE</p>
  </div>
  <div class="content">
    <p>Dear Parent / Guardian,</p>
    <p>This automated notice is to inform you that your student was recorded as <strong>absent</strong> for today's college sessions.</p>
    
    <div class="alert-box">
      <div style="margin-bottom: 8px; font-size: 12px; font-weight: 700; color: #f87171; letter-spacing: 0.5px; text-transform: uppercase;">Attendance Record Summary</div>
      <div class="info-row">
        <span class="info-label">Student Name:</span>
        <span class="info-val">{name}</span>
      </div>
      <div class="info-row">
        <span class="info-label">Roll No / UID:</span>
        <span class="info-val">{uid}</span>
      </div>
      <div class="info-row">
        <span class="info-label">Session Date:</span>
        <span class="info-val">{date_str}</span>
      </div>
      <div class="info-row" style="border-bottom: none;">
        <span class="info-label">Attendance Status:</span>
        <span class="info-val"><span class="badge-absent">Unexcused Absence</span></span>
      </div>
    </div>
    
    <p style="font-size: 13px; color: #94a3b8;">
      If this absence was pre-approved or due to a medical emergency, please ensure a valid medical certificate or leave approval slip is submitted to the department head tomorrow morning.
    </p>
  </div>
  <div class="footer">
    Automated notification dispatched daily at 5:00 PM • Nexus Attendance System<br>
    Please do not reply directly to this automated email.
  </div>
</div>
</body>
</html>
"""

def run_daily_absentee_job(app=None, force=False):
    """
    Core scheduled worker: Finds today's absentees and dispatches email alerts.
    """
    current_app = app or _flask_app
    if not current_app:
        logger.warning("No Flask app context available for scheduled absentee job.")
        return {'success': False, 'message': 'No Flask app context'}

    with current_app.app_context():
        settings = get_settings()
        
        # Check if enabled
        is_enabled = settings.get('auto_absent_alerts_enabled') == 'true'
        email_enabled = settings.get('email') == 'true'
        
        if not force and not is_enabled:
            logger.info("Daily absentee alerts are disabled in settings. Skipping run.")
            return {'success': False, 'message': 'Daily alerts disabled in settings.'}

        if not email_enabled:
            logger.info("Global email notifications are disabled. Skipping run.")
            return {'success': False, 'message': 'Email notifications disabled.'}

        today = datetime.now().strftime('%Y-%m-%d')
        now_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Prevent duplicate auto-runs on the same date unless forced
        last_date = settings.get('last_auto_alert_date')
        if not force and last_date == today:
            logger.info(f"Daily absentee alerts for {today} were already sent. Skipping duplicate run.")
            return {'success': True, 'message': f'Alerts for {today} already sent.'}

        # 1. Identify absent students
        present_student_ids = {a.student_id for a in Attendance.query.filter_by(date=today).all()}
        all_students = Student.query.all()
        absent_students = [s for s in all_students if s.id not in present_student_ids]

        sent_count = 0
        failed_count = 0
        skipped_count = 0

        # 2. Dispatch emails
        for student in absent_students:
            email = (student.email or '').strip()
            if not email or '@' not in email:
                skipped_count += 1
                continue

            subject = f"⚠️ Daily Absence Notice — {student.name} ({today})"
            plain_body = (
                f"Dear Parent/Guardian,\n\n"
                f"This is an automated notice to inform you that {student.name} (UID: {student.uid}) "
                f"was marked absent on {today}.\n\n"
                f"Please ensure they provide a valid reason or medical certificate if needed.\n\n"
                f"Regards,\nNexus Attendance System"
            )
            html_body = get_html_absentee_template(student.name, student.uid, today)

            try:
                ok = send_email(email, subject, plain_body, html_body=html_body)
                if ok:
                    sent_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                logger.error(f"Error sending automated absentee email to {email}: {e}")
                failed_count += 1

        # 3. Update execution telemetry in AppSetting
        stats_summary = f"{sent_count} sent, {failed_count} failed, {skipped_count} skipped"
        for k, v in [
            ('last_auto_alert_date', today),
            ('last_auto_alert_run', now_time_str),
            ('last_auto_alert_stats', stats_summary)
        ]:
            s = AppSetting.query.filter_by(key=k).first()
            if s:
                s.value = v
            else:
                db.session.add(AppSetting(key=k, value=v))
        db.session.commit()

        logger.info(f"Daily absentee alert run finished: {stats_summary} (Total absent: {len(absent_students)})")
        return {
            'success': True,
            'date': today,
            'timestamp': now_time_str,
            'sent': sent_count,
            'failed': failed_count,
            'skipped': skipped_count,
            'total_absent': len(absent_students),
            'stats': stats_summary
        }

def reschedule_daily_job(app, time_str="17:00"):
    """Update scheduled trigger time (e.g. '17:00')"""
    global _flask_app
    _flask_app = app
    try:
        schedule.clear('daily_absentee_tag')
        schedule.every().day.at(time_str).do(run_daily_absentee_job, app=app).tag('daily_absentee_tag')
        logger.info(f"Daily absentee job scheduled for {time_str} every day.")
        return True
    except Exception as e:
        logger.error(f"Failed to reschedule daily absentee job for {time_str}: {e}")
        return False

def _scheduler_worker():
    """Background loop checking pending schedule tasks"""
    global _scheduler_running
    logger.info("Nexus background scheduler daemon started.")
    while _scheduler_running:
        try:
            schedule.run_pending()
        except Exception as e:
            logger.error(f"Scheduler worker error: {e}")
        time.sleep(15)

def start_scheduler(app):
    """Start background scheduler thread once on application boot"""
    global _scheduler_thread, _scheduler_running, _flask_app
    _flask_app = app

    with app.app_context():
        try:
            settings = get_settings()
            alert_time = settings.get('auto_absent_alert_time', '17:00')
        except Exception:
            alert_time = '17:00'
        reschedule_daily_job(app, alert_time)

    if not _scheduler_running:
        _scheduler_running = True
        _scheduler_thread = threading.Thread(target=_scheduler_worker, daemon=True, name="NexusSchedulerThread")
        _scheduler_thread.start()
        logger.info("Scheduler daemon thread successfully initialized.")
