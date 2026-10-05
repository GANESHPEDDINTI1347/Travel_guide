from flask import Flask, jsonify, request
from flask_cors import CORS
from google import genai
import requests
import tempfile
import base64
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MURF_API_KEY = os.getenv("MURF_API_KEY")
app = Flask(__name__)
CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"]
)
client = genai.Client(api_key=GEMINI_API_KEY)

PROMPTS = {
    "Summary": """
You are a professional tourist guide.
Provide a high-level overview of "{place}" in {language}.

Focus on:
- The historical significance
- Why the place is famous
- Key architectural or cultural highlights

Keep the explanation concise, engaging, and easy to follow.
Avoid excessive details and dates.
Limit the response to around 200 words.

Respond ONLY in {language}.""",
    "Detailed": """
You are a professional tourist guide.
Provide a detailed and immersive explanation of "{place}" in {language}.

Cover:
- Historical background and timeline
- Architectural design and unique features
- Cultural importance and notable events
- Interesting facts and visitor insights

Explain concepts clearly and in a storytelling manner.
Include relevant details and examples to create a rich experience.
Limit the response to around 400 words.

Respond ONLY in {language}.
"""
}

def generate_speech(text, voice_id, locale):
    temp_audio = tempfile.NamedTemporaryFile(
        suffix=".mp3",
        delete=False
    )
    url = "https://global.api.murf.ai/v1/speech/stream"
    headers = {
        "api-key": "ap2_ab32ec1e-69a7-45df-a43c-5060cfb73f37",
        "Content-Type": "application/json"
    }
    data = {
    "voice_id": voice_id,
    "text": text,
    "locale": locale,
    "model": "FALCON",
    "format": "MP3",
    "sampleRate": 24000,
    "channelType": "MONO"
    }

    response = requests.post(
        url,
        headers=headers,
        json=data
    )
    if response.status_code == 200:
        with open(temp_audio.name, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
    def generate_speech(text, voice_id, locale):
        temp_audio = tempfile.NamedTemporaryFile(
        suffix=".mp3",
        delete=False
    )

    url = "https://global.api.murf.ai/v1/speech/stream"

    headers = {
        "api-key": MURF_API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "voice_id": voice_id,
        "text": text,
        "locale": locale,
        "model": "FALCON",
        "format": "MP3",
        "sampleRate": 24000,
        "channelType": "MONO"
    }

    response = requests.post(
        url,
        headers=headers,
        json=data,
        timeout=120
    )

    if response.status_code != 200:
        raise Exception(
            f"Murf API error {response.status_code}: "
            f"{response.text}"
        )

    with open(temp_audio.name, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

    return temp_audio


def generate_description(place, answer_type, language):
    prompt = PROMPTS[answer_type].format(place=place, language=language)
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt
    )
    return response.text

@app.route("/generate-audio-guide", methods=["POST"])
def generate_audio_guide():

    try:
        data = request.get_json()

        place = data["place"]
        answer_type = data["answerType"]
        language = data["language"]
        voice_id = data["voiceId"]
        locale = data["locale"]

        print("================================")
        print("Generating audio guide")
        print("Place:", place)
        print("Answer Type:", answer_type)
        print("Language:", language)
        print("Voice:", voice_id)
        print("Locale:", locale)
        print("================================")

        # Generate AI description
        text_description = generate_description(
            place,
            answer_type,
            language
        )

        print("Gemini description generated.")

        # Generate audio
        audio_path = generate_speech(
            text_description,
            voice_id,
            locale
        )

        print("Murf audio generated.")

        with open(audio_path.name, "rb") as f:
            audio_bytes = f.read()

        encoded_audio = base64.b64encode(audio_bytes).decode("utf-8")

        return jsonify({
            "success": True,
            "description": text_description,
            "audioBase64": encoded_audio
        })

    except Exception as e:

        print("ERROR:", str(e))

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def generate_speech(text, voice_id, locale):

    temp_audio = tempfile.NamedTemporaryFile(
        suffix=".mp3",
        delete=False
    )

    url = "https://global.api.murf.ai/v1/speech/stream"

    headers = {
        "api-key":"ap2_ab32ec1e-69a7-45df-a43c-5060cfb73f37",
        "Content-Type": "application/json"
    }

    data = {
        "voice_id": voice_id,
        "text": text,
        "locale": locale,
        "model": "FALCON",
        "format": "MP3",
        "sampleRate": 24000,
        "channelType": "MONO"
    }

    response = requests.post(
        url,
        headers=headers,
        json=data,
        timeout=120
    )

    if response.status_code != 200:
        raise Exception(
            f"Murf API error {response.status_code}: "
            f"{response.text}"
        )

    with open(temp_audio.name, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

    return temp_audio

@app.route("/")
def home():
    return jsonify({
        "status": "success",
        "message": "Travel Guide API is running"
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=True
    )