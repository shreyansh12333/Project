import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from pydantic import BaseModel


sys.path.insert(0, str(Path(__file__).parent.parent))
from slides_generates import generate_slides

load_dotenv()

app = FastAPI()
api_key = os.getenv("GOOGLE_API_KEY")

class SlideRequest(BaseModel):
    topic: str
    access_token: str

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],  
)

@app.get("/")
async def root():
    return {"message": "Welcome to the presentation generator API!"}




@app.post("/generate-presentation")
async def create_presentation(data: SlideRequest):
    """
    Generate AI-powered presentation and create it in user's Google Drive
    
    Args:
        data: SlideRequest containing topic and access_token
        
    Returns:
        Response with presentation_id, presentation_url, presentation_title, total_slides
    """
    try:
        # Validate input
        if not data.topic or len(data.topic.strip()) == 0:
            raise HTTPException(
                status_code=400,
                detail="Topic cannot be empty"
            )
        
        if not data.access_token:
            raise HTTPException(
                status_code=401,
                detail="Access token is required"
            )
        
        print(f"📝 Request received for topic: {data.topic}")
        
        # Step 1: Generate slides content using Gemini
        gemini_api_key = os.getenv("GOOGLE_API_KEY")
        if not gemini_api_key:
            raise HTTPException(
                status_code=500,
                detail="Server configuration error: Gemini API key not found"
            )
        
        print("🤖 Generating slides content with Gemini...")
        slides_data = generate_slides(
            user_input=data.topic,
            api_key=gemini_api_key,
            debug=True
        )

        creds = Credentials(token=data.access_token)
        slides_service = build('slides', 'v1', credentials=creds)
        
        presentation_title = slides_data['presentation_title']
        slides_list = slides_data['slides']
        presentation_body = {
            'title': presentation_title
        }
        
        presentation = slides_service.presentations().create(
            body=presentation_body
        ).execute()
        
        presentation_id = presentation['presentationId']
        print(f"✅ Created presentation: {presentation_id}")

        presentation_details = slides_service.presentations().get(
            presentationId=presentation_id
        ).execute()
        
        slides = presentation_details.get('slides', [])
        requests = []
    
        if slides:
            requests.append({
                'deleteObject': {
                    'objectId': slides[0]['objectId']
                }
            })
        for i, slide_data in enumerate(slides_list):
            slide_id = f'slide_{i}'
            title_id = f'title_{i}'
            body_id = f'body_{i}'
            
            requests.append({
                'createSlide': {
                    'objectId': slide_id,
                    'slideLayoutReference': {
                        'predefinedLayout': 'TITLE_AND_BODY'
                    },
                    'placeholderIdMappings': [
                        {
                            'layoutPlaceholder': {
                                'type': 'TITLE'
                            },
                            'objectId': title_id
                        },
                        {
                            'layoutPlaceholder': {
                                'type': 'BODY'
                            },
                            'objectId': body_id
                        }
                    ]
                }
            })
        
            requests.append({
                'insertText': {
                    'objectId': title_id,
                    'text': slide_data['title']
                }
            })
            
            
            title_colors = [
                {'red': 0.2, 'green': 0.4, 'blue': 0.8}, 
                {'red': 0.8, 'green': 0.2, 'blue': 0.4}, 
                {'red': 0.4, 'green': 0.7, 'blue': 0.3},  
                {'red': 0.9, 'green': 0.5, 'blue': 0.2}, 
                {'red': 0.6, 'green': 0.3, 'blue': 0.8},  
                {'red': 0.2, 'green': 0.7, 'blue': 0.7},  
                {'red': 0.9, 'green': 0.3, 'blue': 0.5},  
                {'red': 0.3, 'green': 0.6, 'blue': 0.9},  
            ]
            
            color = title_colors[i % len(title_colors)]
            
            requests.append({
                'updateTextStyle': {
                    'objectId': title_id,
                    'style': {
                        'foregroundColor': {
                            'opaqueColor': {
                                'rgbColor': color
                            }
                        },
                        'bold': True,
                        'fontSize': {
                            'magnitude': 28,
                            'unit': 'PT'
                        }
                    },
                    'fields': 'foregroundColor,bold,fontSize'
                }
            })
            
            clean_content = slide_data['content'].replace('•', '').strip()
            
            requests.append({
                'insertText': {
                    'objectId': body_id,
                    'text': clean_content
                }
            })
            
            requests.append({
                'updateTextStyle': {
                    'objectId': body_id,
                    'style': {
                        'fontSize': {
                            'magnitude': 16,
                            'unit': 'PT'
                        },
                        'foregroundColor': {
                            'opaqueColor': {
                                'rgbColor': {
                                    'red': 0.2,
                                    'green': 0.2,
                                    'blue': 0.2
                                }
                            }
                        }
                    },
                    'fields': 'fontSize,foregroundColor'
                }
            })
            
        
            bullets_list = [line.strip() for line in clean_content.split('\n') if line.strip()]
            current_index = 0
            
            for bullet_text in bullets_list:
                requests.append({
                    'createParagraphBullets': {
                        'objectId': body_id,
                        'textRange': {
                            'type': 'FIXED_RANGE',
                            'startIndex': current_index,
                            'endIndex': current_index + len(bullet_text)
                        },
                        'bulletPreset': 'BULLET_DISC_CIRCLE_SQUARE'
                    }
                })
                current_index += len(bullet_text) + 1  
        

        if requests:
            body = {'requests': requests}
            response = slides_service.presentations().batchUpdate(
                presentationId=presentation_id,
                body=body
            ).execute()
            
            print(f"✅ Added {len(slides_list)} slides to presentation")
            print(f"📋 Google API Response: {response}")
        
        presentation_url = f"https://docs.google.com/presentation/d/{presentation_id}/edit"
        
        print(f"✅ Presentation created successfully!")
        print(f"🔗 URL: {presentation_url}")
        
        return {
            "success": True,
            "presentation_id": presentation_id,
            "url": presentation_url,
            "presentation_title": presentation_title,
            "total_slides": len(slides_list),
            "google_response": response if requests else None  
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in create_presentation: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate presentation: {str(e)}"
        )