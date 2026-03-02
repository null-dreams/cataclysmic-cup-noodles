import base64
import os.path
import logging
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from email.utils import parsedate_to_datetime, parseaddr

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

def init_cred(SCOPES):
    try:
        logger.info("Initializing credentials...")
        creds = None
        if os.path.exists("token.json"):
            logger.debug("Found existing token.json")
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        if not creds or not creds.valid:
            logger.info("Credentials invalid or missing, refreshing/reauthenticating...")
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired credentials...")
                creds.refresh(Request())
            else:
                if not os.path.exists("credentials.json"):
                    logger.error("credentials.json not found")
                    raise FileNotFoundError("credentials.json not found")
                logger.info("Running OAuth flow...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
                creds = flow.run_local_server(port=0)
            with open("token.json", "w") as token:
                token.write(creds.to_json())
                logger.info("Saved new token.json")
        logger.info("Authentication successful")
        return creds

    except Exception:
        logger.exception("Authentication failed")
        raise

def get_service():
    logger.info("Building Gmail service...")
    SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
    service = build("gmail", "v1", credentials=init_cred(SCOPES))
    logger.info("Gmail service built successfully")
    return service

def get_header(headers):
    parsed_date = None
    parsed_addr = ("Unknown", "Unknown")

    for header in headers:
        if header['name'] == "Date":
            try:
                parsed_date = parsedate_to_datetime(header['value'])
            except Exception:
                logger.warning("Failed to parse Date header")

        elif header['name'] == "From":
            parsed_addr = parseaddr(header['value'])
    if not parsed_date:
        logger.warning("Date header missing or invalid")

    return {
        "sender_name": parsed_addr[0] or "Unknown",
        "sender_email": parsed_addr[1] or "Unknown",
        "date": parsed_date.strftime("%d %b %Y") if parsed_date else "Unknown",
        "time": parsed_date.strftime("%H:%M") if parsed_date else "Unknown",
    }

def get_body_data(payload):
    if payload.get("body", {}).get("data"):
        return payload["body"]["data"]
    for part in payload.get("parts", []):
        if part["mimeType"] in ["text/plain", "text/html"]:
            return part.get("body", {}).get("data")
        elif part["mimeType"].startswith("multipart/"):
            body = get_body_data(part)
            if body:
                return body

def fetch_messages(service, max_results=5):
    try:
        logger.info(f"Fetching up to {max_results} messages...")

        results = service.users().messages().list(
            userId="me",
            maxResults=max_results
        ).execute()
        messages = results.get("messages", [])
        
        logger.info(f"Fetched {len(messages)} messages")
        return messages

    except HttpError:
        logger.exception("Gmail API error while listing messages")
        raise

def fetch_full_message(service, message_id):
    try:
        logger.debug(f"Fetching full message for ID: {message_id}")

        return service.users().messages().get(
            userId="me",
            id=message_id,
            format="full"
        ).execute()

    except HttpError:
        logger.exception(f"Failed to fetch message ID: {message_id}")
        raise

def decode_body(raw_body):
    if not raw_body:
        logger.warning("No body data found")
        return ""

    try:
        return base64.urlsafe_b64decode(raw_body).decode("utf-8", errors="replace")
    except Exception:
        logger.exception("Failed to decode email body")
        return ""

def parse_message(message):
    logger.debug("Parsing message payload")

    payload = message['payload']
    header_data = get_header(payload['headers'])
    raw_body = get_body_data(payload)
    decoded_body = decode_body(raw_body)

    logger.debug("Message parsed successfully")

    return {
        **header_data,
        "body": decoded_body
    }

def get_emails(max_results=5):
    try:
        logger.info("Starting email retrieval pipeline")

        service = get_service()
        messages = fetch_messages(service, max_results)

        parsed_emails = []

        for msg in messages:
            full_message = fetch_full_message(service, msg["id"])
            parsed = parse_message(full_message)
            parsed_emails.append(parsed)

        logger.info("Email retrieval pipeline completed successfully")
        return parsed_emails

    except Exception:
        logger.exception("Pipeline execution failed")
        return []