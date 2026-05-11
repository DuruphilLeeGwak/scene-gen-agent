import anthropic
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
# --- 설정 ---
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OUTPUT_PATH = "../output/scene.json"

# --- Claude 호출 ---
def generate_scene(prompt: str) -> dict:
    client = anthropic.Anthropic(api_key=API_KEY)

    system_prompt = """You are a 3D scene configuration generator for Unity.
Given a text description, output ONLY a valid JSON object. No explanation, no markdown, no code blocks.

The JSON must follow this exact schema:
{
  "scene_id": "unique_id_string",
  "environment": {
    "type": "warehouse | office | outdoor | lab",
    "ambient_intensity": 0.1
  },
  "objects": [
    {
      "id": "obj_01",
      "type": "box | sphere | cylinder | capsule",
      "position": {"x": 0.0, "y": 0.5, "z": 0.0},
      "scale": {"x": 1.0, "y": 1.0, "z": 1.0},
      "color": {"r": 0.8, "g": 0.6, "b": 0.4}
    }
  ],
  "lights": [
    {
      "id": "light_01",
      "type": "spot | point | directional",
      "position": {"x": 0.0, "y": 5.0, "z": 0.0},
      "intensity": 3.0,
      "color": {"r": 1.0, "g": 0.9, "b": 0.8},
      "range": 10.0
    }
  ],
  "variant_seed": 42
}"""

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        system=system_prompt,
        messages=[
            {"role": "user", "content": f"Generate a Unity scene for: {prompt}"}
        ]
    )

    raw = message.content[0].text
    # 마크다운 코드블록 제거
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0]
    raw = raw.strip()
    scene_data = json.loads(raw)
    return scene_data


# --- 저장 ---
def save_scene(scene_data: dict, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(scene_data, f, indent=2)
    print(f"Saved: {path}")
    print(json.dumps(scene_data, indent=2))


# --- 실행 ---
if __name__ == "__main__":
    prompt = sys.argv[1] if len(sys.argv) > 1 else "dark warehouse with 3 boxes and 1 spotlight"
    print(f"Generating scene for: '{prompt}'")
    scene = generate_scene(prompt)
    save_scene(scene, OUTPUT_PATH)