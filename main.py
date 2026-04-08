"""
=============================================================
  AJATYA GANDRAL — JOB SEARCH BOT  |  Main Runner
  Runs 24/7 on Railway — sends applications, monitors inbox,
  auto-replies to interviews, sends follow-ups, updates tracker
=============================================================
"""
import os
import time
import schedule
from datetime import datetime

import config
from cv_generator import generate_cv
from emailer import (send_email, build_application_email,
                     check_inbox_for_replies, send_interview_reply,
                     send_followup_email)
from tracker import update_tracker, get_pending_followups

PROFILE = {
    "name":        config.YOUR_NAME,
    "email":       config.YOUR_EMAIL,
    "phone":       config.YOUR_PHONE,
    "profile":     config.YOUR_PROFILE,
    "skills":      config.YOUR_SKILLS,
    "experience":  config.YOUR_EXPERIENCE,
    "education":   config.YOUR_EDUCATION,
    "credentials": config.YOUR_CREDENTIALS,
}

def now():
    return datetime.now().strftime("%d-%b-%Y %H:%M IST")

# ─────────────────────────────────────────────
#  📤  SEND PENDING APPLICATIONS
# ─────────────────────────────────────────────
def send_pending_applications():
    pending = [j for j in config.JOBS if j.get("status") == "pending"]
    if not pending:
        print(f"[{now()}] ✅ No pending applications.")
        return

    print(f"[{now()}] 🚀 Sending {len(pending)} pending applications...")
    os.makedirs("cvs", exist_ok=True)

    for job in pending:
        company = job["company"]
        try:
            # 1. Generate custom CV
            print(f"  📄 Generating CV for {company}...")
            cv_path = generate_cv(job, PROFILE)
            if not cv_path:
                print(f"  ⚠️  Skipping {company} — CV generation failed")
                continue

            # 2. Build custom email
            subject, body = build_application_email(job, PROFILE)

            # 3. Send email with CV attached
            send_email(config.YOUR_EMAIL, config.GMAIL_APP_PASSWORD,
                       to=job["hr_email"], subject=subject,
                       body=body, attachment=cv_path)

            # 4. Update tracker
            update_tracker(company, job["hr_email"], job["role"],
                           status="Sent ✅", notes=f"Applied for {job['role']}")

            # 5. Mark as applied in config (in memory)
            job["status"] = "applied"

            print(f"  ✅ Sent to {company} ({job['hr_email']})")
            time.sleep(4)

        except Exception as e:
            print(f"  ❌ Failed for {company}: {e}")
            update_tracker(company, job["hr_email"], job["role"],
                           status="Failed ❌", notes=str(e)[:100])

    send_tracker_to_self()
    print(f"[{now()}] ✅ Applications done!\n")

# ─────────────────────────────────────────────
#  📥  CHECK INBOX FOR REPLIES
# ─────────────────────────────────────────────
def check_inbox():
    print(f"[{now()}] 🔍 Checking inbox for replies...")
    applied_jobs = [j for j in config.JOBS if j.get("status") == "applied"]
    if not applied_jobs:
        return

    try:
        replies = check_inbox_for_replies(
            config.YOUR_EMAIL, config.GMAIL_APP_PASSWORD,
            applied_jobs, config.INTERVIEW_KEYWORDS
        )

        for job, email_data, is_interview in replies:
            company = job["company"]
            subject = email_data["subject"]

            if is_interview:
                print(f"  🎯 INTERVIEW INVITATION from {company}!")
                send_interview_reply(
                    config.YOUR_EMAIL, config.GMAIL_APP_PASSWORD,
                    job["hr_email"], company, job["role"],
                    subject, config.YOUR_NAME, config.YOUR_PHONE
                )
                update_tracker(company, job["hr_email"], job["role"],
                               status="Interview Scheduled 🎯",
                               reply=f"Yes — {datetime.now().strftime('%d-%b-%Y')}",
                               notes="Interview invite received. Auto-reply sent.")
                # Alert yourself
                send_email(config.YOUR_EMAIL, config.GMAIL_APP_PASSWORD,
                           to=config.YOUR_EMAIL,
                           subject=f"🎯 INTERVIEW CALL from {company}!",
                           body=f"Ajatya,\n\nYou received an interview invitation from {company}!\n\nSubject: {subject}\n\nAn auto-reply has been sent confirming your availability.\n\nPlease check your inbox and follow up directly if needed.\n\n— Your Job Bot")
            else:
                print(f"  📩 Reply from {company}: {subject}")
                update_tracker(company, job["hr_email"], job["role"],
                               status="Replied 📩",
                               reply=f"Yes — {datetime.now().strftime('%d-%b-%Y')}",
                               notes=f"Reply: {subject[:60]}")

        if replies:
            send_tracker_to_self()

    except Exception as e:
        print(f"  ❌ Inbox check error: {e}")

# ─────────────────────────────────────────────
#  📬  SEND FOLLOW-UPS
# ─────────────────────────────────────────────
def send_followups():
    print(f"[{now()}] 📬 Checking follow-ups...")
    due = get_pending_followups()
    for job_data in due:
        try:
            job = next((j for j in config.JOBS if j["company"] == job_data["company"]), job_data)
            send_followup_email(config.YOUR_EMAIL, config.GMAIL_APP_PASSWORD,
                                job, config.YOUR_NAME, config.YOUR_PHONE)
            update_tracker(job_data["company"], job_data["hr_email"], job_data["role"],
                           status="Sent ✅",
                           followup=datetime.now().strftime("%d-%b-%Y"),
                           notes="Follow-up sent after 5 days")
            print(f"  📬 Follow-up sent to {job_data['company']}")
        except Exception as e:
            print(f"  ❌ Follow-up error for {job_data['company']}: {e}")

# ─────────────────────────────────────────────
#  📊  EMAIL TRACKER TO SELF
# ─────────────────────────────────────────────
def send_tracker_to_self():
    from tracker import TRACKER_FILE
    if not os.path.exists(TRACKER_FILE):
        return
    try:
        send_email(config.YOUR_EMAIL, config.GMAIL_APP_PASSWORD,
                   to=config.YOUR_EMAIL,
                   subject=f"📊 Job Tracker Updated — {datetime.now().strftime('%d %b %Y %H:%M')} IST",
                   body="Hi Ajatya,\n\nYour updated job applications tracker is attached.\n\n— Your Job Search Bot",
                   attachment=TRACKER_FILE)
        print(f"  📊 Tracker emailed to {config.YOUR_EMAIL}")
    except Exception as e:
        print(f"  ❌ Tracker email error: {e}")

# ─────────────────────────────────────────────
#  ▶️  MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  AJATYA GANDRAL — JOB SEARCH BOT STARTING")
    print("=" * 60)
    print(f"  Time: {now()}")
    print(f"  Email: {config.YOUR_EMAIL}")
    print("=" * 60 + "\n")

    # Run immediately on start
    send_pending_applications()
    check_inbox()

    # Schedule recurring tasks
    schedule.every(config.CHECK_INBOX_EVERY_HOURS).hours.do(check_inbox)
    schedule.every().day.at(config.TRACKER_EMAIL_TIME).do(send_tracker_to_self)
    schedule.every().day.at("10:00").do(send_followups)
    schedule.every().day.at("08:00").do(send_pending_applications)

    print(f"\n[{now()}] ✅ Bot is running!")
    print(f"  • Inbox check:   every {config.CHECK_INBOX_EVERY_HOURS} hours")
    print(f"  • New job check: daily at 08:00 IST")
    print(f"  • Follow-ups:    daily at 10:00 IST")
    print(f"  • Tracker email: daily at {config.TRACKER_EMAIL_TIME} IST\n")

    while True:
        schedule.run_pending()
        time.sleep(60)
