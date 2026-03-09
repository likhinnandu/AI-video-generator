import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory, render_template, send_file
from flask_cors import CORS
import webbrowser
from threading import Timer

# --- Import your core logic modules ---
from story_generation import StoryGenerator
from audio_generation import AudioModel
from image_generation import ImageModel
from video_synchronization import generate_video

# --- Configuration and Initialization ---
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

GENERATED_VIDEOS_DIR = "generated_videos"
os.makedirs(GENERATED_VIDEOS_DIR, exist_ok=True)

# --- Initialize AI Clients ---
story_generator_client = None
image_client = None
audio_client = None

try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY is not set. Video generation will fail until it is provided in the .env file.")
    else:
        story_generator_client = StoryGenerator(api_key=api_key)
        image_client = ImageModel()
        audio_client = AudioModel()
        logger.info("Initialized Video Script Generator, Audio, and Image clients successfully.")
except Exception as e:
    logger.error(f"Failed to initialize AI models during startup (Ensure your API keys are valid): {e}")

# --- Frontend Serving Routes ---
@app.route("/", methods=["GET"])
def serve_frontend():
    return render_template("index.html")

@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory("static", filename)

# --- Helper to parse clean error messages ---
def _get_friendly_error(error: Exception) -> str:
    """Extract a user-friendly error message from API exceptions."""
    error_str = str(error)
    if "RESOURCE_EXHAUSTED" in error_str or "429" in error_str:
        return ("API quota exceeded. Your Gemini API key has reached its free-tier limit. "
                "Please wait for the quota to reset, or upgrade your plan at https://ai.google.dev/")
    if "INVALID_API_KEY" in error_str or "API_KEY_INVALID" in error_str or "401" in error_str:
        return ("Invalid API key. Please check your GEMINI_API_KEY in the .env file "
                "and ensure it is a valid Google Gemini API key.")
    if "PERMISSION_DENIED" in error_str or "403" in error_str:
        return ("Permission denied. Your API key may not have access to the requested model. "
                "Please check your Google Cloud project permissions.")
    if "quota" in error_str.lower():
        return ("API quota limit reached. Please wait and try again later, "
                "or check your usage at https://ai.google.dev/")
    return f"An error occurred: {error_str}"

# --- API Endpoint for Video Generation ---
@app.route('/generate-video', methods=['POST'])
def generate_video_endpoint():
    try:
        # Check if AI clients are initialized
        if not story_generator_client or not image_client or not audio_client:
            return jsonify({
                "error": "AI services are not initialized. Please set your GEMINI_API_KEY in the .env file and restart the server."
            }), 503

        data = request.get_json()
        prompt = data.get("prompt")
        try:
            scenes = int(data.get("scenes", 4))
        except ValueError:
            return jsonify({"error": "Number of scenes must be an integer."}), 400

        style = data.get("style", "dramatic")
        format_type = data.get("format_type", "structured")

        if not prompt:
            return jsonify({"error": "Video prompt is required."}), 400
        if not isinstance(scenes, int) or scenes <= 0 or scenes > 10:
            return jsonify({"error": "Number of scenes must be a positive integer, up to 10."}), 400

        logger.info(f"Received request: Prompt='{prompt}', Scenes={scenes}, Style='{style}', Format='{format_type}'")

        # --- Step 1: Generate Video Script ---
        logger.info("Step 1/4: Generating video script...")
        story = {}
        try:
            if format_type.lower() == "legacy":
                story = story_generator_client.generate_story_legacy_format(prompt, scenes)
            else:
                story_response_obj = story_generator_client.generate_story(prompt, scenes, style)
                story = story_response_obj.dict()
        except Exception as e:
            logger.error(f"Video script generation failed: {e}", exc_info=True)
            return jsonify({"error": f"Video script generation failed: {_get_friendly_error(e)}"}), 500

        story_title = story.get("title", "Untitled Video")
        safe_title = "".join(c for c in story_title if c.isalnum()).strip() or "Untitled_Video"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dir_name = f"{safe_title}_{timestamp}"
        output_dir = os.path.join(GENERATED_VIDEOS_DIR, dir_name)
        os.makedirs(output_dir, exist_ok=True)

        with open(os.path.join(output_dir, "story_data.json"), "w") as f:
            json.dump(story, f, indent=2)

        scenes_data_list = (
            [v for k, v in story.get("response", {}).items() if k.startswith("scene")]
            if format_type.lower() == "legacy"
            else story.get("scenes", [])
        )

        # --- Step 2: Generate Audio ---
        logger.info("Step 2/4: Generating audio...")
        processed_scene_nums = []
        for i, scene in enumerate(scenes_data_list):
            scene_num = i + 1
            narration = None
            image_prompt = None

            if format_type.lower() == "legacy":
                narration = scene.get('narration')
                image_prompt = scene.get('image_prompt')
            elif 'media' in scene:
                narration = scene['media'].get('audio_narration')
                image_prompt = scene['media'].get('image_prompt')

            if narration:
                try:
                    audio_client.generate_audio_for_video(narration, output_dir, f"scene_{scene_num}.mp3")
                    processed_scene_nums.append(scene_num)
                    logger.info(f"Audio generated for scene {scene_num}")
                except Exception as e:
                    logger.error(f"Audio generation failed for scene {scene_num}: {e}")

            # --- Step 3: Generate Images ---
            if image_prompt:
                try:
                    logger.info(f"Step 3/4: Generating image for scene {scene_num}...")
                    image_client.generate_image_for_video(image_prompt, output_dir, f"scene_{scene_num}")
                    if scene_num not in processed_scene_nums:
                        processed_scene_nums.append(scene_num)
                    logger.info(f"Image generated for scene {scene_num}")
                except Exception as e:
                    logger.error(f"Image generation failed for scene {scene_num}: {_get_friendly_error(e)}")

        if not processed_scene_nums:
            return jsonify({"error": "No assets could be generated. Please check your API key and quota."}), 500

        # --- Step 4: Generate Video ---
        logger.info("Step 4/4: Synchronizing video...")
        video_output_file_name = f"{dir_name}.mp4"
        generate_video(output_dir, processed_scene_nums, video_output_file_name)
        final_video_path = os.path.join(output_dir, video_output_file_name)

        if not os.path.exists(final_video_path):
            return jsonify({"error": "Video file was not created. Please check server logs for details."}), 500

        video_download_url = f"/download-video/{dir_name}/{video_output_file_name}"
        video_stream_url = f"/stream-video/{dir_name}/{video_output_file_name}"

        logger.info(f"Video generated successfully: {final_video_path}")
        return jsonify({
            "message": "Video generated successfully!",
            "video_path": final_video_path,
            "video_download_url": video_download_url,
            "video_stream_url": video_stream_url,
            "title": story_title
        }), 200

    except Exception as e:
        logger.error(f"Error during video generation: {str(e)}", exc_info=True)
        return jsonify({"error": _get_friendly_error(e)}), 500

# --- Download and Stream Routes ---
@app.route("/download-video/<project>/<filename>", methods=["GET"])
def download_video(project, filename):
    try:
        video_dir = os.path.join(GENERATED_VIDEOS_DIR, project)
        return send_from_directory(video_dir, filename, as_attachment=True)
    except Exception as e:
        logger.error(f"Error downloading video: {e}")
        return "Video not found", 404

@app.route("/stream-video/<project>/<filename>", methods=["GET"])
def stream_video(project, filename):
    try:
        video_path = os.path.join(GENERATED_VIDEOS_DIR, project, filename)
        return send_file(video_path, mimetype="video/mp4")
    except Exception as e:
        logger.error(f"Error streaming video: {e}")
        return "Video not found", 404

# --- Launch App and Browser ---
def open_browser():
    webbrowser.open_new_tab("http://127.0.0.1:5000/")

if __name__ == "__main__":
    Timer(1.5, open_browser).start()
    app.run(debug=True, use_reloader=False)
