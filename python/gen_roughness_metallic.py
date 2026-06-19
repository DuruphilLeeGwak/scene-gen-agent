import argparse
import sys
from pathlib import Path

import cv2
import numpy as np


# Material category lookup table — (roughness_min, roughness_max, metallic)
# Roughness: 0.0 = perfectly smooth, 1.0 = fully rough
# Metallic:  0.0 = dielectric (non-metal), 1.0 = full metal
MATERIAL_PRESETS = {
    "metal":    (0.2, 0.5,  1.0),
    "fabric":   (0.8, 1.0,  0.0),
    "wood":     (0.5, 0.8,  0.0),
    "stone":    (0.7, 0.9,  0.0),
    "concrete": (0.8, 0.95, 0.0),
    "ceramic":  (0.1, 0.4,  0.0),
}


def estimate_roughness(img_bgr: np.ndarray, r_min: float, r_max: float) -> float:
    # 알베도 이미지의 픽셀 분산(variance)을 분석해 roughness 범위 내에서 값 결정
    # 분산이 클수록 표면 디테일이 많다 → roughness 높게 설정
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    variance = float(np.var(gray))

    # variance를 [0, 0.05] 범위로 클램핑 후 정규화 (재료 사진 기준 경험값)
    normalized = min(variance / 0.05, 1.0)

    # 정규화된 분산을 카테고리 roughness 범위에 매핑
    roughness = r_min + normalized * (r_max - r_min)
    return round(roughness, 3)


def make_grayscale_map(value: float, size: tuple) -> np.ndarray:
    # 단일 값으로 채워진 512×512 grayscale 이미지 생성
    # value: 0.0~1.0 → pixel: 0~255
    pixel_val = int(np.clip(value * 255, 0, 255))
    return np.full(size, pixel_val, dtype=np.uint8)


def main():
    parser = argparse.ArgumentParser(description="Step 1.4: Roughness and metallic map generation")
    parser.add_argument("--input", default="pipeline/output", help="Root output folder containing material subfolders")
    parser.add_argument("--material", required=True, help="Material category (metal/fabric/wood/stone/concrete/ceramic)")
    args = parser.parse_args()

    # 카테고리 유효성 확인
    if args.material not in MATERIAL_PRESETS:
        print(f"Error: unknown material '{args.material}'")
        print(f"Available: {', '.join(MATERIAL_PRESETS.keys())}")
        sys.exit(1)

    r_min, r_max, metallic_val = MATERIAL_PRESETS[args.material]

    # 날짜 prefix 포함 폴더 탐색
    input_dir = Path(args.input)
    candidates = sorted(input_dir.glob(f"*_{args.material}"))
    if not candidates:
        print(f"Error: no folder matching *_{args.material} in {input_dir}")
        sys.exit(1)
    target_dir = candidates[-1]

    # albedo 파일 수집 (roughness 계산의 입력으로 사용)
    albedo_files = sorted(target_dir.glob("*_albedo.png"))
    if not albedo_files:
        print(f"Error: no *_albedo.png files found in {target_dir}")
        sys.exit(1)

    print(f"Material: {args.material}  |  roughness range: [{r_min}, {r_max}]  |  metallic: {metallic_val}")
    print(f"Input folder: {target_dir}")
    print()

    succeeded = 0
    failed = []

    for albedo_path in albedo_files:
        label = albedo_path.name.split("_")[0]
        roughness_path = target_dir / f"{label}_roughness.png"
        metallic_path  = target_dir / f"{label}_metallic.png"

        try:
            img_bgr = cv2.imread(str(albedo_path))
            if img_bgr is None:
                raise ValueError("Failed to load albedo image")

            h, w = img_bgr.shape[:2]

            # albedo 분산 분석으로 roughness 값 결정
            roughness_val = estimate_roughness(img_bgr, r_min, r_max)

            # roughness, metallic 각각 단색 grayscale 맵으로 저장
            roughness_map = make_grayscale_map(roughness_val, (h, w))
            metallic_map  = make_grayscale_map(metallic_val,  (h, w))

            cv2.imwrite(str(roughness_path), roughness_map)
            cv2.imwrite(str(metallic_path),  metallic_map)

            print(f"  [{label}] roughness={roughness_val:.3f} → {roughness_path.name}")
            print(f"  [{label}] metallic={metallic_val:.1f}   → {metallic_path.name}")
            succeeded += 1

        except Exception as e:
            print(f"  [{label}] FAILED: {e}")
            failed.append(albedo_path.name)

    print()
    print(f"Done. {succeeded}/{len(albedo_files)} processed → {target_dir}")
    if failed:
        print(f"Failed: {', '.join(failed)}")


if __name__ == "__main__":
    main()
