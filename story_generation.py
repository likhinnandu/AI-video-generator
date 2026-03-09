import os
import json
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from dotenv import load_dotenv
from google import genai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

class MediaElement(BaseModel):
    """Class for defining multimedia elements of a scene"""
    image_prompt: str = Field(
        description="Detailed prompt for image generation that captures the essence of the scene"
    )
    audio_narration: str = Field(
        description="Text for text-to-speech narration that conveys the emotional tone of the scene"
    )
    background_music: str = Field(
        default="ambient",
        description="Type of background music for the scene (e.g., suspenseful, cheerful, melancholic)"
    )
    duration_seconds: float = Field(
        default=5.0,
        description="Suggested duration of this scene in seconds"
    )

class Scene(BaseModel):
    """Class for defining a scene in the video"""
    title: str = Field(
        description="Short descriptive title for the scene"
    )
    description: str = Field(
        description="Detailed description of what happens in the scene"
    )
    media: MediaElement = Field(
        description="Multimedia elements for the scene"
    )
    transition: str = Field(
        default="cut",
        description="Transition to the next scene (e.g., fade, dissolve, cut)"
    )

class StoryResponse(BaseModel):
    """Response model for generated video"""
    title: str = Field(description="Title of the video")
    theme: str = Field(description="Central theme of the video")
    scenes: List[Scene] = Field(description="List of scenes that compose the video")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the generated video"
    )

class StoryGenerator:
    """Generates structured video scripts for automatic video creation using Google Gemini"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the StoryGenerator with Gemini API key for video script generation"""
        self._initialize_llm(api_key)
        
    def _initialize_llm(self, api_key: Optional[str] = None):
        """Initialize the Google Gemini client"""
        try:
            # Use provided API key or get from environment
            if not api_key:
                api_key = os.getenv("GEMINI_API_KEY")
                
            if not api_key:
                raise ValueError("No Gemini API key provided. Set GEMINI_API_KEY environment variable or pass api_key to constructor.")
                
            # Initialize Google Gemini client
            self.client = genai.Client(api_key=api_key)
            self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
            logger.info(f"Gemini LLM initialized successfully with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Error initializing Gemini LLM: {str(e)}")
            raise
            
    def _create_system_prompt(self) -> str:
        """Create the system prompt for video script generation"""
        return """You are a creative storyteller and expert screenwriter specializing in creating engaging, visually compelling videos.

Your task is to generate a structured video script that can be converted into a video sequence. Each video should be divided into distinct scenes that flow naturally together to tell a cohesive narrative.

For each scene, provide:
1. A title that captures the essence of the scene
2. A detailed description of what happens
3. Multimedia elements:
    - Image prompt: VERY detailed visual description for image generation with style, lighting, mood, colors, and details with proper synchronization with the audio narration. The image for the next scene should visually represent a continuation of the video.
    - Audio narration: Engaging narrative text for voice-over that advances the video and conveys emotion.
    - Background music suggestion
    - Suggested duration in seconds
4. Transition to the next scene

Important requirements:
- Each scene's audio narration should continue the narrative from the previous scene.
- Audio narration should sound like a professional narrator.
- Image prompts should be extremely detailed for high-quality generation, including specific visual elements, composition, and artistic style.
- The video should have a clear beginning, middle, and end.
- The whole video when read through all scenes should feel cohesive and complete.
- Ensure the image prompts for consecutive scenes depict a logical progression of the video's visuals.

YOU MUST RESPOND WITH VALID JSON ONLY. Do not include any markdown formatting, code fences, or extra text.
The JSON must follow this exact structure:
{
    "title": "Title of the video",
    "theme": "Central theme",
    "scenes": [
        {
            "title": "Scene title",
            "description": "Scene description",
            "media": {
                "image_prompt": "Detailed image generation prompt",
                "audio_narration": "Narration text for voice-over",
                "background_music": "Music type",
                "duration_seconds": 5.0
            },
            "transition": "fade"
        }
    ]
}
"""

    def generate_story(self, prompt: str, num_scenes: int = 5, style: Optional[str] = None) -> StoryResponse:
        """
        Generate a structured video script based on the input prompt using Google Gemini
        
        Args:
            prompt: The user's video prompt or request
            num_scenes: Suggested number of scenes (default: 5)
            style: Optional style guidance (e.g., "dramatic", "comedic")
            
        Returns:
            StoryResponse object containing the structured video script
        """
        try:
            logger.info(f"Generating video script for prompt: {prompt}")
            
            # Prepare the user prompt
            user_prompt = f"Create a video script with approximately {num_scenes} scenes based on the following prompt: {prompt}"
            if style:
                user_prompt += f"\nThe video should be in a {style} style."
                
            user_prompt += "\n\nMake sure each scene flows naturally from the previous one, with audio narration that continues the narrative and image prompts that are extremely detailed for high-quality generation."
            user_prompt += "\n\nRespond ONLY with valid JSON. No markdown, no code fences, no extra text."
                
            # Call the Gemini API
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=genai.types.GenerateContentConfig(
                    system_instruction=self._create_system_prompt(),
                    temperature=0.7,
                    max_output_tokens=3000,
                ),
            )
            
            # Extract and parse the response text
            response_text = response.text.strip()
            
            # Clean up response - remove markdown code fences if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            elif response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            result = json.loads(response_text)
            
            # Add metadata
            if "metadata" not in result:
                result["metadata"] = {}
                
            result["metadata"]["generation_timestamp"] = datetime.now().isoformat()
            result["metadata"]["prompt"] = prompt
            result["metadata"]["model"] = self.model_name
            
            # Convert to Pydantic model for validation
            story_response = StoryResponse(**result)
            logger.info(f"Successfully generated video script '{story_response.title}' with {len(story_response.scenes)} scenes")
            
            return story_response
                
        except Exception as e:
            logger.error(f"Error generating video script: {str(e)}", exc_info=True)
            raise

    def generate_story_legacy_format(self, message: str, num_scenes: int = 5) -> Dict[str, Any]:
        """
        Generate a video script in the legacy format as per the provided template
        
        Args:
            message: The user's video prompt or request
            num_scenes: Suggested number of scenes
            
        Returns:
            Dictionary in the legacy format with scenes
        """
        try:
            # First generate structured video script
            story_response = self.generate_story(message, num_scenes)
            
            # Convert to legacy format
            legacy_format = {"response": {}}
            legacy_format["title"] = story_response.title
            legacy_format["theme"] = story_response.theme
            for i, scene in enumerate(story_response.scenes, 1):
                scene_key = f"scene{i}"
                legacy_format["response"][scene_key] = {
                    "title": scene.title,
                    "description": scene.description,
                    "narration": scene.media.audio_narration,
                    "image_prompt": scene.media.image_prompt,
                    "background_music": scene.media.background_music,
                    "duration_seconds": scene.media.duration_seconds
                }
            
            logger.info("Successfully converted video script to legacy format.")
            return legacy_format
            
        except Exception as e:
            logger.error(f"Error generating video script in legacy format: {str(e)}", exc_info=True)
            raise