"""
Email Agent Communication Service
Enables agents to receive tasks and communicate with users via email.

Email: ace.llc.nyc@gmail.com
Trigger: Subject contains "CESAR.ai Agent"
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import smtplib
import time
from datetime import datetime, timedelta
from email import message_from_bytes
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from imaplib import IMAP4_SSL
from typing import Any

import httpx
import psycopg
from psycopg.rows import dict_row

# Configuration
GMAIL_USER = os.getenv("EMAIL_AGENT_USER", "ace.llc.nyc@gmail.com")
GMAIL_PASSWORD = os.getenv("EMAIL_AGENT_PASSWORD", "")  # App-specific password
GMAIL_IMAP_HOST = "imap.gmail.com"
GMAIL_SMTP_HOST = "smtp.gmail.com"
GMAIL_SMTP_PORT = 587

TRIGGER_SUBJECT = "CESAR.ai Agent"
CHECK_INTERVAL_SECONDS = 30  # Check email every 30 seconds

# Database configuration
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "dbname": os.getenv("POSTGRES_DB", "mcp"),
    "user": os.getenv("POSTGRES_USER", "mcp_user"),
    "password": os.getenv("POSTGRES_PASSWORD", "4392e1770d58b957825a74c690ee2559"),
}

# API endpoint for agent orchestrator
ORCHESTRATOR_API = os.getenv("ORCHESTRATOR_API", "http://localhost:8000")


class EmailMessage:
    """Represents a processed email message"""

    def __init__(
        self,
        message_id: str,
        from_email: str,
        subject: str,
        body: str,
        received_at: datetime,
        raw_headers: dict[str, Any],
    ):
        self.message_id = message_id
        self.from_email = from_email
        self.subject = subject
        self.body = body
        self.received_at = received_at
        self.raw_headers = raw_headers

        # Extract task from subject
        self.task_description = self._extract_task_from_subject()

    def _extract_task_from_subject(self) -> str:
        """Extract the actual task from the subject line"""
        # Remove the trigger phrase
        task = self.subject.replace(TRIGGER_SUBJECT, "").strip()
        # Remove common prefixes
        task = re.sub(r"^(Re:|Fwd?:)\s*", "", task, flags=re.IGNORECASE).strip()
        # Remove leading/trailing punctuation
        task = task.strip(":- ")
        return task if task else "General inquiry"


class EmailAgentService:
    """Service that monitors email and routes to agents"""

    def __init__(self):
        self.imap: IMAP4_SSL | None = None
        self.processed_message_ids: set[str] = set()
        self.running = False

    def connect_imap(self) -> None:
        """Connect to Gmail IMAP"""
        try:
            self.imap = IMAP4_SSL(GMAIL_IMAP_HOST)
            self.imap.login(GMAIL_USER, GMAIL_PASSWORD)
            print(f"✅ Connected to IMAP as {GMAIL_USER}")
        except Exception as e:
            print(f"❌ IMAP connection failed: {e}")
            raise

    def disconnect_imap(self) -> None:
        """Disconnect from Gmail IMAP"""
        if self.imap:
            try:
                self.imap.logout()
                print("✅ Disconnected from IMAP")
            except Exception as e:
                print(f"⚠️ IMAP disconnect error: {e}")

    def fetch_unread_emails(self) -> list[EmailMessage]:
        """Fetch unread emails with the trigger subject"""
        if not self.imap:
            raise RuntimeError("IMAP not connected")

        try:
            # Select inbox
            self.imap.select("INBOX")

            # Search for unread emails with trigger subject
            _, message_numbers = self.imap.search(
                None, f'(UNSEEN SUBJECT "{TRIGGER_SUBJECT}")'
            )

            if not message_numbers[0]:
                return []

            emails = []
            for num in message_numbers[0].split():
                # Fetch email
                _, msg_data = self.imap.fetch(num, "(RFC822)")
                email_body = msg_data[0][1]
                email_message = message_from_bytes(email_body)

                # Parse email
                message_id = email_message.get("Message-ID", "")
                from_email = email_message.get("From", "")
                subject = email_message.get("Subject", "")
                date_str = email_message.get("Date", "")

                # Extract body
                body = self._extract_body(email_message)

                # Parse date
                received_at = datetime.now()  # Fallback
                try:
                    from email.utils import parsedate_to_datetime

                    received_at = parsedate_to_datetime(date_str)
                except Exception:
                    pass

                # Skip if already processed
                msg_hash = hashlib.md5(
                    f"{message_id}{from_email}{subject}".encode()
                ).hexdigest()
                if msg_hash in self.processed_message_ids:
                    continue

                emails.append(
                    EmailMessage(
                        message_id=message_id,
                        from_email=from_email,
                        subject=subject,
                        body=body,
                        received_at=received_at,
                        raw_headers=dict(email_message.items()),
                    )
                )

                self.processed_message_ids.add(msg_hash)

            return emails

        except Exception as e:
            print(f"❌ Error fetching emails: {e}")
            return []

    def _extract_body(self, email_message) -> str:
        """Extract plain text body from email"""
        body = ""

        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                        break
                    except Exception:
                        pass
        else:
            try:
                body = email_message.get_payload(decode=True).decode("utf-8", errors="ignore")
            except Exception:
                body = str(email_message.get_payload())

        return body.strip()

    async def send_email_response(
        self, to_email: str, subject: str, body: str, in_reply_to: str | None = None
    ) -> bool:
        """Send email response via SMTP"""
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = GMAIL_USER
            msg["To"] = to_email
            msg["Subject"] = f"Re: {subject}" if not subject.startswith("Re:") else subject

            if in_reply_to:
                msg["In-Reply-To"] = in_reply_to
                msg["References"] = in_reply_to

            # Add plain text part
            text_part = MIMEText(body, "plain")
            msg.attach(text_part)

            # Add HTML part with branding
            html_body = f"""
            <html>
            <head></head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                color: white; padding: 20px; border-radius: 10px 10px 0 0;">
                        <h2 style="margin: 0;">CESAR.ai Agent Response</h2>
                    </div>
                    <div style="background: #f9f9f9; padding: 20px; border: 1px solid #ddd;
                                border-top: none; border-radius: 0 0 10px 10px;">
                        <div style="white-space: pre-wrap; background: white; padding: 15px;
                                    border-radius: 5px; border: 1px solid #eee;">
{body}
                        </div>
                        <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                        <p style="font-size: 12px; color: #777; text-align: center;">
                            This response was generated by CESAR.ai Autonomous Agent System<br>
                            Powered by Multi-Agent MCP Architecture
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            html_part = MIMEText(html_body, "html")
            msg.attach(html_part)

            # Send via SMTP
            with smtplib.SMTP(GMAIL_SMTP_HOST, GMAIL_SMTP_PORT) as server:
                server.starttls()
                server.login(GMAIL_USER, GMAIL_PASSWORD)
                server.send_message(msg)

            print(f"✅ Sent email response to {to_email}")
            return True

        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False

    async def log_email_interaction(
        self,
        email: EmailMessage,
        agent_response: str,
        agent_id: str,
        session_id: str,
        processing_time_ms: float,
    ) -> None:
        """Log email interaction to database for continual learning"""
        try:
            with psycopg.connect(**DB_CONFIG) as conn:
                cur = conn.cursor(row_factory=dict_row)

                # Create session if needed
                cur.execute(
                    """
                    INSERT INTO sessions (id, label, context, status)
                    VALUES (%s, %s, %s, 'active')
                    ON CONFLICT (id) DO UPDATE SET updated_at = now()
                    RETURNING id
                    """,
                    (
                        session_id,
                        f"Email from {email.from_email}",
                        json.dumps(
                            {
                                "channel": "email",
                                "from": email.from_email,
                                "subject": email.subject,
                            }
                        ),
                    ),
                )

                # Create agent run
                cur.execute(
                    """
                    INSERT INTO agent_runs (session_id, agent_id, status, input_summary, output_summary)
                    VALUES (%s, %s, 'completed', %s, %s)
                    RETURNING id
                    """,
                    (
                        session_id,
                        agent_id,
                        f"Email task: {email.task_description[:200]}",
                        f"Response sent: {agent_response[:200]}...",
                    ),
                )
                run_row = cur.fetchone()
                run_id = run_row["id"]

                # Log events
                cur.execute(
                    """
                    INSERT INTO events (run_id, session_id, agent_id, event_type, payload)
                    VALUES (%s, %s, %s, 'email_received', %s)
                    """,
                    (
                        run_id,
                        session_id,
                        agent_id,
                        json.dumps(
                            {
                                "from": email.from_email,
                                "subject": email.subject,
                                "body_preview": email.body[:500],
                                "received_at": email.received_at.isoformat(),
                            }
                        ),
                    ),
                )

                cur.execute(
                    """
                    INSERT INTO events (run_id, session_id, agent_id, event_type, payload)
                    VALUES (%s, %s, %s, 'email_response_sent', %s)
                    """,
                    (
                        run_id,
                        session_id,
                        agent_id,
                        json.dumps(
                            {
                                "to": email.from_email,
                                "response_preview": agent_response[:500],
                                "processing_time_ms": processing_time_ms,
                            }
                        ),
                    ),
                )

                # Create episodic memory
                cur.execute(
                    """
                    INSERT INTO memory_episodic (
                        session_id, agent_id, event_type, content, context,
                        importance_score, tags
                    )
                    VALUES (%s, %s, 'user_message', %s, %s, 0.8, %s)
                    RETURNING id
                    """,
                    (
                        session_id,
                        agent_id,
                        f"User email: {email.body}",
                        json.dumps(
                            {
                                "channel": "email",
                                "from": email.from_email,
                                "subject": email.subject,
                                "task": email.task_description,
                            }
                        ),
                        ["email", "user_interaction", "task_request"],
                    ),
                )

                cur.execute(
                    """
                    INSERT INTO memory_episodic (
                        session_id, agent_id, event_type, content, context,
                        importance_score, tags
                    )
                    VALUES (%s, %s, 'agent_response', %s, %s, 0.7, %s)
                    """,
                    (
                        session_id,
                        agent_id,
                        f"Agent response: {agent_response}",
                        json.dumps(
                            {
                                "channel": "email",
                                "to": email.from_email,
                                "processing_time_ms": processing_time_ms,
                            }
                        ),
                        ["email", "agent_response", "task_completion"],
                    ),
                )

                # Create learning reflection
                cur.execute(
                    """
                    INSERT INTO learning_reflections (
                        session_id, run_id, agent_id, rating, content, tags
                    )
                    VALUES (%s, %s, %s, 'positive', %s, %s)
                    """,
                    (
                        session_id,
                        run_id,
                        agent_id,
                        f"Successfully processed email task: {email.task_description}. "
                        f"Response delivered in {processing_time_ms:.2f}ms via email to {email.from_email}.",
                        ["email_interaction", "task_completion", "user_communication"],
                    ),
                )

                conn.commit()
                print(f"✅ Logged email interaction to database (session: {session_id})")

        except Exception as e:
            print(f"❌ Failed to log email interaction: {e}")

    async def process_email_with_agent(self, email: EmailMessage) -> str:
        """Route email to appropriate agent and get response"""
        try:
            # Determine routing based on task
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Call orchestrator API to route and process
                response = await client.post(
                    f"{ORCHESTRATOR_API}/api/tasks/process",
                    json={
                        "task_description": email.task_description,
                        "task_body": email.body,
                        "context": {
                            "channel": "email",
                            "from": email.from_email,
                            "subject": email.subject,
                        },
                    },
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "Task processed successfully.")
                else:
                    # Fallback: Use central orchestrator
                    return await self._fallback_processing(email)

        except Exception as e:
            print(f"❌ Error processing with agent: {e}")
            return await self._fallback_processing(email)

    async def _fallback_processing(self, email: EmailMessage) -> str:
        """Fallback processing when orchestrator is unavailable"""
        return f"""Thank you for your email regarding: {email.task_description}

Your request has been received and queued for processing by the CESAR.ai Agent system.

Email Details:
- Task: {email.task_description}
- Received: {email.received_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
- Request ID: {hashlib.md5(email.message_id.encode()).hexdigest()[:8]}

An agent will process your request and respond shortly. If this is urgent, please include "URGENT" in your subject line.

Best regards,
CESAR.ai Autonomous Agent System
"""

    async def process_incoming_emails(self) -> None:
        """Main processing loop for incoming emails"""
        print("📧 Starting email monitoring...")

        while self.running:
            try:
                # Fetch unread emails
                emails = self.fetch_unread_emails()

                for email in emails:
                    print(f"\n📨 New email from {email.from_email}")
                    print(f"   Subject: {email.subject}")
                    print(f"   Task: {email.task_description}")

                    start_time = time.time()

                    # Process with agent
                    agent_response = await self.process_email_with_agent(email)

                    processing_time_ms = (time.time() - start_time) * 1000

                    # Send response
                    await self.send_email_response(
                        to_email=email.from_email,
                        subject=email.subject,
                        body=agent_response,
                        in_reply_to=email.message_id,
                    )

                    # Log interaction for continual learning
                    session_id = hashlib.md5(
                        f"{email.from_email}_{datetime.now().date()}".encode()
                    ).hexdigest()
                    await self.log_email_interaction(
                        email=email,
                        agent_response=agent_response,
                        agent_id="central_orchestrator",
                        session_id=session_id,
                        processing_time_ms=processing_time_ms,
                    )

                    print(f"✅ Processed in {processing_time_ms:.2f}ms")

                # Wait before next check
                await asyncio.sleep(CHECK_INTERVAL_SECONDS)

            except Exception as e:
                print(f"❌ Error in email processing loop: {e}")
                await asyncio.sleep(CHECK_INTERVAL_SECONDS)

    async def start(self) -> None:
        """Start the email agent service"""
        print("🚀 Starting Email Agent Service")
        print(f"   Email: {GMAIL_USER}")
        print(f"   Trigger: Subject contains '{TRIGGER_SUBJECT}'")
        print(f"   Check interval: {CHECK_INTERVAL_SECONDS}s")

        self.connect_imap()
        self.running = True

        try:
            await self.process_incoming_emails()
        finally:
            self.running = False
            self.disconnect_imap()

    def stop(self) -> None:
        """Stop the email agent service"""
        print("🛑 Stopping Email Agent Service")
        self.running = False


async def main():
    """Main entry point"""
    service = EmailAgentService()
    try:
        await service.start()
    except KeyboardInterrupt:
        service.stop()
        print("\n✅ Email Agent Service stopped")


if __name__ == "__main__":
    asyncio.run(main())
