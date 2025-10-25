"""
prompts.py - Improved prompt for Google Slides generation
"""

from langchain_core.prompts import ChatPromptTemplate

def get_slides_prompt():
    """
    Optimized prompt for Gemini to generate clean, structured slides
    that work perfectly with Google Slides API
    """

    template = """You are a professional presentation content generator. Your output will be used directly with Google Slides API.

TOPIC: "{user_input}"

STRUCTURE REQUIREMENTS:
- Generate between {min_slides} and {max_slides} slides
- Slide 1: Title slide (presentation overview)
- Slides 2 to N-1: Content slides (main topics)
- Last slide: Conclusion/Summary

SLIDE FORMAT (CRITICAL):
Each slide must have:
1. **title**: Clear, concise heading (5-8 words maximum)
2. **content**: Exactly 3-4 bullet points formatted as follows:
   - Start each bullet with • symbol
   - One sentence per bullet (12-15 words)
   - Separate bullets with \\n (newline character)
   - NO sub-bullets, NO dashes, NO nested lists
   - All bullets at the SAME hierarchical level

CONTENT RULES:
✓ Factual and direct - stick to "{user_input}" only
✓ Simple, clear language
✓ Each slide covers ONE main concept
✓ DO NOT repeat the slide title in the content bullets
✓ NO creative storytelling or analogies
✓ NO markdown formatting (**, ##, etc.)

FORBIDDEN:
✗ Do NOT include the title text as the first bullet
✗ Do NOT use sub-bullets or hierarchies
✗ Do NOT use -, →, *, or any symbol except •
✗ Do NOT add extra explanations outside bullets
✗ Do NOT use overly long sentences (keep under 15 words)

CORRECT BULLET FORMAT EXAMPLE:
• Machine learning enables computers to learn from data automatically
• Algorithms improve performance through experience without explicit programming
• Applications include image recognition and natural language processing
• Deep learning is a subset using neural networks

INCORRECT FORMAT (DO NOT DO THIS):
• Machine Learning
  - Subset of AI (WRONG - no sub-bullets)
• Machine Learning: enables computers to learn (WRONG - title repeated)
• This is a very long explanation that goes beyond fifteen words and becomes difficult to read (WRONG - too long)

OUTPUT FORMAT:
{format_instructions}

Return ONLY valid JSON. No additional text, explanations, or formatting outside the JSON structure."""

    return ChatPromptTemplate.from_template(template)