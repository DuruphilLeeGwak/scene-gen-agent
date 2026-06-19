import anthropic
import argparse
import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Base schema — objects may include an optional texture_id field
BASE_SYSTEM_PROMPT = """You are a 3D scene configuration generator for Unity.
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
      "color": {"r": 0.8, "g": 0.6, "b": 0.4},
      "texture_id": "001"
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
}

Rules for texture_id:
- texture_id is optional. Only assign it when a texture from the library suits the object.
- If no texture fits an object, omit texture_id entirely.
- color is always required as a fallback (used when texture_id is absent or fails to load)."""


def build_system_prompt(texture_library: dict | None) -> str:
    if not texture_library or not texture_library.get("textures"):
        return BASE_SYSTEM_PROMPT

    # Append texture library description so LLM can choose texture_id per object
    lines = ["\n\nAvailable textures (use texture_id to assign):"]
    for t in texture_library["textures"]:
        lines.append(f'  "{t["id"]}": {t["description"]}')
    lines.append(
        "\nChoose the texture whose description best matches each object's role. "
        "Multiple objects may share the same texture_id."
    )
    return BASE_SYSTEM_PROMPT + "\n".join(lines)


def load_texture_library(folder: Path | None) -> dict | None:
    # Find texture_library.json — from given folder or latest pipeline/output
    if folder:
        candidate = folder / "texture_library.json"
        if candidate.exists():
            with open(candidate) as f:
                return json.load(f)
        print(f"Warning: texture_library.json not found in {folder}")
        return None

    output_root = Path(__file__).parent.parent / "pipeline" / "output"
    if not output_root.exists():
        return None
    dirs = sorted([d for d in output_root.iterdir() if d.is_dir()], reverse=True)
    for d in dirs:
        candidate = d / "texture_library.json"
        if candidate.exists():
            print(f"Auto-detected texture library: {candidate}")
            with open(candidate) as f:
                return json.load(f)
    return None


def generate_scene(prompt: str, texture_library: dict | None) -> dict:
    client = anthropic.Anthropic(api_key=API_KEY)
    system_prompt = build_system_prompt(texture_library)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system_prompt,
        messages=[
            {"role": "user", "content": f"Generate a Unity scene for: {prompt}"}
        ]
    )

    raw = message.content[0].text.strip()
    # Strip markdown code blocks if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0].strip()
    return json.loads(raw)


def save_scene(scene_data: dict, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(scene_data, f, indent=2)
    print(f"Saved: {path}")
    print(json.dumps(scene_data, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Step 2.2: LLM scene generation with texture assignment")
    parser.add_argument("prompt", nargs="?",
                        default="dark warehouse with 3 boxes and 1 spotlight",
                        help="Scene description prompt")
    parser.add_argument("--textures", metavar="FOLDER",
                        help="Pipeline output folder containing texture_library.json "
                             "(default: auto-detect latest)")
    parser.add_argument("--output", default="output/scene.json",
                        help="Output path for scene.json (default: output/scene.json)")
    args = parser.parse_args()

    texture_folder = Path(args.textures) if args.textures else None
    texture_library = load_texture_library(texture_folder)

    if texture_library:
        print(f"Loaded {len(texture_library['textures'])} texture(s) from library")
    else:
        print("No texture library found — generating scene without texture assignment")

    print(f"Generating scene for: '{args.prompt}'")
    scene = generate_scene(args.prompt, texture_library)
    save_scene(scene, Path(args.output))
