"""
Email sender — sends job application emails with CV attachments
"""
import smtplib
import imaplib
import email as email_lib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from datetime import datetime

def now_str():
    return datetime.now().strftime("%d-%b-%Y %H:%M IST")

def send_email(your_email, password, to, subject, body, attachment=None):
    msg = MIMEMultipart()
    msg["From"]    = your_email
    msg["To"]      = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    if attachment and os.path.exists(attachment):
        with open(attachment, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition",
                            f'attachment; filename="{os.path.basename(attachment)}"')
            msg.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(your_email, password)
        server.sendmail(your_email, to, msg.as_string())

def build_application_email(job, profile):
    company = job["company"]
    role    = job["role"]
    reqs    = job.get("key_requirements", "").lower()
    name    = profile["name"]
    email   = profile["email"]
    phone   = profile["phone"]

    # Tailor opening line based on job type
    if "junior" in role.lower():
        opening = f"I am writing to apply for the {role} position at {company}. With 3+ years of hands-on experience in construction scheduling and Primavera P6, I am eager to grow within your team and contribute to your planning operations."
    elif "consultancy" in reqs or "consultant" in reqs:
        opening = f"I am writing to apply for the {role} position at {company}. With 3+ years of project controls and Primavera P6 experience — combined with a postgraduate degree from Heriot-Watt University Dubai — I bring a consultancy-oriented mindset and strong documentation capabilities to your team."
    elif "claims" in reqs or "fidic" in reqs:
        opening = f"I am writing to apply for the {role} position at {company}. My experience in Primavera P6, delay log maintenance, FIDIC contract management, and claims-related documentation aligns directly with your project controls requirements."
    else:
        opening = f"I am writing to apply for the {role} position at {company}. With 3+ years of progressive experience in construction scheduling, project controls, and Primavera P6 across residential, commercial, and government infrastructure projects, I am confident I will add immediate value to your planning team."

    # Build highlights based on requirements
    highlights = [
        "• Primavera P6 — Baseline scheduling, critical path analysis, progress tracking, and earned value analysis",
        "• UAE Ministry of Education — Degree Attestation & Equivalency Certificate (employment-ready)",
        "• Valid Dubai Driving License",
    ]
    if "site" in reqs or "supervision" in reqs:
        highlights.append("• Proven site supervision and HSE compliance — zero LTI incidents achieved")
    if "claims" in reqs or "fidic" in reqs:
        highlights.append("• FIDIC contract management and claims documentation experience from Heriot-Watt Dubai PG programme")
    if "delay" in reqs or "recovery" in reqs:
        highlights.append("• KEY ACHIEVEMENT: Recovered a 14 km road project from 3-week overrun risk to within 5 days of original target")
    if "bim" in reqs or "revit" in reqs:
        highlights.append("• Proficient in Revit BIM, Navisworks, BIM 360, and AutoCAD")
    highlights.append("• Postgraduate Certificate in the Built Environment, Heriot-Watt University Dubai (Nov 2025)")

    highlights_text = "\n".join(highlights)

    body = f"""Dear Hiring Manager,

{opening}

Key highlights of my profile:
{highlights_text}

I am immediately available, visa-ready, and based in India with full readiness to relocate to Dubai upon offer. I would welcome the opportunity to discuss how my experience aligns with your current project requirements.

Please find my tailored CV attached for your review.

Yours sincerely,
{name}
{role}
📧 {email}
📞 {phone} (WhatsApp available)"""

    subject = f"Application for {role} — {name} | Primavera P6 | Heriot-Watt Dubai | UAE Attested | Immediate Availability"

    return subject, body

def check_inbox_for_replies(your_email, password, jobs, interview_keywords):
    """Check inbox for replies from HR emails — returns list of (job, email_data, is_interview)"""
    results = []
    hr_emails = {j["hr_email"].lower(): j for j in jobs}

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(your_email, password)
        mail.select("inbox")

        for hr_email, job in hr_emails.items():
            _, msgs = mail.search(None, f'(FROM "{hr_email}" UNSEEN)')
            for msg_id in msgs[0].split():
                _, data = mail.fetch(msg_id, "(RFC822)")
                raw = email_lib.message_from_bytes(data[0][1])
                subject  = raw.get("Subject", "")
                sender   = raw.get("From", "")
                body_txt = ""
                if raw.is_multipart():
                    for part in raw.walk():
                        if part.get_content_type() == "text/plain":
                            body_txt = part.get_payload(decode=True).decode(errors="ignore")
                            break
                else:
                    body_txt = raw.get_payload(decode=True).decode(errors="ignore")

                combined     = (subject + " " + body_txt).lower()
                is_interview = any(k in combined for k in interview_keywords)
                results.append((job, {"subject": subject, "sender": sender, "body": body_txt}, is_interview))

        mail.logout()
    except Exception as e:
        print(f"[{now_str()}] ❌ Inbox check error: {e}")

    return results

def send_interview_reply(your_email, password, hr_email, company, role, original_subject, name, phone):
    body = f"""Dear Hiring Team,

Thank you very much for considering my application for the {role} position at {company}.

I am delighted to receive your invitation and confirm that I am available for the interview. Please let me know your preferred date, time, and format (in-person / video call / phone), and I will make myself fully available.

A few points for your reference:
• I am currently based in India and can attend video or phone interviews at any time convenient for you (IST timezone)
• I am immediately available to relocate to Dubai upon offer
• My UAE credentials (degree attestation, equivalency certificate, and Dubai driving license) are all verified and ready

I look forward to the opportunity to discuss how my experience in Primavera P6, construction scheduling, and project controls can contribute to {company}'s projects.

Please feel free to reach me directly at:
📧 {your_email}
📞 {phone} (WhatsApp available)

Thank you once again. I look forward to hearing from you.

Yours sincerely,
{name}
Planning Engineer"""

    send_email(your_email, password,
               to=hr_email,
               subject=f"Re: {original_subject}",
               body=body)

def send_followup_email(your_email, password, job, name, phone):
    company = job["company"]
    role    = job["role"]
    hr_email = job["hr_email"]

    body = f"""Dear Hiring Manager,

I hope this message finds you well. I am writing to follow up on my application for the {role} position at {company}, submitted approximately 5 business days ago.

I remain very enthusiastic about this opportunity and would be delighted to discuss how my experience in Primavera P6, construction scheduling, and project controls can benefit your team.

Please let me know if you require any additional information or documents. I am immediately available for an interview at your convenience — in-person in Dubai or via video/phone call from India.

Thank you for your time and consideration.

Yours sincerely,
{name}
Planning Engineer
📧 {your_email}
📞 {phone} (WhatsApp available)"""

    send_email(your_email, password,
               to=hr_email,
               subject=f"Follow-Up: Application for {role} — {name} | Primavera P6 | UAE Attested",
               body=body)
