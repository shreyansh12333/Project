"""
Google Drive service for file management
Handles authentication and file operations
"""

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
import json
from typing import Optional, Dict, Any

# Scopes for Google Drive and Slides
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/presentations'
]

class GoogleDriveService:
    def __init__(self):
        self.service = None
        self.creds = None
    
    def authenticate(self, credentials_json: str) -> bool:
        """
        Authenticate with Google APIs using service account or OAuth
        
        Args:
            credentials_json: JSON string of credentials
            
        Returns:
            bool: True if authentication successful
        """
        try:
            # Parse credentials
            creds_data = json.loads(credentials_json)
            
            # Create credentials object
            self.creds = Credentials.from_authorized_user_info(creds_data, SCOPES)
            
            # Build the service
            self.service = build('drive', 'v3', credentials=self.creds)
            
            return True
            
        except Exception as e:
            print(f"Authentication failed: {e}")
            return False
    
    def create_folder(self, folder_name: str, parent_folder_id: Optional[str] = None) -> Optional[str]:
        """
        Create a folder in Google Drive
        
        Args:
            folder_name: Name of the folder
            parent_folder_id: ID of parent folder (optional)
            
        Returns:
            str: Folder ID if successful, None otherwise
        """
        try:
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_folder_id:
                folder_metadata['parents'] = [parent_folder_id]
            
            folder = self.service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            
            return folder.get('id')
            
        except HttpError as error:
            print(f'An error occurred: {error}')
            return None
    
    def list_files(self, folder_id: Optional[str] = None, mime_type: Optional[str] = None) -> list:
        """
        List files in Google Drive
        
        Args:
            folder_id: ID of folder to search in (optional)
            mime_type: Filter by MIME type (optional)
            
        Returns:
            list: List of files
        """
        try:
            query_parts = []
            
            if folder_id:
                query_parts.append(f"'{folder_id}' in parents")
            
            if mime_type:
                query_parts.append(f"mimeType='{mime_type}'")
            
            query = " and ".join(query_parts) if query_parts else None
            
            results = self.service.files().list(
                q=query,
                pageSize=100,
                fields="nextPageToken, files(id, name, mimeType, createdTime)"
            ).execute()
            
            return results.get('files', [])
            
        except HttpError as error:
            print(f'An error occurred: {error}')
            return []
    
    def delete_file(self, file_id: str) -> bool:
        """
        Delete a file from Google Drive
        
        Args:
            file_id: ID of file to delete
            
        Returns:
            bool: True if successful
        """
        try:
            self.service.files().delete(fileId=file_id).execute()
            return True
            
        except HttpError as error:
            print(f'An error occurred: {error}')
            return False
    
    def share_file(self, file_id: str, email: str, role: str = 'reader') -> bool:
        """
        Share a file with someone
        
        Args:
            file_id: ID of file to share
            email: Email address to share with
            role: Permission role (reader, writer, owner)
            
        Returns:
            bool: True if successful
        """
        try:
            permission = {
                'type': 'user',
                'role': role,
                'emailAddress': email
            }
            
            self.service.permissions().create(
                fileId=file_id,
                body=permission
            ).execute()
            
            return True
            
        except HttpError as error:
            print(f'An error occurred: {error}')
            return False
    
    def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a file
        
        Args:
            file_id: ID of the file
            
        Returns:
            dict: File information
        """
        try:
            file_info = self.service.files().get(
                fileId=file_id,
                fields='id, name, mimeType, size, createdTime, modifiedTime, webViewLink'
            ).execute()
            
            return file_info
            
        except HttpError as error:
            print(f'An error occurred: {error}')
            return None