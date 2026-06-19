import argparse
import json
import sys
import subprocess
from pathlib import Path
from datetime import date


# 각 단계 스크립트 경로 (pipeline.py 기준 상대 경로)
SCRIPTS_DIR     = Path(__file__).parent
CAPTURE_SCRIPT  = SCRIPTS_DIR / "capture_to_pbr.py"
ALBEDO_SCRIPT   = SCRIPTS_DIR / "comfy_albedo.py"
NORMAL_SCRIPT   = SCRIPTS_DIR / "gen_normal.py"
ROUGHMET_SCRIPT = SCRIPTS_DIR / "gen_roughness_metallic.py"
METADATA_SCRIPT = SCRIPTS_DIR / "extract_metadata.py"


def run_step(label: str, cmd: list):
    # 각 단계를 subprocess로 실행하고 실패 시 즉시 중단
    print(f"\n{'='*50}")
    print(f"  {label}")
    print(f"{'='*50}")
    result = subprocess.run(cmd, text=True)
    if result.returncode != 0:
        print(f"\nError: {label} failed (exit code {result.returncode}). Stopping pipeline.")
        sys.exit(result.returncode)


def main():
    parser = argparse.ArgumentParser(
        description="Scene Gen Agent — full material-to-PBR pipeline (Steps 1.1–1.4)"
    )
    # 입력 이미지 폴더 (기본: pipeline/input/raw)
    parser.add_argument("--input", default="pipeline/input/raw",
                        help="Folder containing raw material photos (default: pipeline/input/raw)")
    # 재료 카테고리 (roughness/metallic 룩업 테이블 키)
    parser.add_argument("--material", required=True,
                        help="Material category: metal / fabric / wood / stone / concrete / ceramic")
    # 출력 루트 폴더 (기본: pipeline/output)
    parser.add_argument("--output", default="pipeline/output",
                        help="Root output folder (default: pipeline/output)")
    # ControlNet 밝기 평탄화 강도
    parser.add_argument("--strength", type=float, default=4.0,
                        help="Normal map surface relief strength (default: 4.0)")
    # ComfyUI 서버 주소
    parser.add_argument("--comfy-url", default="http://127.0.0.1:8000",
                        help="ComfyUI server URL (default: http://127.0.0.1:8000)")
    args = parser.parse_args()

    # 날짜 기반 출력 폴더 경로 계산
    today = date.today().strftime("%Y-%m-%d")
    run_output = str(Path(args.output) / f"{today}_{args.material}")

    print(f"\nScene Gen Agent — Material to PBR Pipeline")
    print(f"  material : {args.material}")
    print(f"  input    : {args.input}")
    print(f"  output   : {run_output}")

    # Step 1.1 — 전처리: crop + CLAHE + resize → source_crop.png
    run_step("Step 1.1 — Preprocessing (crop + CLAHE + resize)", [
        sys.executable, str(CAPTURE_SCRIPT),
        "--input",    args.input,
        "--material", args.material,
        "--output",   args.output,
    ])

    # Step 1.2 — ControlNet Tile → albedo.png
    run_step("Step 1.2 — Albedo generation (ComfyUI ControlNet Tile)", [
        sys.executable, str(ALBEDO_SCRIPT),
        "--input",  run_output,
        "--output", run_output,
    ])

    # Step 1.3 — Sobel gradient → normal.png
    run_step("Step 1.3 — Normal map generation (Sobel gradient)", [
        sys.executable, str(NORMAL_SCRIPT),
        "--material", args.material,
        "--strength", str(args.strength),
    ])

    # Step 1.4 — 카테고리 룩업 + 분산 분석 → roughness.png, metallic.png
    run_step("Step 1.4 — Roughness and metallic estimation", [
        sys.executable, str(ROUGHMET_SCRIPT),
        "--material", args.material,
    ])

    # run_info.json — 재료 카테고리와 날짜를 기록, extract_metadata.py가 읽음
    run_info = {"material": args.material, "date": today}
    with open(Path(run_output) / "run_info.json", "w") as f:
        json.dump(run_info, f, indent=2)

    # Step 2.1 — 텍스처 메타데이터 추출 → texture_library.json
    run_step("Step 2.1 — Texture metadata extraction", [
        sys.executable, str(METADATA_SCRIPT),
        "--folder", run_output,
    ])

    # 최종 출력 파일 목록 요약
    print(f"\n{'='*50}")
    print(f"  Pipeline complete → {run_output}")
    print(f"{'='*50}")
    out_dir = Path(run_output)
    if out_dir.exists():
        files = sorted(out_dir.glob("*.png"))
        for f in files:
            print(f"  {f.name}")


if __name__ == "__main__":
    main()
