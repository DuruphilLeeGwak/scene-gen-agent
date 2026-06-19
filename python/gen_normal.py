import argparse
import sys
from pathlib import Path

import cv2
import numpy as np


def albedo_to_normal(img_bgr: np.ndarray, strength: float = 4.0) -> np.ndarray:
    # grayscale로 변환 — 밝기값을 height(높낮이)로 해석
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0

    # Sobel 필터로 X, Y 방향 기울기(gradient) 계산
    # strength가 높을수록 표면 요철이 강하게 표현됨
    grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3) * strength
    grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3) * strength

    # gradient로부터 normal 벡터 구성: N = normalize(-gx, -gy, 1)
    # Z=1 고정으로 표면이 카메라를 향한다고 가정
    normal = np.dstack((-grad_x, -grad_y, np.ones_like(gray)))

    # 각 픽셀의 normal 벡터를 단위벡터로 정규화
    norm = np.linalg.norm(normal, axis=2, keepdims=True)
    normal = normal / (norm + 1e-8)

    # [-1, 1] → [0, 255] 로 remapping (OpenGL 표준 normal map 포맷)
    normal_img = ((normal + 1.0) / 2.0 * 255.0).astype(np.uint8)

    # normal map은 RGB 저장 (cv2는 BGR이므로 채널 순서 변환)
    # R=X, G=Y, B=Z
    normal_bgr = cv2.cvtColor(normal_img, cv2.COLOR_RGB2BGR)
    return normal_bgr


def main():
    parser = argparse.ArgumentParser(description="Step 1.3: Normal map generation from albedo")
    parser.add_argument("--input", default="pipeline/output", help="Folder containing YYYY-MM-DD_<material> subfolders")
    parser.add_argument("--material", required=True, help="Material subfolder name suffix (e.g. concrete)")
    parser.add_argument("--strength", type=float, default=4.0, help="Surface relief strength (default: 4.0)")
    args = parser.parse_args()

    # 입력 폴더: pipeline/output/YYYY-MM-DD_<material>/
    input_dir = Path(args.input)
    # 날짜 prefix 포함한 실제 폴더 찾기
    candidates = sorted(input_dir.glob(f"*_{args.material}"))
    if not candidates:
        print(f"Error: no folder matching *_{args.material} in {input_dir}")
        sys.exit(1)

    # 여러 개면 가장 최신(마지막) 폴더 사용
    target_dir = candidates[-1]
    print(f"Input folder: {target_dir}")

    # albedo 파일 수집
    albedo_files = sorted(target_dir.glob("*_albedo.png"))
    if not albedo_files:
        print(f"Error: no *_albedo.png files found in {target_dir}")
        sys.exit(1)

    print(f"Found {len(albedo_files)} albedo image(s) → strength={args.strength}")
    print()

    succeeded = 0
    failed = []

    for albedo_path in albedo_files:
        # 순번 추출: "001_albedo.png" → "001"
        label = albedo_path.name.split("_")[0]
        out_path = target_dir / f"{label}_normal.png"

        try:
            # albedo 로드 → normal map 생성 → 저장
            img_bgr = cv2.imread(str(albedo_path))
            if img_bgr is None:
                raise ValueError("Failed to load image")

            normal_bgr = albedo_to_normal(img_bgr, strength=args.strength)
            cv2.imwrite(str(out_path), normal_bgr)

            print(f"  [{label}] {albedo_path.name} → {out_path.name}")
            succeeded += 1

        except Exception as e:
            print(f"  [{label}] {albedo_path.name} — FAILED: {e}")
            failed.append(albedo_path.name)

    print()
    print(f"Done. {succeeded}/{len(albedo_files)} processed → {target_dir}")
    if failed:
        print(f"Failed: {', '.join(failed)}")


if __name__ == "__main__":
    main()
