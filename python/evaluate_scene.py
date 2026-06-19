import anthropic
import argparse
import base64
import json
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Step 3.1 — Evaluation criteria
# Three scoring dimensions, each 1–5, with reasoning required.
EVAL_SYSTEM_PROMPT = """You are a 3D scene quality evaluator for a PBR material pipeline.
You will be shown a rendered Unity scene. Evaluate it across three dimensions and return ONLY a valid JSON object.

Scoring dimensions (1 = poor, 5 = excellent):

1. material_consistency
   Does the surface texture look physically plausible? Does the material read correctly
   (roughness, reflectance, surface detail) under the given lighting?

2. lighting_plausibility
   Does the lighting feel natural and coherent? Are shadows and highlights consistent
   with the light source positions? Does the scene avoid harsh clipping or flat illumination?

3. spatial_composition
   Is the arrangement of objects spatially coherent? Does the layout feel intentional
   rather than random? Is there a clear visual hierarchy or focal point?

Output format — ONLY this JSON, no explanation, no markdown:
{
  "material_consistency": { "score": 4, "reason": "..." },
  "lighting_plausibility": { "score": 3, "reason": "..." },
  "spatial_composition":   { "score": 4, "reason": "..." },
  "overall_score": 3.7,
  "summary": "one sentence overall assessment"
}

overall_score = average of the three dimension scores, rounded to one decimal place."""


def encode_image(path: Path) -> str:
    with open(path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def evaluate_image(client: anthropic.Anthropic, image_path: Path, label: str) -> dict:
    print(f"  Evaluating: {image_path.name} ({label})")

    b64 = encode_image(image_path)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=EVAL_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": f"Evaluate this rendered scene. Label: {label}",
                    },
                ],
            }
        ],
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    result = json.loads(raw)
    result["label"] = label
    result["image"] = image_path.name
    return result


def find_screenshots(folder: Path) -> list[tuple[Path, str]]:
    # Accepts a folder of PNGs or the validation folder from Step 1.6
    # Returns list of (path, label) tuples
    images = sorted(folder.glob("*.png"))
    return [(img, img.stem) for img in images]


def main():
    parser = argparse.ArgumentParser(description="Step 3.2: Claude Vision API scene evaluation")
    parser.add_argument(
        "--images", metavar="FOLDER",
        help="Folder of scene screenshot PNGs to evaluate "
             "(default: docs/images/validation/)"
    )
    parser.add_argument(
        "--output", metavar="FILE",
        help="Output path for evaluation_report.json "
             "(default: pipeline/output/latest/evaluation_report.json)"
    )
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent

    # Resolve image folder
    if args.images:
        image_folder = Path(args.images)
    else:
        image_folder = repo_root / "docs" / "images" / "validation"

    if not image_folder.exists():
        print(f"Error: image folder not found: {image_folder}")
        return

    screenshots = find_screenshots(image_folder)
    if not screenshots:
        print(f"Error: no PNG files found in {image_folder}")
        return

    print(f"Found {len(screenshots)} screenshot(s) in {image_folder}")

    # Resolve output path
    if args.output:
        out_path = Path(args.output)
    else:
        output_root = repo_root / "pipeline" / "output"
        if output_root.exists():
            dirs = sorted([d for d in output_root.iterdir() if d.is_dir()], reverse=True)
            latest = dirs[0] if dirs else output_root
        else:
            latest = repo_root / "output"
        out_path = latest / "evaluation_report.json"

    client = anthropic.Anthropic(api_key=API_KEY)

    # Step 3.2 — evaluate each screenshot
    results = []
    for image_path, label in screenshots:
        try:
            result = evaluate_image(client, image_path, label)
            results.append(result)
            print(f"    overall: {result['overall_score']} — {result['summary']}")
        except Exception as e:
            print(f"    Error evaluating {image_path.name}: {e}")

    if not results:
        print("No results to save.")
        return

    # Aggregate summary across all evaluated images
    avg_overall = round(sum(r["overall_score"] for r in results) / len(results), 2)
    avg_per_dim = {}
    for dim in ("material_consistency", "lighting_plausibility", "spatial_composition"):
        scores = [r[dim]["score"] for r in results if dim in r]
        avg_per_dim[dim] = round(sum(scores) / len(scores), 2) if scores else None

    report = {
        "evaluated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "image_folder": str(image_folder),
        "num_images": len(results),
        "average_overall": avg_overall,
        "average_per_dimension": avg_per_dim,
        "results": results,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nEvaluation complete")
    print(f"  Average overall score : {avg_overall} / 5.0")
    for dim, val in avg_per_dim.items():
        print(f"  {dim:<30}: {val}")
    print(f"\nSaved → {out_path}")


if __name__ == "__main__":
    main()
