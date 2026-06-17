import smtplib
import imaplib
import email
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from langchain.tools import tool



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


# ─────────────────────────────────────────
#  GMAIL TOOLS
#
#  Credentials are passed as a JSON-like string so the LLM can supply them.
#  Format:  email=you@gmail.com password=your_app_password
#
#  ⚠️  Use a Gmail App Password, NOT your real password.
#  Generate one at: https://myaccount.google.com/apppasswords
# ─────────────────────────────────────────

def _parse_credentials(creds_string: str) -> tuple[str, str]:
    """Parse 'email=x@gmail.com password=abc123' into (email, password)."""
    parts = {}
    for token in creds_string.strip().split():
        if "=" in token:
            key, value = token.split("=", 1)
            parts[key.strip()] = value.strip()
    return parts.get("email", ""), parts.get("password", "")


@tool(description=(
    "Use this tool to write and save an email as a Gmail DRAFT (does NOT send it). "
    "Input format: credentials='email=you@gmail.com password=app_password' "
    "to='recipient@example.com' subject='Hello' body='Email content here'"
))
def gmail_save_draft(credentials: str, to: str, subject: str, body: str) -> str:
    """
    Saves an email as a draft in Gmail via IMAP.
    Uses Gmail App Password for authentication.
    """
    sender_email, app_password = _parse_credentials(credentials)
    if not sender_email or not app_password:
        return "Error: Provide credentials as 'email=x@gmail.com password=your_app_password'"

    # Build the email message
    msg = MIMEMultipart()
    msg["From"]    = sender_email
    msg["To"]      = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        # Connect to Gmail IMAP and append to Drafts folder
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(sender_email, app_password)

        # Gmail's Drafts folder
        status, _ = mail.append(
            '"[Gmail]/Drafts"',
            "\\Draft",
            imaplib.Time2Internaldate(None),
            msg.as_bytes()
        )
        mail.logout()

        if status == "OK":
            return f"✅ Draft saved successfully!\nTo: {to}\nSubject: {subject}"
        else:
            return f"❌ Failed to save draft. IMAP status: {status}"

    except imaplib.IMAP4.error as e:
        return f"❌ IMAP error: {e}\nMake sure you are using a Gmail App Password."
    except Exception as e:
        return f"❌ Unexpected error: {e}"


@tool(description=(
    "Use this tool to read and filter emails from Gmail inbox. "
    "You can filter by sender, subject keyword, or read the latest N emails. "
    "Input format: credentials='email=you@gmail.com password=app_password' "
    "filter_by='sender' filter_value='boss@company.com' limit=5"
))
def gmail_read_emails(
    credentials: str,
    filter_by: str = "all",
    filter_value: str = "",
    limit: int = 5
) -> str:
    """
    Reads emails from Gmail inbox.
    filter_by options: 'all', 'sender', 'subject'
    """
    sender_email, app_password = _parse_credentials(credentials)
    if not sender_email or not app_password:
        return "Error: Provide credentials as 'email=x@gmail.com password=your_app_password'"

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(sender_email, app_password)
        mail.select("inbox")

        # Build IMAP search query
        if filter_by == "sender" and filter_value:
            search_query = f'(FROM "{filter_value}")'
        elif filter_by == "subject" and filter_value:
            search_query = f'(SUBJECT "{filter_value}")'
        else:
            search_query = "ALL"

        status, messages = mail.search(None, search_query)
        if status != "OK":
            return "❌ Failed to search emails."

        email_ids = messages[0].split()
        if not email_ids:
            return "📭 No emails found matching your filter."

        # Get the latest `limit` emails
        recent_ids = email_ids[-limit:][::-1]

        result = [f"📬 Found {len(email_ids)} email(s). Showing latest {len(recent_ids)}:\n"]

        for eid in recent_ids:
            status, msg_data = mail.fetch(eid, "(RFC822)")
            if status != "OK":
                continue

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            subject = msg.get("Subject", "No Subject")
            sender  = msg.get("From", "Unknown")
            date    = msg.get("Date", "Unknown Date")

            # Extract plain text body
            body_text = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body_text = part.get_payload(decode=True).decode(errors="ignore")
                        break
            else:
                body_text = msg.get_payload(decode=True).decode(errors="ignore")

            # Trim body preview
            preview = body_text.strip()[:200] + ("..." if len(body_text) > 200 else "")

            result.append(
                f"─────────────────────\n"
                f"From    : {sender}\n"
                f"Subject : {subject}\n"
                f"Date    : {date}\n"
                f"Preview : {preview}\n"
            )

        mail.logout()
        return "\n".join(result)

    except imaplib.IMAP4.error as e:
        return f"❌ IMAP error: {e}\nMake sure you're using a Gmail App Password."
    except Exception as e:
        return f"❌ Unexpected error: {e}"


ALL_TOOLS = [multiply, divide, add, subtract, github_repos, gmail_save_draft, gmail_read_emails]

TOOL_MAP = {
    "multiply":          multiply,
    "divide":            divide,
    "add":               add,
    "subtract":          subtract,
    "github_repos":      github_repos,
    "gmail_save_draft":  gmail_save_draft,
    "gmail_read_emails": gmail_read_emails,
}