import argparse
import json
import numpy as np
import cv2
from pathlib import Path

# Step 2.1 — Texture Metadata Extraction
# Reads albedo/roughness/metallic maps for each texture set in a pipeline output folder
# and writes texture_library.json — used by prompt_to_scene.py to inform the LLM.


def dominant_color_hex(albedo_path: Path) -> str:
    # Mean RGB of albedo image → hex color string
    img = cv2.imread(str(albedo_path))
    if img is None:
        return "#808080"
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    mean = img_rgb.mean(axis=(0, 1)).astype(int)
    return "#{:02X}{:02X}{:02X}".format(mean[0], mean[1], mean[2])


def average_value(path: Path) -> float:
    # Average pixel intensity of a grayscale map, returned as 0.0–1.0
    img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        return 0.5
    return float(img.mean()) / 255.0


def latest_output_folder(repo_root: Path) -> Path | None:
    output_root = repo_root / "pipeline" / "output"
    if not output_root.exists():
        return None
    # YYYY-MM-DD_<material> naming → lexicographic descending = date descending
    dirs = sorted([d for d in output_root.iterdir() if d.is_dir()], reverse=True)
    return dirs[0] if dirs else None


def main():
    parser = argparse.ArgumentParser(description="Step 2.1: Extract PBR texture metadata")
    parser.add_argument("--folder", help="Pipeline output folder (default: latest in pipeline/output)")
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent

    if args.folder:
        folder = Path(args.folder)
    else:
        folder = latest_output_folder(repo_root)
        if folder is None:
            print("Error: no output folders found in pipeline/output")
            return

    if not folder.exists():
        print(f"Error: folder not found: {folder}")
        return

    print(f"Extracting metadata from: {folder}")

    # Material category from run_info.json written by pipeline.py
    run_info_path = folder / "run_info.json"
    category = "unknown"
    if run_info_path.exists():
        with open(run_info_path) as f:
            category = json.load(f).get("material", "unknown")

    albedo_files = sorted(folder.glob("*_albedo.png"))
    if not albedo_files:
        print(f"Error: no *_albedo.png files found in {folder}")
        return

    textures = []
    for albedo_path in albedo_files:
        texture_id = albedo_path.name.split("_")[0]  # "001", "002", ...

        roughness_path = folder / f"{texture_id}_roughness.png"
        metallic_path  = folder / f"{texture_id}_metallic.png"

        color_hex = dominant_color_hex(albedo_path)
        roughness  = average_value(roughness_path) if roughness_path.exists() else 0.5
        metallic   = average_value(metallic_path)  if metallic_path.exists()  else 0.0

        # Human-readable description — fed verbatim into the LLM system prompt
        material_type = "metallic" if metallic > 0.5 else "non-metallic"
        description = (
            f"{category}, color {color_hex}, "
            f"roughness {roughness:.2f}, {material_type}"
        )

        entry = {
            "id": texture_id,
            "category": category,
            "dominant_color_hex": color_hex,
            "roughness": round(roughness, 3),
            "metallic": round(metallic, 3),
            "description": description,
        }
        textures.append(entry)
        print(f"  [{texture_id}] {description}")

    library = {
        "output_folder": str(folder),
        "textures": textures,
    }

    out_path = folder / "texture_library.json"
    with open(out_path, "w") as f:
        json.dump(library, f, indent=2)
    print(f"\nSaved → {out_path}")


if __name__ == "__main__":
    main()
