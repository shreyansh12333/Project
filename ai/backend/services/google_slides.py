"""
Google Slides service for presentation creation
Converts AI-generated content into actual Google Slides
"""

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
from typing import Optional, Dict, Any, List
import sys
import os

# Add AI module to path
sys.path.append('../../ai')
from ai.models import Presentation, Slide

# Scopes for Google Slides
SCOPES = ['https://www.googleapis.com/auth/presentations', 'https://www.googleapis.com/auth/drive']

class GoogleSlidesService:
    def __init__(self):
        self.service = None
        self.creds = None
    
    def authenticate(self, credentials_json: str) -> bool:
        """
        Authenticate with Google Slides API
        
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
            self.service = build('slides', 'v1', credentials=self.creds)
            
            return True
            
        except Exception as e:
            print(f"Authentication failed: {e}")
            return False
    
    def create_presentation(self, title: str) -> Optional[str]:
        """
        Create a new Google Slides presentation
        
        Args:
            title: Title of the presentation
            
        Returns:
            str: Presentation ID if successful
        """
        try:
            presentation = {
                'title': title
            }
            
            presentation_response = self.service.presentations().create(
                body=presentation
            ).execute()
            
            return presentation_response.get('presentationId')
            
        except HttpError as error:
            print(f'An error occurred: {error}')
            return None
    
    def add_slide(self, presentation_id: str, slide_index: int = None) -> Optional[str]:
        """
        Add a new slide to presentation
        
        Args:
            presentation_id: ID of the presentation
            slide_index: Position to insert slide (optional)
            
        Returns:
            str: Slide ID if successful
        """
        try:
            requests = [{
                'createSlide': {
                    'insertionIndex': slide_index,
                    'slideLayoutReference': {
                        'predefinedLayout': 'TITLE_AND_BODY'
                    }
                }
            }]
            
            response = self.service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={'requests': requests}
            ).execute()
            
            # Get the slide ID from response
            slide_id = response.get('replies')[0].get('createSlide').get('objectId')
            return slide_id
            
        except HttpError as error:
            print(f'An error occurred: {error}')
            return None
    
    def update_slide_content(self, presentation_id: str, slide_id: str, title: str, content: str) -> bool:
        """
        Update slide with title and content
        
        Args:
            presentation_id: ID of the presentation
            slide_id: ID of the slide
            title: Slide title
            content: Slide content
            
        Returns:
            bool: True if successful
        """
        try:
            requests = []
            
            # Find text boxes in the slide
            presentation = self.service.presentations().get(
                presentationId=presentation_id
            ).execute()
            
            # Get the slide
            slide = None
            for s in presentation.get('slides', []):
                if s.get('objectId') == slide_id:
                    slide = s
                    break
            
            if not slide:
                return False
            
            # Update title and content
            for element in slide.get('pageElements', []):
                shape = element.get('shape')
                if shape and shape.get('shapeType') == 'TEXT_BOX':
                    placeholder = shape.get('placeholder')
                    if placeholder:
                        placeholder_type = placeholder.get('type')
                        
                        # Update title
                        if placeholder_type == 'TITLE':
                            requests.append({
                                'insertText': {
                                    'objectId': element.get('objectId'),
                                    'text': title
                                }
                            })
                        
                        # Update body content
                        elif placeholder_type == 'BODY':
                            requests.append({
                                'insertText': {
                                    'objectId': element.get('objectId'),
                                    'text': content
                                }
                            })
            
            if requests:
                self.service.presentations().batchUpdate(
                    presentationId=presentation_id,
                    body={'requests': requests}
                ).execute()
                
                return True
            
            return False
            
        except HttpError as error:
            print(f'An error occurred: {error}')
            return False
    
    def add_title_slide(self, presentation_id: str, title: str) -> Optional[str]:
        """
        Add a title slide (first slide with just the title)
        
        Args:
            presentation_id: ID of the presentation
            title: Main title for the presentation
            
        Returns:
            str: Slide ID if successful
        """
        try:
            requests = [{
                'createSlide': {
                    'insertionIndex': 0,
                    'slideLayoutReference': {
                        'predefinedLayout': 'TITLE_ONLY'  # Title-only layout
                    }
                }
            }]
            
            response = self.service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={'requests': requests}
            ).execute()
            
            slide_id = response.get('replies')[0].get('createSlide').get('objectId')
            
            # Add the title text
            title_requests = [{
                'insertText': {
                    'objectId': slide_id,
                    'text': title
                }
            }]
            
            self.service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={'requests': title_requests}
            ).execute()
            
            return slide_id
            
        except HttpError as error:
            print(f'An error occurred: {error}')
            return None

    def create_presentation_from_ai(self, presentation_data: Presentation) -> Optional[Dict[str, Any]]:
        """
        Create a complete Google Slides presentation from AI-generated data
        Structure: Title slide + Content slides with subtopics and bullet points
        
        Args:
            presentation_data: Pydantic model with presentation data
            
        Returns:
            dict: Presentation info with ID and URL
        """
        try:
            # Create the presentation
            presentation_id = self.create_presentation(presentation_data.presentation_title)
            if not presentation_id:
                return None
            
            # Get the presentation to work with the default slide
            presentation = self.service.presentations().get(
                presentationId=presentation_id
            ).execute()
            
            default_slides = presentation.get('slides', [])
            if default_slides:
                default_slide_id = default_slides[0].get('objectId')
                
                # Step 1: Create title slide (first slide)
                title_slide_id = self.add_title_slide(presentation_id, presentation_data.presentation_title)
                
                # Step 2: Add content slides for each AI-generated slide
                content_slide_ids = []
                for i, slide_data in enumerate(presentation_data.slides):
                    slide_id = self.add_slide(presentation_id, i + 2)  # Start after title slide
                    if slide_id:
                        content_slide_ids.append((slide_id, slide_data))
                
                # Step 3: Update content for each slide (subtopic + bullet points)
                for slide_id, slide_data in content_slide_ids:
                    self.update_slide_content(
                        presentation_id, 
                        slide_id, 
                        slide_data.title,  # This becomes the subtopic
                        slide_data.content  # This contains the bullet points
                    )
                
                # Step 4: Remove the original default empty slide
                requests = [{
                    'deleteObject': {
                        'objectId': default_slide_id
                    }
                }]
                
                self.service.presentations().batchUpdate(
                    presentationId=presentation_id,
                    body={'requests': requests}
                ).execute()
            
            # Calculate total slides (title + content slides)
            total_slides = 1 + len(presentation_data.slides)
            
            # Get the final presentation URL
            presentation_url = f"https://docs.google.com/presentation/d/{presentation_id}/edit"
            
            return {
                'presentation_id': presentation_id,
                'presentation_url': presentation_url,
                'title': presentation_data.presentation_title,
                'slide_count': total_slides,
                'structure': {
                    'title_slide': presentation_data.presentation_title,
                    'content_slides': [slide.title for slide in presentation_data.slides]
                }
            }
            
        except HttpError as error:
            print(f'An error occurred: {error}')
            return None
    
    def get_presentation_info(self, presentation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a presentation
        
        Args:
            presentation_id: ID of the presentation
            
        Returns:
            dict: Presentation information
        """
        try:
            presentation = self.service.presentations().get(
                presentationId=presentation_id
            ).execute()
            
            return {
                'id': presentation.get('presentationId'),
                'title': presentation.get('title'),
                'slide_count': len(presentation.get('slides', [])),
                'url': f"https://docs.google.com/presentation/d/{presentation_id}/edit"
            }
            
        except HttpError as error:
            print(f'An error occurred: {error}')
            return None