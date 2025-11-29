# backend/celery_worker.py

import os
import csv
import smtplib                           # for sending emails
from email.mime.text import MIMEText     # for HTML email body
from datetime import datetime, timedelta

from celery import Celery
from celery.schedules import crontab  # for periodic jobs

from config import Config
from app import create_app
from extensions import db
from models import (
    Booking,
    ParkingSlot,
    ExportJob,
    User,
    ParkingLot,
)

# -------------------------------------------------
# CELERY APP SETUP (Redis as broker + backend)
# -------------------------------------------------

celery = Celery(
    "vps_tasks",
    broker=Config.CELERY_BROKER_URL,
    backend=Config.CELERY_RESULT_BACKEND,
)

# Flask app context for DB operations inside tasks
_flask_app = create_app()


# -------------------------------------------------
# SIMPLE EMAIL SENDER (for MailHog)
# -------------------------------------------------

def send_email_basic(to_email, subject, html_body):

    try:
        msg = MIMEText(html_body, "html")
        msg["Subject"] = subject
        msg["From"] = Config.FROM_EMAIL
        msg["To"] = to_email

        with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
            server.sendmail(Config.FROM_EMAIL, [to_email], msg.as_string())

        print(f"[EMAIL] Sent mail to {to_email} with subject '{subject}'")
    except Exception as e:
        # Do not crash the Celery job if email fails
        print(f"[EMAIL] Failed to send mail to {to_email}: {e}")


# -------------------------------------------------
# 1. CLEANUP STALE BOOKINGS (manual trigger from Admin)
# -------------------------------------------------
@celery.task
def cleanup_stale_bookings_a():

    with _flask_app.app_context():
        # bookings older than 8 hours
        cutoff_time = datetime.utcnow() - timedelta(hours=8)

        stale_bookings = Booking.query.filter(
            Booking.status == "ACTIVE",
            Booking.start_time < cutoff_time,
        ).all()

        changed_count = 0

        for booking in stale_bookings:
            # free the slot
            slot = ParkingSlot.query.get(booking.slot_id)
            if slot:
                slot.is_occupied = False

            # close the booking
            booking.status = "COMPLETED"
            booking.end_time = datetime.utcnow()
            changed_count += 1

        if changed_count > 0:
            db.session.commit()

        print(f"[CLEANUP] Closed {changed_count} stale bookings.")
        return changed_count


# -------------------------------------------------
# 2. USER CSV EXPORT JOB (User-triggered async job)
# -------------------------------------------------
@celery.task
def export_user_bookings_csv(export_id):

    with _flask_app.app_context():
        job = ExportJob.query.get(export_id)
        if not job:
            print(f"[EXPORT] ExportJob {export_id} not found.")
            return f"ExportJob {export_id} not found"

        try:
            job.status = "IN_PROGRESS"
            db.session.commit()

            # all bookings for this user
            bookings = (
                Booking.query
                .filter_by(user_id=job.user_id)
                .order_by(Booking.start_time.asc())
                .all()
            )

            # ensure exports folder exists
            base_dir = os.path.dirname(__file__)
            exports_dir = os.path.join(base_dir, "exports")
            os.makedirs(exports_dir, exist_ok=True)

            timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            file_name = f"bookings_user_{job.user_id}_{timestamp_str}.csv"
            file_path = os.path.join(exports_dir, file_name)

            fieldnames = [
                "booking_id",
                "user_id",
                "slot_id",
                "vehicle_number",
                "start_time",
                "end_time",
                "amount",
                "status",
            ]

            with open(file_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for b in bookings:
                    writer.writerow({
                        "booking_id": b.id,
                        "user_id": b.user_id,
                        "slot_id": b.slot_id,
                        "vehicle_number": b.vehicle_number,
                        "start_time": b.start_time.isoformat() if b.start_time else "",
                        "end_time": b.end_time.isoformat() if b.end_time else "",
                        "amount": b.amount,
                        "status": b.status,
                    })

            job.status = "DONE"
            job.file_path = file_path
            job.completed_at = datetime.utcnow()
            db.session.commit()

            print(f"[EXPORT] Export complete for user_id={job.user_id}: {file_path}")
            return f"Export complete: {file_path}"

        except Exception as e:
            job.status = "FAILED"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.session.commit()

            print(f"[EXPORT] Export failed for job_id={export_id}: {e}")
            return f"Export failed: {e}"


# -------------------------------------------------
# 3. DAILY REMINDER JOB (Scheduled)
# -------------------------------------------------
@celery.task
def send_daily_reminders_a():

    with _flask_app.app_context():
        lots_count = ParkingLot.query.count()
        if lots_count == 0:
            print("[REMINDER] No parking lots available, skipping reminders.")
            return "NO_LOTS"

        today = datetime.utcnow().date()
        start_of_day = datetime(today.year, today.month, today.day)
        end_of_day = start_of_day + timedelta(days=1)

        # only regular users (skip ADMIN)
        users = User.query.filter(User.role == "USER").all()
        reminded_count = 0

        for user in users:
            has_booking_today = (
                Booking.query.filter(
                    Booking.user_id == user.id,
                    Booking.start_time >= start_of_day,
                    Booking.start_time < end_of_day,
                ).count() > 0
            )

            if not has_booking_today:
                subject = "Daily Parking Reminder"
                body = f"""
                <html>
                  <body>
                    <h3>Hello {user.name},</h3>
                    <p>You have not made any parking bookings today.</p>
                    <p>If needed, please log in to the Vehicle Parking System and book a parking slot.</p>
                    <p><b>This is an automated reminder.</b></p>
                  </body>
                </html>
                """

                send_email_basic(user.email, subject, body)
                reminded_count += 1

        print(f"[REMINDER] Total users reminded today (emails sent): {reminded_count}")
        return reminded_count


# -------------------------------------------------
# 4. MONTHLY ACTIVITY REPORT JOB (Scheduled)
# -------------------------------------------------
@celery.task
def send_monthly_activity_report_a():

    with _flask_app.app_context():
        # 1. Determine previous month (year, month)
        now = datetime.utcnow()
        if now.month == 1:
            report_year = now.year - 1
            report_month = 12
        else:
            report_year = now.year
            report_month = now.month - 1

        # Start & end of previous month
        start_date = datetime(report_year, report_month, 1)
        if report_month == 12:
            end_date = datetime(report_year + 1, 1, 1)
        else:
            end_date = datetime(report_year, report_month + 1, 1)

        # Create reports folder
        base_dir = os.path.dirname(__file__)
        reports_dir = os.path.join(base_dir, "reports")
        os.makedirs(reports_dir, exist_ok=True)

        users = User.query.all()
        generated_count = 0

        for user in users:
            # All bookings for this user in previous month
            bookings = Booking.query.filter(
                Booking.user_id == user.id,
                Booking.start_time >= start_date,
                Booking.start_time < end_date,
            ).all()

            if not bookings:
                total_bookings = 0
                total_amount = 0.0
                most_used_lot_name = "No bookings this month"
            else:
                total_bookings = len(bookings)
                total_amount = sum(b.amount or 0 for b in bookings)

                # Count usage per parking lot
                lot_usage = {}
                for b in bookings:
                    slot = ParkingSlot.query.get(b.slot_id)
                    if not slot:
                        continue
                    lot = ParkingLot.query.get(slot.lot_id)
                    if not lot:
                        continue
                    lot_usage[lot.name] = lot_usage.get(lot.name, 0) + 1

                if lot_usage:
                    most_used_lot_name = max(lot_usage, key=lot_usage.get)
                else:
                    most_used_lot_name = "Unknown"

            # Build a very simple HTML report
            month_str = f"{report_year}-{report_month:02d}"
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Monthly Parking Activity Report - {month_str}</title>
</head>
<body>
    <h2>Monthly Parking Activity Report</h2>
    <p><strong>User:</strong> {user.name} ({user.email})</p>
    <p><strong>Month:</strong> {month_str}</p>

    <h3>Summary</h3>
    <ul>
        <li>Total bookings: {total_bookings}</li>
        <li>Total amount spent: ₹{total_amount:.2f}</li>
        <li>Most used parking lot: {most_used_lot_name}</li>
    </ul>

    <p>This report is auto-generated by the Vehicle Parking System.</p>
</body>
</html>
"""

            # Save to file
            file_name = (
                f"monthly_report_user_{user.id}_{report_year}_{report_month:02d}.html"
            )
            file_path = os.path.join(reports_dir, file_name)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            # Also send as email using MailHog
            subject = f"Monthly Parking Activity Report - {month_str}"
            send_email_basic(user.email, subject, html_content)

            print(
                f"[MONTHLY REPORT] Generated report for user_id={user.id}, "
                f"email={user.email}, file={file_path}"
            )
            generated_count += 1

        print(
            f"[MONTHLY REPORT] Total user reports generated for "
            f"{report_year}-{report_month:02d}: {generated_count}"
        )
        return generated_count


# -------------------------------------------------
# 5. CELERY BEAT SCHEDULE (Periodic jobs)
# -------------------------------------------------
# task names are "module_name.function_name"
celery.conf.beat_schedule = {
    # Daily reminders at 18:00 UTC
    "daily-reminders-job-a": {
        "task": "celery_worker.send_daily_reminders_a",
        "schedule": crontab(hour=18, minute=0),
    },
    # Monthly activity reports on 1st of every month at 00:05 UTC
    "monthly-activity-report-a": {
        "task": "celery_worker.send_monthly_activity_report_a",
        "schedule": crontab(day_of_month=1, hour=0, minute=5),
    },
    # (Optional) we keep cleanup as manual via Admin button,
    # so it is NOT scheduled here.
}
