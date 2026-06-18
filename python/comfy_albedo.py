import argparse
import json
import sys
import time
import urllib.request
import urllib.parse
import uuid
import shutil
from pathlib import Path

# ComfyUI 서버 주소 (데스크탑 앱은 8000 포트 사용)
COMFY_URL = "http://127.0.0.1:8000"


def check_server():
    # ComfyUI 서버가 응답하는지 확인
    try:
        urllib.request.urlopen(f"{COMFY_URL}/system_stats", timeout=3)
        return True
    except Exception:
        return False


def build_workflow(image_b64_name: str) -> dict:
    # ControlNet Tile 워크플로우 JSON 구성
    # 구조: 이미지 로드 → SD1.5 모델 로드 → ControlNet Tile 적용 → KSampler → 저장
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": "v1-5-pruned-emaonly.safetensors"
            }
        },
        "2": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                # albedo 생성용 프롬프트: 조명 제거, 순수 재료 색상+텍스처 유도
                "text": "material surface texture, flat diffuse albedo, no shadows, no specular highlights, no baked lighting, uniform illumination, PBR albedo map",
                "clip": ["1", 1]
            }
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                # 네거티브: 조명/그림자/광택 억제
                "text": "shadow, specular, highlight, glossy, reflection, baked lighting, dark areas, bright spots",
                "clip": ["1", 1]
            }
        },
        "4": {
            "class_type": "LoadImage",
            "inputs": {
                "image": image_b64_name
            }
        },
        "5": {
            "class_type": "ControlNetLoader",
            "inputs": {
                "control_net_name": "control_v11f1e_sd15_tile.pth"
            }
        },
        "6": {
            "class_type": "ControlNetApply",
            "inputs": {
                # strength: ControlNet이 입력 이미지 구조를 얼마나 따를지 (0.8 = 강하게 따름)
                "conditioning": ["2", 0],
                "control_net": ["5", 0],
                "image": ["4", 0],
                "strength": 0.8
            }
        },
        "7": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "positive": ["6", 0],
                "negative": ["3", 0],
                "latent_image": ["8", 0],
                "seed": 42,
                "steps": 20,
                # denoise: 낮을수록 원본 구조 유지 (0.4 = 조명만 제거, 텍스처 보존)
                "denoise": 0.4,
                "cfg": 7.0,
                "sampler_name": "euler",
                "scheduler": "normal"
            }
        },
        "8": {
            "class_type": "VAEEncode",
            "inputs": {
                "pixels": ["4", 0],
                "vae": ["1", 2]
            }
        },
        "9": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["7", 0],
                "vae": ["1", 2]
            }
        },
        "10": {
            "class_type": "SaveImage",
            "inputs": {
                # ComfyUI output 폴더에 임시 저장 후 우리 pipeline/output으로 복사
                "filename_prefix": "albedo_tmp",
                "images": ["9", 0]
            }
        }
    }


def upload_image(img_path: Path) -> str:
    # ComfyUI input 폴더에 이미지 업로드, 서버가 참조할 파일명 반환
    with open(img_path, "rb") as f:
        data = f.read()

    boundary = "----boundary"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image"; filename="{img_path.name}"\r\n'
        f"Content-Type: image/png\r\n\r\n"
    ).encode() + data + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"{COMFY_URL}/upload/image",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
    return result["name"]


def queue_prompt(workflow: dict) -> str:
    # 워크플로우를 ComfyUI 큐에 전송, prompt_id 반환
    client_id = str(uuid.uuid4())
    payload = json.dumps({"prompt": workflow, "client_id": client_id}).encode()
    req = urllib.request.Request(
        f"{COMFY_URL}/prompt",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
        return result["prompt_id"]
    except urllib.error.HTTPError as e:
        # 400 에러 시 ComfyUI가 반환하는 상세 오류 출력
        body = e.read().decode()
        print(f"\nComfyUI error {e.code}: {body}")
        sys.exit(1)


def wait_for_completion(prompt_id: str, timeout: int = 120) -> bool:
    # 큐에서 해당 prompt_id가 사라질 때까지 대기 (완료 신호)
    start = time.time()
    while time.time() - start < timeout:
        with urllib.request.urlopen(f"{COMFY_URL}/queue") as resp:
            queue = json.loads(resp.read())
        running = [item for item in queue.get("queue_running", []) if item[1] == prompt_id]
        pending = [item for item in queue.get("queue_pending", []) if item[1] == prompt_id]
        if not running and not pending:
            return True
        time.sleep(2)
    return False


def get_output_image(prompt_id: str) -> str | None:
    # history에서 해당 prompt_id의 출력 파일명 가져오기
    with urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}") as resp:
        history = json.loads(resp.read())
    outputs = history.get(prompt_id, {}).get("outputs", {})
    for node_output in outputs.values():
        images = node_output.get("images", [])
        if images:
            return images[0]["filename"]
    return None


def download_output(filename: str, dest: Path):
    # ComfyUI output 폴더에서 결과 이미지를 pipeline/output으로 복사
    encoded = urllib.parse.quote(filename)
    url = f"{COMFY_URL}/view?filename={encoded}&type=output"
    with urllib.request.urlopen(url) as resp:
        dest.write_bytes(resp.read())


def main():
    parser = argparse.ArgumentParser(description="Step 1.2: ControlNet Tile albedo generation")
    parser.add_argument("--input", required=True, help="Folder containing *_source_crop.png files")
    parser.add_argument("--output", required=True, help="Output folder (same as input is fine)")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # ComfyUI 서버 연결 확인
    if not check_server():
        print("Error: ComfyUI server not running at", COMFY_URL)
        print("Please start ComfyUI first.")
        sys.exit(1)

    # source_crop 파일 수집
    crops = sorted(input_dir.glob("*_source_crop.png"))
    if not crops:
        print(f"Error: no *_source_crop.png files found in {input_dir}")
        sys.exit(1)

    print(f"Found {len(crops)} source_crop image(s)")
    print()

    for crop_path in crops:
        # 순번 추출: "001_source_crop.png" → "001"
        label = crop_path.name.split("_")[0]
        out_path = output_dir / f"{label}_albedo.png"

        print(f"  [{label}] {crop_path.name} → {out_path.name}")

        # 이미지 업로드 → 워크플로우 전송 → 완료 대기 → 결과 저장
        uploaded_name = upload_image(crop_path)
        workflow = build_workflow(uploaded_name)
        prompt_id = queue_prompt(workflow)

        print(f"         queued (id: {prompt_id[:8]}...) waiting...", end="", flush=True)
        success = wait_for_completion(prompt_id)

        if not success:
            print(" TIMEOUT")
            continue

        out_filename = get_output_image(prompt_id)
        if not out_filename:
            print(" no output found")
            continue

        download_output(out_filename, out_path)
        print(f" done → {out_path.name}")

    print()
    print(f"Albedo generation complete → {output_dir}")


if __name__ == "__main__":
    main()
