from google import genai
from PIL import Image
from io import BytesIO
import os
from dotenv import load_dotenv
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  # Logger for image_generation.py

load_dotenv()

class ImageModel:
    def __init__(self):
        logger.info("Initializing Gemini image client")
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set for ImageModel.")
        self.client = genai.Client(api_key=api_key)
        logger.info("Initialized Gemini image client successfully")

    def generate_image_for_video(self, prompt: str, dir_name: str, img_name_base: str) -> str:
        """
        Generates an image from a given prompt using Google Gemini's Imagen model
        and saves it to a JPG file.

        Args:
            prompt (str): The detailed prompt for image generation.
            dir_name (str): The directory where the image file should be saved.
            img_name_base (str): The base filename for the generated image (e.g., "scene_1").

        Returns:
            str: The full path to the saved image file.
        """
        full_image_path = os.path.join(dir_name, f"{img_name_base}.jpg")
        
        # Ensure the directory exists
        os.makedirs(dir_name, exist_ok=True)

        try:
            logger.info(f"Generating image for prompt: '{prompt[:50]}...'")  # Log first 50 chars
            
            # Use Gemini's Imagen model for image generation
            response = self.client.models.generate_images(
                model="imagen-3.0-generate-002",
                prompt=prompt,
                config=genai.types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="1:1",
                ),
            )
            
            logger.info("Image generation response received.")
            
            if response.generated_images and len(response.generated_images) > 0:
                generated_image = response.generated_images[0]
                # Save the image from the response
                image = Image.open(BytesIO(generated_image.image.image_bytes))
                image.save(full_image_path)
                logger.info(f"Saved image to {full_image_path}")
                return full_image_path
            else:
                raise ValueError("No image returned by Gemini Imagen API.")

        except Exception as e:
            logger.error(f"Error generating or saving image to {full_image_path}: {str(e)}", exc_info=True)
            self._create_dummy_image(full_image_path)
            return full_image_path

    def _create_dummy_image(self, path: str):
        """Creates a black dummy image if actual image generation fails."""
        try:
            # Create a 1024x1024 black image
            dummy_image = Image.new('RGB', (1024, 1024), color='black')
            dummy_image.save(path)
            logger.warning(f"Created a black dummy image at {path} due to generation failure.")
        except Exception as dummy_e:
            logger.error(f"Failed to create dummy image at {path}: {dummy_e}")

if __name__ == "__main__":
    # Example usage when run directly (for testing)
    image_client = ImageModel()
    test_dir = "test_image_output"
    os.makedirs(test_dir, exist_ok=True)
    try:
        image_client.generate_image_for_video(
            "A futuristic city with flying cars and towering skyscrapers, sunset lighting, vibrant colors, cinematic view, highly detailed, octane render.",
            test_dir,
            "test_scene_image"
        )
    except Exception as e:
        logger.error(f"Test image generation failed: {e}")