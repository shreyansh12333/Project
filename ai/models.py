"""
Pydantic models for structured output
"""

from pydantic import BaseModel, Field
from typing import List


class Slide(BaseModel):
    """Individual slide structure"""
    title: str = Field(description="Slide title - short, impactful heading (max 8 words)")
    content: str = Field(description="Slide content with 3-4 simple bullet points separated by \\n. Each bullet MUST start with • symbol. Each bullet is ONE sentence (15-20 words max). ABSOLUTELY NO sub-bullets, dashes, or nested content. Keep all bullets at the same level. Do NOT repeat the title.")


class Presentation(BaseModel):
    """Complete presentation structure"""
    presentation_title: str = Field(description="Overall presentation title - clear and descriptive")
    slides: List[Slide] = Field(
        description="List of 10-12 slides covering the topic comprehensively. Include: 1-2 introduction slides, 8-9 content slides, and 1 conclusion slide at the end.",
        min_length=5,
        max_length=10
    )