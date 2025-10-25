from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

def get_slides_service(access_token: str):
    """
    Returns a Google Slides API service object using the provided access token.
    """
    creds = Credentials(token=access_token)
    service = build("slides", "v1", credentials=creds)
    return service