from celery import Celery
from app.backend.api.utils.celery_db import mongodb


celery = Celery(
    "agent_tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)


celery.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    task_acks_late=True,
    task_reject_on_worker_lost=True,

    worker_prefetch_multiplier=1,
)




@celery.task(
    bind=True,
    name="create.book",
    max_retries=3,
    default_retry_delay=10
)
def create_book_task(self, book_data):

    try:

        result = mongodb["books"].insert_one(
            book_data
        )

        return {
            "book_id": str(result.inserted_id),
            "status": "created"
        }

    except Exception as exc:
        raise self.retry(exc=exc)

@celery.task(
    bind=True,
    name="tasks.send_email",
    max_retries=3,
    default_retry_delay=10,   # seconds between retries
)
def send_email_task(self, to: str, subject: str, body: str) -> dict:
    """
    Celery task: send an email via Gmail SMTP.
    Retries up to 3 times on transient failures.
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

        return {
            "status": "sent",
            "to": to,
            "subject": subject,
        }

    except smtplib.SMTPException as exc:
        # Retry on SMTP errors (network blip, rate limit, etc.)
        raise self.retry(exc=exc)

    except Exception as exc:
        return {
            "status": "failed",
            "error": str(exc),
        }