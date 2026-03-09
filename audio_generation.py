from gtts import gTTS
from dotenv import load_dotenv
import os
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  # Logger for audio_generation.py

class AudioModel:
    def __init__(self):
        logger.info("Initializing Google TTS (gTTS) audio client")
        # gTTS doesn't require an API key - it uses Google Translate's TTS service
        logger.info("Initialized Google TTS audio client successfully")

    def generate_audio_for_video(self, prompt: str, dir_name: str, audio_name: str) -> str:
        """
        Generates audio from a given text using Google TTS (gTTS) and saves it to a file.

        Args:
            prompt (str): The text to convert to speech.
            dir_name (str): The directory where the audio file should be saved.
            audio_name (str): The filename for the generated audio (e.g., "scene_1.mp3").

        Returns:
            str: The full path to the saved audio file.
        """
        full_audio_path = os.path.join(dir_name, audio_name)
        
        # Ensure the directory exists
        os.makedirs(dir_name, exist_ok=True)

        try:
            logger.info(f"Generating audio for: '{prompt[:50]}...'")  # Log first 50 chars
            
            # Use gTTS for text-to-speech
            tts = gTTS(text=prompt, lang='en', slow=False)
            tts.save(full_audio_path)
            
            logger.info(f"Saved audio to {full_audio_path}")
            return full_audio_path
        except Exception as e:
            logger.error(f"Error generating or saving audio to {full_audio_path}: {str(e)}", exc_info=True)
            # Create a dummy silent audio file to prevent video generation from crashing
            try:
                # Create a minimal silent MP3 as fallback
                # A simple approach: generate a very short TTS as placeholder
                fallback_tts = gTTS(text="...", lang='en', slow=False)
                fallback_tts.save(full_audio_path)
                logger.warning(f"Created a fallback audio file at {full_audio_path} due to error.")
                return full_audio_path
            except Exception as dummy_e:
                logger.error(f"Failed to create fallback audio file: {dummy_e}")
                raise  # Re-raise original error if fallback creation also fails

if __name__ == "__main__":
    # Example usage when run directly (for testing)
    audio_client = AudioModel()
    test_dir = "test_audio_output"
    os.makedirs(test_dir, exist_ok=True)
    try:
        audio_client.generate_audio_for_video(
            "This is a test narration for the audio generation module.",
            test_dir,
            "test_scene_audio.mp3"
        )
    except Exception as e:
        logger.error(f"Test audio generation failed: {e}")