"""
=============================================================
  AJATYA GANDRAL — JOB SEARCH BOT
  Works on GitHub Actions (--once) or Railway (continuous)
=============================================================
"""
import os
import sys
import time
import schedule
from datetime import datetime

import config
from cv_generator import generate_cv
from emailer import (send_email, build_application_email,
                     check_inbox_for_replies, send_interview_reply,
                     send_followup_email)
from tracker import update_tracker, get_pending_followups

# Read password from env variable OR config file
GMAIL_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", config.GMAIL_APP_PASSWORD)

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

# ── Send pending applications ─────────────────────────────
def send_pending_applications():
    pending = [j for j in config.JOBS if j.get("status") == "pending"]
    if not pending:
        print("[" + now() + "] No pending applications.")
        return

    print("[" + now() + "] Sending " + str(len(pending)) + " pending applications...")
    os.makedirs("cvs", exist_ok=True)

    for job in pending:
        company = job["company"]
        try:
            print("  Generating CV for " + company + "...")
            cv_path = generate_cv(job, PROFILE)
            if not cv_path:
                print("  Skipping " + company + " — CV generation failed")
                continue

            subject, body = build_application_email(job, PROFILE)
            send_email(config.YOUR_EMAIL, GMAIL_PASSWORD,
                       to=job["hr_email"], subject=subject,
                       body=body, attachment=cv_path)

            update_tracker(company, job["hr_email"], job["role"],
                           status="Sent", notes="Applied for " + job["role"])
            job["status"] = "applied"
            print("  Sent to " + company + " (" + job["hr_email"] + ")")
            time.sleep(4)

        except Exception as e:
            print("  Failed for " + company + ": " + str(e))
            update_tracker(company, job["hr_email"], job["role"],
                           status="Failed", notes=str(e)[:100])

    send_tracker_to_self()

# ── Check inbox ───────────────────────────────────────────
def check_inbox():
    print("[" + now() + "] Checking inbox for replies...")
    applied_jobs = [j for j in config.JOBS if j.get("status") == "applied"]
    if not applied_jobs:
        return

    try:
        replies = check_inbox_for_replies(
            config.YOUR_EMAIL, GMAIL_PASSWORD,
            applied_jobs, config.INTERVIEW_KEYWORDS
        )
        for job, email_data, is_interview in replies:
            company = job["company"]
            subject = email_data["subject"]
            if is_interview:
                print("  INTERVIEW from " + company + "!")
                send_interview_reply(
                    config.YOUR_EMAIL, GMAIL_PASSWORD,
                    job["hr_email"], company, job["role"],
                    subject, config.YOUR_NAME, config.YOUR_PHONE
                )
                update_tracker(company, job["hr_email"], job["role"],
                               status="Interview Scheduled",
                               reply="Yes - " + datetime.now().strftime("%d-%b-%Y"),
                               notes="Interview invite. Auto-reply sent.")
                send_email(config.YOUR_EMAIL, GMAIL_PASSWORD,
                           to=config.YOUR_EMAIL,
                           subject="INTERVIEW CALL from " + company + "!",
                           body="Ajatya,\n\nInterview invitation from " + company + "!\n\nSubject: " + subject + "\n\nAuto-reply sent confirming availability.\n\n— Job Bot")
            else:
                print("  Reply from " + company + ": " + subject)
                update_tracker(company, job["hr_email"], job["role"],
                               status="Replied",
                               reply="Yes - " + datetime.now().strftime("%d-%b-%Y"),
                               notes="Reply: " + subject[:60])
        if replies:
            send_tracker_to_self()
    except Exception as e:
        print("  Inbox check error: " + str(e))

# ── Send follow-ups ───────────────────────────────────────
def send_followups():
    print("[" + now() + "] Checking follow-ups...")
    due = get_pending_followups()
    for job_data in due:
        try:
            job = next((j for j in config.JOBS if j["company"] == job_data["company"]), job_data)
            send_followup_email(config.YOUR_EMAIL, GMAIL_PASSWORD,
                                job, config.YOUR_NAME, config.YOUR_PHONE)
            update_tracker(job_data["company"], job_data["hr_email"], job_data["role"],
                           status="Sent",
                           followup=datetime.now().strftime("%d-%b-%Y"),
                           notes="Follow-up sent after 5 days")
            print("  Follow-up sent to " + job_data["company"])
        except Exception as e:
            print("  Follow-up error: " + str(e))

# ── Email tracker ─────────────────────────────────────────
def send_tracker_to_self():
    from tracker import TRACKER_FILE
    if not os.path.exists(TRACKER_FILE):
        return
    try:
        send_email(config.YOUR_EMAIL, GMAIL_PASSWORD,
                   to=config.YOUR_EMAIL,
                   subject="Job Tracker Updated - " + datetime.now().strftime("%d %b %Y %H:%M") + " IST",
                   body="Hi Ajatya,\n\nYour updated job applications tracker is attached.\n\n— Job Search Bot",
                   attachment=TRACKER_FILE)
        print("  Tracker emailed to " + config.YOUR_EMAIL)
    except Exception as e:
        print("  Tracker email error: " + str(e))

# ── Main ──────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  AJATYA GANDRAL - JOB SEARCH BOT")
    print("=" * 55)
    print("  Time:  " + now())
    print("  Email: " + config.YOUR_EMAIL)
    print("=" * 55)

    # --once flag = GitHub Actions mode (run once and exit)
    if "--once" in sys.argv:
        print("\n  Mode: GitHub Actions (run once)\n")
        send_pending_applications()
        check_inbox()
        send_followups()
        print("\n  Done!")

    else:
        # Continuous mode for Railway/server
        print("\n  Mode: Continuous\n")
        send_pending_applications()
        check_inbox()

        schedule.every(config.CHECK_INBOX_EVERY_HOURS).hours.do(check_inbox)
        schedule.every().day.at(config.TRACKER_EMAIL_TIME).do(send_tracker_to_self)
        schedule.every().day.at("10:00").do(send_followups)
        schedule.every().day.at("08:00").do(send_pending_applications)

        print("\n  Bot running continuously...")
        print("  Inbox check: every " + str(config.CHECK_INBOX_EVERY_HOURS) + " hours")
        print("  Press CTRL+C to stop.\n")

        while True:
            schedule.run_pending()
            time.sleep(60)
