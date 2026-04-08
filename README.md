# Ajatya Gandral — Job Search Bot

Automated job application bot for Planning Engineer roles in Dubai.

## How it works
1. Add jobs to `config.py` with `"status": "pending"`
2. Bot auto-generates a custom CV for each job
3. Bot sends the email with CV attached
4. Bot monitors inbox every 2 hours for replies
5. Bot auto-replies to interview invitations
6. Bot sends follow-up emails after 5 days if no reply
7. Bot emails you the Excel tracker daily at 9 AM IST

## Setup on Railway

1. Set these environment variables in Railway dashboard:
   - `GMAIL_APP_PASSWORD` — your 16-char Gmail app password

2. Deploy — bot starts automatically

## Adding new jobs (from Claude chat)
Just tell Claude: "Search Planning Engineer jobs Dubai"
Claude will find jobs and update config.py for you automatically.
