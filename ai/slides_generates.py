"""
slides_generator.py - Improved version ready for Google Slides API
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import JsonOutputParser
from models import Presentation
from prompts import get_slides_prompt
from config import MODEL_NAME, TEMPERATURE, MAX_TOKENS, MIN_SLIDES, MAX_SLIDES
import re
import json


def clean_slide_content(title: str, content: str) -> str:
    """
    Aggressively remove title from content if it appears at the beginning.
    Handles multiple formats and edge cases.
    """
    if not content or not title:
        return content
    
    content = content.strip()
    title_original = title.strip()
    
    # Create multiple variants of the title to check against
    title_variants = [
        title_original,
        title_original.lower(),
        re.sub(r'[*#:\-_\s]+', '', title_original.lower()),  # Remove all formatting
        re.sub(r'[^\w\s]', '', title_original.lower()),  # Keep only alphanumeric
    ]
    
    # Split into lines
    lines = content.split('\n')
    
    # Remove empty lines at start
    while lines and not lines[0].strip():
        lines.pop(0)
    
    if not lines:
        return ""
    
    # Check first line for title match
    first_line = lines[0].strip()
    first_line_variants = [
        first_line,
        first_line.lower(),
        re.sub(r'[*#:\-_\s]+', '', first_line.lower()),
        re.sub(r'[^\w\s]', '', first_line.lower()),
    ]
    
    # If any variant of first line matches any variant of title, remove it
    should_remove = False
    for fv in first_line_variants:
        for tv in title_variants:
            if fv == tv or (fv and tv and fv in tv) or (tv and fv and tv in fv):
                should_remove = True
                break
        if should_remove:
            break
    
    if should_remove:
        lines.pop(0)
        # Remove empty lines after title
        while lines and not lines[0].strip():
            lines.pop(0)
    
    # Rejoin and check if content STILL starts with title as substring
    content_joined = '\n'.join(lines)
    content_lower = content_joined.lower()
    title_clean = re.sub(r'[^\w\s]', '', title_original.lower())
    
    # If content starts with title (ignoring formatting), remove it
    if title_clean and content_lower.startswith(title_clean):
        content_joined = content_joined[len(title_clean):].strip()
        content_joined = content_joined.lstrip(':\n\r\t -•')
    
    # Final cleanup: if first line after all this is STILL very similar to title
    final_lines = content_joined.split('\n')
    if final_lines:
        first_final = re.sub(r'[^\w\s]', '', final_lines[0].lower()).strip()
        title_final = re.sub(r'[^\w\s]', '', title_original.lower()).strip()
        if first_final == title_final:
            final_lines.pop(0)
            while final_lines and not final_lines[0].strip():
                final_lines.pop(0)
            content_joined = '\n'.join(final_lines)
    
    return content_joined.strip()


def validate_and_clean_slides(slides_data: dict, debug: bool = False) -> dict:
    """
    Validate and clean the slides data structure
    
    Returns:
        Clean dict with structure:
        {
            "presentation_title": "...",
            "slides": [{"title": "...", "content": "..."}, ...]
        }
    """
    # Handle different possible structures
    if "slides" in slides_data:
        if isinstance(slides_data["slides"], dict) and "slides" in slides_data["slides"]:
            # Nested structure: {"slides": {"presentation_title": "...", "slides": [...]}}
            presentation_title = slides_data["slides"].get("presentation_title", "Untitled Presentation")
            slides_list = slides_data["slides"]["slides"]
        elif isinstance(slides_data["slides"], list):
            # Flat structure: {"slides": [...], "presentation_title": "..."}
            presentation_title = slides_data.get("presentation_title", "Untitled Presentation")
            slides_list = slides_data["slides"]
        else:
            raise ValueError("Invalid slides structure")
    elif "presentation_title" in slides_data and isinstance(slides_data.get("slides"), list):
        # Direct Presentation model structure
        presentation_title = slides_data["presentation_title"]
        slides_list = slides_data["slides"]
    else:
        raise ValueError("Cannot parse slides data structure")
    
    # Clean each slide
    cleaned_slides = []
    for i, slide in enumerate(slides_list):
        if not isinstance(slide, dict) or "title" not in slide or "content" not in slide:
            if debug:
                print(f"⚠️ Skipping invalid slide {i}: {slide}")
            continue
            
        original_content = slide["content"]
        cleaned_content = clean_slide_content(slide["title"], original_content)
        
        # Debug logging
        if debug and len(cleaned_content) < len(original_content) * 0.8:
            print(f"🧹 Cleaned slide '{slide['title']}': {len(original_content)} -> {len(cleaned_content)} chars")
        
        cleaned_slides.append({
            "title": slide["title"].strip(),
            "content": cleaned_content
        })
    
    return {
        "presentation_title": presentation_title,
        "slides": cleaned_slides
    }


def generate_slides(user_input: str, api_key: str, debug: bool = False) -> dict:
    """
    Main function to generate slides content using Gemini
    
    Args:
        user_input: User's topic/description
        api_key: Google Gemini API key
        debug: Enable debug logging
        
    Returns:
        dict: Clean structured slides data:
        {
            "presentation_title": "Title of Presentation",
            "slides": [
                {"title": "Slide 1 Title", "content": "• Bullet 1\\n• Bullet 2\\n• Bullet 3"},
                {"title": "Slide 2 Title", "content": "• Bullet 1\\n• Bullet 2\\n• Bullet 3"}
            ]
        }
        
    Raises:
        ValueError: If slides generation or parsing fails
        Exception: For API errors
    """
    try:
        if debug:
            print(f"📝 Generating slides for: {user_input}")
            print(f"🤖 Using model: {MODEL_NAME} (temp={TEMPERATURE})")
        
        # Initialize Gemini
        llm = ChatGoogleGenerativeAI(
            model=MODEL_NAME,
            google_api_key=api_key,
            temperature=TEMPERATURE,
            max_output_tokens=MAX_TOKENS
        )

        parser = JsonOutputParser(pydantic_object=Presentation)
        prompt = get_slides_prompt()
        
        # Create chain
        chain = prompt | llm | parser
        
        # Generate content
        result = chain.invoke({
            "user_input": user_input,
            "format_instructions": parser.get_format_instructions(),
            "min_slides": MIN_SLIDES,
            "max_slides": MAX_SLIDES
        })
        
        if debug:
            print("\n" + "="*50)
            print("RAW AI OUTPUT:")
            print(json.dumps(result, indent=2))
            print("="*50 + "\n")
        
        # Validate and clean
        cleaned_data = validate_and_clean_slides(result, debug=debug)
        
        # Validation
        num_slides = len(cleaned_data["slides"])
        if num_slides < MIN_SLIDES or num_slides > MAX_SLIDES:
            print(f"⚠️ Warning: Generated {num_slides} slides (expected {MIN_SLIDES}-{MAX_SLIDES})")
        
        if debug:
            print(f"✅ Successfully generated {num_slides} slides")
            print(f"📊 Presentation: {cleaned_data['presentation_title']}\n")
        
        return cleaned_data
        
    except Exception as e:
        error_msg = f"Failed to generate slides: {str(e)}"
        if debug:
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
        raise Exception(error_msg)
