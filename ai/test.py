import os
from dotenv import load_dotenv
load_dotenv()

from models  import Presentation
from slides_generates import generate_slides

api_key = os.getenv("GOOGLE_API_KEY")


slides = generate_slides("Hello", api_key)
print(slides)