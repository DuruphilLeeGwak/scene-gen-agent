import argparse
import sys
from pathlib import Path
from datetime import date

import cv2
import numpy as np
from PIL import Image


# 배경 제거: 픽셀값 10 이하를 배경으로 보고 가장 큰 윤곽의 bounding box만 남긴다
def crop_to_subject(img_bgr):
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 윤곽이 없으면 원본 그대로 반환
    if not contours:
        return img_bgr

    x, y, w, h = cv2.boundingRect(max(contours, key=cv2.contourArea))
    return img_bgr[y:y + h, x:x + w]


# 밝기 평탄화: LAB 색공간의 L채널에만 CLAHE를 적용해 조명 영향을 줄인다
def flatten_brightness(img_bgr):
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    # clipLimit: 대비 증폭 상한 / tileGridSize: 로컬 영역 분할 크기
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)

    lab = cv2.merge([l, a, b])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


def main():
    # CLI 인수 정의
    parser = argparse.ArgumentParser(description="Material photo preprocessing step")
    parser.add_argument("--input", default="pipeline/input/raw", help="Folder containing source images (default: pipeline/input/raw)")
    parser.add_argument("--material", required=True, help="Material category (e.g. concrete, fabric, wood)")
    parser.add_argument("--output", default="pipeline/output", help="Root output folder (default: pipeline/output)")
    args = parser.parse_args()

    # 입력 폴더 유효성 확인
    input_dir = Path(args.input)
    if not input_dir.is_dir():
        print(f"Error: {input_dir} is not a directory")
        sys.exit(1)

    # jpg / jpeg / png 파일만 수집 후 파일명 기준 정렬
    image_files = sorted(
        [p for p in input_dir.glob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png"}]
    )

    if not image_files:
        print(f"Error: no jpg/jpeg/png files found in {input_dir}")
        sys.exit(1)

    # 출력 폴더 생성: pipeline/output/YYYY-MM-DD_<material>/
    today = date.today().strftime("%Y-%m-%d")
    output_dir = Path(args.output) / f"{today}_{args.material}"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Found {len(image_files)} image(s) → output: {output_dir}")
    print()

    succeeded = 0
    failed = []

    # 파일별 처리 루프 — 순번 001, 002... 부여
    for idx, src_path in enumerate(image_files, start=1):
        label = f"{idx:03d}"
        out_path = output_dir / f"{label}_source_crop.png"

        try:
            # PIL로 로드 후 BGR로 변환 (cv2 처리를 위해)
            pil_img = Image.open(src_path).convert("RGB")
            img_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

            # 전처리 3단계: crop → 밝기 평탄화 → 512×512 리사이즈
            img_bgr = crop_to_subject(img_bgr)
            img_bgr = flatten_brightness(img_bgr)
            img_bgr = cv2.resize(img_bgr, (512, 512), interpolation=cv2.INTER_LANCZOS4)

            # 결과 저장
            cv2.imwrite(str(out_path), img_bgr)
            print(f"  [{label}] {src_path.name} → {out_path.name}")
            succeeded += 1

        except Exception as e:
            print(f"  [{label}] {src_path.name} — FAILED: {e}")
            failed.append(src_path.name)

    # 처리 요약 출력
    print()
    print(f"Done. {succeeded}/{len(image_files)} processed → {output_dir}")
    if failed:
        print(f"Failed: {', '.join(failed)}")


if __name__ == "__main__":
    main()
