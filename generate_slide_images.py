#!/usr/bin/env python3
"""Generate cinematic slide background images using Gemini 3 Pro image generation."""

import base64
import os
import sys

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Installing google-genai package...")
    os.system(f"{sys.executable} -m pip install -q google-genai")
    from google import genai
    from google.genai import types

# Load from .env if not already in environment
_env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

API_KEY = os.environ.get("GEMINI_API_KEY", "")
MODEL = "gemini-3-pro-image-preview"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "app", "landing", "static", "images")

SLIDES = [
    {
        "filename": "slide-1.png",
        "prompt": (
            "Generate an image: Cinematic deep space scene with a vibrant blue and purple nebula, "
            "Earth visible in the lower corner glowing with atmosphere, distant stars, "
            "dark background suitable for text overlay, wide 16:9 aspect ratio, "
            "photorealistic space photography style, dramatic lighting, no text or letters anywhere"
        ),
    },
    {
        "filename": "slide-2.png",
        "prompt": (
            "Generate an image: Abstract futuristic data constellation in deep space, glowing neural network "
            "nodes connected by light beams in teal and electric blue, representing AI "
            "intelligence and observability, dark background with subtle star field, "
            "wide 16:9 cinematic composition, no text or letters anywhere, suitable for text overlay"
        ),
    },
    {
        "filename": "slide-3.png",
        "prompt": (
            "Generate an image: Dramatic rocket launch viewed from space perspective, rocket trail of fire "
            "and smoke ascending from Earth's atmosphere into dark space, cinematic "
            "wide angle, dramatic lighting with orange and blue contrast, photorealistic, "
            "no text or letters anywhere, dark areas suitable for text overlay, 16:9 aspect ratio"
        ),
    },
]


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    client = genai.Client(api_key=API_KEY)

    for slide in SLIDES:
        filepath = os.path.join(OUTPUT_DIR, slide["filename"])
        print(f"Generating {slide['filename']} with {MODEL}...")

        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=slide["prompt"],
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                ),
            )

            # Extract image from response parts
            saved = False
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                    with open(filepath, "wb") as f:
                        f.write(part.inline_data.data)
                    print(f"  Saved: {filepath}")
                    saved = True
                    break

            if not saved:
                print(f"  WARNING: No image found in response for {slide['filename']}")
                # Print text parts for debugging
                for part in response.candidates[0].content.parts:
                    if part.text:
                        print(f"  Text response: {part.text[:200]}")

        except Exception as e:
            print(f"  ERROR generating {slide['filename']}: {e}")

    print("\nDone! Images saved to:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
