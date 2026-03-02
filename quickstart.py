import os.path
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

def get_body(payload):
    if payload.get("body", {}).get("data"):
        return payload["body"]["data"]
    for part in payload.get("parts", []):
        if part["mimeType"] in ["text/plain", "text/html"]:
            return part.get("body", {}).get("data")
        elif part["mimeType"].startswith("multipart/"):
            body = get_body(part)
            if body:
                return body

def get_header_data(headers):
    sep = " "
    for header in headers:
        if header["name"] == "Date":
            header_date = header["value"].split(' ')
            date = sep.join(header_date[1:4])
            time = header_date[-2]
        if header["name"] == "From":
            sender_data = header["value"].split(' ')
            sender_name = sep.join(sender_data[:-1])
            sender_email = sender_data[-1][1:-1]

    print(f"Sender Name: {sender_name}\nSender Email: {sender_email}\nData: {date}\nTime: {time}")

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
        results = service.users().messages().list(userId="me").execute()
        mail_id = results["messages"][1]["id"]
        message = service.users().messages().get(userId="me", id=mail_id, format="full").execute()

        payload = message["payload"]
        get_header_data(payload["headers"])

        body_data = None
        body_data = get_body(payload=payload)
        if body_data is not None:
            decoded_body = base64.urlsafe_b64decode(body_data).decode("utf-8")
            print(decoded_body)

            
            with open("temp.txt", "w") as f:
                f.write(decoded_body)

    except HttpError as error:
        print(f"An error occured: {error}")
    
if __name__ == "__main__":
    main()