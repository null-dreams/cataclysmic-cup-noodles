import os.path
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

def main():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("gmail", "v1", credentials=creds)
        results = service.users().messages().list(userId="me", maxResults=2).execute()
        mail_id = results["messages"][0]["id"]
        message = service.users().messages().get(userId="me", id=mail_id, format="full").execute()

        payload = message["payload"]
        parts = payload.get("parts", [])
        body_data = None

        if parts:
            for part in parts:
                if part["mimeType"] == "text/plain":
                    body_data = part["body"]["data"]
                    break
        else:
            body_data = payload["body"].get("data")

        decoded_body = base64.urlsafe_b64decode(body_data).decode("utf-8")
        print(decoded_body)
    except HttpError as error:
        print(f"An error occured: {error}")
    
if __name__ == "__main__":
    main()