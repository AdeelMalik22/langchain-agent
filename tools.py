import os
import smtplib
import imaplib
import email
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from langchain.tools import tool

from dotenv import load_dotenv

load_dotenv()

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

@tool(description="Use this tool to multiply two numbers")
def multiply(a: int, b: int) -> int:
    return a * b

@tool(description="Use this tool to divide two numbers")
def divide(a: float, b: float) -> float:
    if b == 0:
        return "Error: Cannot divide by zero"
    return a / b

@tool(description="Use this tool to add two numbers")
def add(a: int, b: int) -> int:
    return a + b

@tool(description="Use this tool to subtract two numbers")
def subtract(a: int, b: int) -> int:
    return a - b


@tool(description=(
    "Use this tool to explore a GitHub account. "
    "Give it a GitHub username or profile URL and it will list all public repositories "
    "along with the main language used and the repo description. "
    "Example input: 'https://github.com/AdeelMalik22' or just 'AdeelMalik22'"
))
def github_repos(github_input: str) -> str:
    """
    Fetches all public repos for a GitHub user.
    Input can be a full URL like https://github.com/username or just the username.
    """
    # Extract username from URL if full URL is given
    username = github_input.strip().rstrip("/")
    if "github.com/" in username:
        username = username.split("github.com/")[-1]

    url = f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated"
    headers = {"Accept": "application/vnd.github+json"}

    response = requests.get(url, headers=headers)

    if response.status_code == 404:
        return f"GitHub user '{username}' not found."
    if response.status_code != 200:
        return f"GitHub API error: {response.status_code}"

    repos = response.json()
    if not repos:
        return f"No public repositories found for '{username}'."

    result = [f" Public Repositories for @{username}:\n"]
    for repo in repos:
        name        = repo.get("name", "N/A")
        description = repo.get("description") or "No description"
        language    = repo.get("language") or "Not specified"
        stars       = repo.get("stargazers_count", 0)
        repo_url    = repo.get("html_url", "")

        result.append(
            f"• {name}\n"
            f"  Language : {language}\n"
            f"  Stars    : {stars}\n"
            f"  About    : {description}\n"
            f"  URL      : {repo_url}\n"
        )

    return "\n".join(result)


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


@tool
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


@tool
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


@tool
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


ALL_TOOLS = [
    multiply,
    divide,
    add,
    subtract,
    github_repos,
    gmail_read,
    gmail_search,
    gmail_save_draft,
]

TOOL_MAP = {
    "multiply": multiply,
    "divide": divide,
    "add": add,
    "subtract": subtract,
    "github_repos": github_repos,
    "gmail_read": gmail_read,
    "gmail_search": gmail_search,
    "gmail_save_draft": gmail_save_draft,
}