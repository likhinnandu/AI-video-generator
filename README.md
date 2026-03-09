# Automated Video Generator

An AI-powered web application that transforms simple text prompts into fully produced videos — complete with AI-generated scripts, images, narration, and synchronized video output.

---

## 📌 Problem Statement

Creating video content traditionally requires significant time, effort, and expertise in scripting, image sourcing, voiceover recording, and video editing. This creates a high barrier for individuals, educators, and small content creators who need quick, professional-quality video content but lack the tools or skills.

**The Automated Video Generator solves this by:**
- Eliminating the need for manual scripting — the AI generates a structured, scene-by-scene video script from a single text prompt.
- Removing the dependency on stock images or manual illustrations — the AI generates unique, context-aware images for each scene.
- Automating narration — text-to-speech converts each scene's script into natural-sounding audio.
- Handling video assembly — images and audio are automatically synchronized and compiled into a final `.mp4` video ready for download.

**In short:** One prompt in → One complete video out.

---

## 🏗️ Architecture

The application follows a **modular pipeline architecture** where each stage of video creation is handled by an independent module, orchestrated by a central Flask application.

```
┌─────────────────────────────────────────────────────────────┐
│                        USER (Browser)                       │
│                   http://127.0.0.1:5000/                    │
└───────────────────────────┬─────────────────────────────────┘
                            │  Prompt + Settings
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     Flask Web Server                        │
│                        (app.py)                             │
│  • Serves frontend (HTML/CSS/JS)                            │
│  • Receives POST requests to /generate-video                │
│  • Orchestrates the 4-step pipeline                         │
│  • Returns video stream/download URLs                       │
└────┬──────────────┬──────────────┬──────────────┬───────────┘
     │              │              │              │
     ▼              ▼              ▼              ▼
┌──────────┐ ┌───────────┐ ┌───────────┐ ┌────────────────┐
│  Step 1  │ │  Step 2   │ │  Step 3   │ │    Step 4      │
│  Script  │ │  Audio    │ │  Image    │ │    Video       │
│Generator │ │ Generator │ │ Generator │ │ Synchronizer   │
│          │ │           │ │           │ │                │
│ Gemini   │ │  Google   │ │  Gemini   │ │   MoviePy +    │
│ 2.0 Flash│ │   TTS     │ │  Imagen 3 │ │   FFmpeg       │
└──────────┘ └───────────┘ └───────────┘ └────────────────┘
     │              │              │              │
     ▼              ▼              ▼              ▼
  story_data     scene_X.mp3   scene_X.jpg    final_video
    .json                                       .mp4
```

### Pipeline Flow

| Step | Module                    | API / Library         | Description                                                  |
|------|---------------------------|-----------------------|--------------------------------------------------------------|
| 1    | `story_generation.py`     | Google Gemini 2.0 Flash | Generates a structured JSON video script with scenes, image prompts, and narration text |
| 2    | `audio_generation.py`     | Google TTS (gTTS)     | Converts each scene's narration text into `.mp3` audio files |
| 3    | `image_generation.py`     | Gemini Imagen 3       | Generates a unique image for each scene from detailed prompts |
| 4    | `video_synchronization.py`| MoviePy + FFmpeg      | Combines images and audio into a synchronized `.mp4` video   |

### Technology Stack

| Layer     | Technology                          |
|-----------|-------------------------------------|
| Frontend  | HTML5, CSS3 (Glassmorphism UI), JavaScript |
| Backend   | Python 3.9+, Flask, Flask-CORS      |
| AI Models | Google Gemini 2.0 Flash (text), Gemini Imagen 3 (images) |
| Audio     | gTTS (Google Text-to-Speech)        |
| Video     | MoviePy, FFmpeg                     |
| Config    | python-dotenv (`.env` file)         |

---

## 📁 Project Structure

```
Automated-Video-Generator/
│
├── app.py                          # Main Flask application — routes, orchestration, error handling
├── story_generation.py             # Video script generation using Google Gemini API
├── image_generation.py             # Image generation using Gemini Imagen 3
├── audio_generation.py             # Text-to-Speech audio generation using gTTS
├── video_synchronization.py        # Combines images + audio into final video using MoviePy
│
├── templates/
│   └── index.html                  # Frontend HTML (main UI page)
│
├── static/
│   ├── css/
│   │   └── style.css               # Stylesheet (dark theme, glassmorphism, animations)
│   └── js/
│       └── main.js                 # Frontend JavaScript (form handling, API calls, UI updates)
│
├── generated_videos/               # Output directory for all generated assets
│   └── <VideoTitle_Timestamp>/     # Each generation creates a subdirectory containing:
│       ├── story_data.json         #   - The generated video script (JSON)
│       ├── scene_1.jpg             #   - Generated image for scene 1
│       ├── scene_1.mp3             #   - Generated audio for scene 1
│       ├── scene_2.jpg             #   - Generated image for scene 2
│       ├── scene_2.mp3             #   - Generated audio for scene 2
│       └── <VideoTitle>.mp4        #   - Final synchronized video
│
├── .env                            # Environment variables (GEMINI_API_KEY) — DO NOT COMMIT
├── requirements.txt                # Python dependencies
├── storyenv/                       # Python virtual environment (not committed to git)
└── README.md                       # This file
```

---

## ⚙️ Setup and Installation

### Prerequisites

Ensure the following are installed on your system:

- **Python 3.9+** — [Download Python](https://www.python.org/downloads/)
- **pip** — comes bundled with Python
- **FFmpeg** — required by MoviePy for video processing
  - **Windows:** Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to your system PATH
  - **macOS:** `brew install ffmpeg`
  - **Linux:** `sudo apt-get install ffmpeg`
- **Google Gemini API Key** — Get one at [https://ai.google.dev/](https://ai.google.dev/)

### Step-by-Step Installation

**1. Clone the repository**

```bash
git clone https://github.com/your-username/Automated-Video-Generator.git
cd Automated-Video-Generator
```

**2. Create and activate a virtual environment**

```bash
# Create virtual environment
python -m venv storyenv

# Activate it
# On Windows:
.\storyenv\Scripts\activate

# On macOS/Linux:
source storyenv/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Set up your API key**

Create a `.env` file in the project root (same directory as `app.py`):

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

> **Note:** Get your free API key from [Google AI Studio](https://ai.google.dev/). The free tier has rate limits — upgrade for higher usage.

---

## 🚀 Commands to Run the Program

### Start the Application

```bash
# Make sure your virtual environment is activated first
.\storyenv\Scripts\activate        # Windows
source storyenv/bin/activate       # macOS/Linux

# Run the Flask server
python app.py
```

The server starts at **http://127.0.0.1:5000/** and a browser window will open automatically.

### Usage

1. Open **http://127.0.0.1:5000/** in your browser
2. Enter a **video prompt** (e.g., *"A brave astronaut discovering a neon-lit alien city"*)
3. Set the **Number of Scenes** (1–10)
4. Choose a **Visual Style** (Cinematic, Anime, Dramatic, etc.)
5. Click **Generate Video**
6. Wait for the AI pipeline to complete (typically 1–3 minutes)
7. **Watch** the video directly in the browser or **download** it

### Other Useful Commands

```bash
# Install a specific package
pip install <package-name>

# Update requirements.txt after adding new packages
pip freeze > requirements.txt

# Deactivate the virtual environment when done
deactivate
```

---

## ⚠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| `429 RESOURCE_EXHAUSTED` error | Your Gemini API key has reached its free-tier quota. Wait for reset or upgrade at [ai.google.dev](https://ai.google.dev/) |
| `GEMINI_API_KEY is not set` | Ensure your `.env` file exists in the project root with a valid key |
| Video has no audio/images | Check the Flask console for `ERROR` logs. Verify `.mp3` and `.jpg` files exist in `generated_videos/` |
| FFmpeg not found | Install FFmpeg and add it to your system PATH |
| `ModuleNotFoundError` | Ensure your virtual environment is activated and run `pip install -r requirements.txt` |

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
