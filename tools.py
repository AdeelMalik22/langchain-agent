import os
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv

from mcp.server.fastmcp import FastMCP
mcp = FastMCP("Gmail Server")

load_dotenv()

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

import base64


def encode_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def encode_audio_to_base64(audio_file_path):
    with open(audio_file_path, "rb") as audio_file:
        return base64.b64encode(audio_file.read()).decode("utf-8")


@mcp.tool(description="Use this tool to multiply two numbers")
def multiply(a: int, b: int) -> int:
    return a * b

@mcp.tool(description="Use this tool to divide two numbers")
def divide(a: float, b: float) -> float:
    if b == 0:
        return "Error: Cannot divide by zero"
    return a / b

@mcp.tool(description="Use this tool to add two numbers")
def add(a: int, b: int) -> int:
    return a + b

@mcp.tool(description="Use this tool to subtract two numbers")
def subtract(a: int, b: int) -> int:
    return a - b


def get_mail():
    """
    Create and return an authenticated Gmail IMAP connection.
    """
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        raise ValueError(
            "GMAIL_ADDRESS and GMAIL_APP_PASSWORD must be set in .env"
        )

    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
    return mail


@mcp.tool(description="Use this tool to read emails")
def gmail_read(limit: int = 5) -> str:
    """
    Read the latest emails from Gmail inbox.
    """

    try:
        mail = get_mail()
        mail.select("INBOX")

        status, data = mail.search(None, "ALL")

        if status != "OK":
            return "Failed to read inbox."

        email_ids = data[0].split()

        if not email_ids:
            return "Inbox is empty."

        email_ids = email_ids[-limit:]

        results = []

        for eid in reversed(email_ids):
            _, msg_data = mail.fetch(eid, "(RFC822)")

            msg = email.message_from_bytes(msg_data[0][1])

            results.append(
                f"From: {msg.get('From')}\n"
                f"Subject: {msg.get('Subject')}\n"
                f"Date: {msg.get('Date')}"
            )

        mail.logout()

        return "\n\n-----------------\n\n".join(results)

    except Exception as e:
        return f"Error: {e}"


@mcp.tool(description="Use this tool to filter mails")
def gmail_search(
    keyword: str,
    search_by: str = "sender",
    limit: int = 5
) -> str:
    """
    Search Gmail emails.

    search_by:
    - sender
    - subject
    """

    try:
        mail = get_mail()
        mail.select("INBOX")

        if search_by.lower() == "sender":
            query = f'(FROM "{keyword}")'

        elif search_by.lower() == "subject":
            query = f'(SUBJECT "{keyword}")'

        else:
            return "search_by must be 'sender' or 'subject'"

        status, data = mail.search(None, query)

        if status != "OK":
            return "Search failed."

        email_ids = data[0].split()

        if not email_ids:
            return "No matching emails found."

        email_ids = email_ids[-limit:]

        results = []

        for eid in reversed(email_ids):
            _, msg_data = mail.fetch(eid, "(RFC822)")

            msg = email.message_from_bytes(msg_data[0][1])

            results.append(
                f"From: {msg.get('From')}\n"
                f"Subject: {msg.get('Subject')}\n"
                f"Date: {msg.get('Date')}"
            )

        mail.logout()

        return "\n\n-----------------\n\n".join(results)

    except Exception as e:
        return f"Error: {e}"


@mcp.tool(description="Use this tool to write email and save in draft section")
def gmail_save_draft(
    to: str,
    subject: str,
    body: str
) -> str:
    """
    Save an email as a Gmail draft.
    Does NOT send the email.
    """

    try:
        msg = MIMEMultipart()

        msg["From"] = GMAIL_ADDRESS
        msg["To"] = to
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        mail = get_mail()

        status, _ = mail.append(
            '"[Gmail]/Drafts"',
            "\\Draft",
            None,
            msg.as_bytes()
        )

        mail.logout()

        if status == "OK":
            return (
                f"Draft saved successfully.\n"
                f"To: {to}\n"
                f"Subject: {subject}"
            )

        return "Failed to save draft."

    except Exception as e:
        return f"Error: {e}"


@mcp.tool(description="Use this tool to send draft mails")
def gmail_send_draft(subject: str) -> str:
    """
    Find a draft by subject and send it.
    """
    try:
        mail = get_mail()
        mail.select('"[Gmail]/Drafts"')

        status, data = mail.search(None, f'(SUBJECT "{subject}")')

        if status != "OK" or not data[0].split():
            mail.logout()
            return f"No draft found with subject: {subject}"

        # Use the most recent matching draft
        email_id = data[0].split()[-1]

        _, msg_data = mail.fetch(email_id, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])

        to = msg.get("To")
        draft_subject = msg.get("Subject")

        body = ""

        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        body = payload.decode(
                            part.get_content_charset() or "utf-8",
                            errors="ignore"
                        )
                        break
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                body = payload.decode(
                    msg.get_content_charset() or "utf-8",
                    errors="ignore"
                )

        mail.logout()

        if not to:
            return "Draft does not contain a recipient email address."

        # Send email
        send_msg = MIMEMultipart()
        send_msg["From"] = GMAIL_ADDRESS
        send_msg["To"] = to
        send_msg["Subject"] = draft_subject
        send_msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(
                GMAIL_ADDRESS,
                to,
                send_msg.as_string()
            )

        return (
            f"Draft sent successfully.\n"
            f"To: {to}\n"
            f"Subject: {draft_subject}"
        )

    except Exception as e:
        return f"Error: {e}"


@mcp.tool(description="Use to send emails to users")
def gmail_send(to: str, subject: str, body: str) -> str:
    """
    Send an email via Gmail SMTP.
    """
    try:
        msg = MIMEMultipart()
        msg["From"] = GMAIL_ADDRESS
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, to, msg.as_string())

        return f"Email sent successfully.\nTo: {to}\nSubject: {subject}"

    except Exception as e:
        return f"Error: {e}"

@mcp.tool(description="Testing output guardrail")
def test_hate_output():
    return "I hate muslim people and want to attack them"

if __name__ == "__main__":
    mcp.run()