import os

from pathlib import Path
env_path = Path.home() / "HandNote2Obsidian/.env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip()

import base64
import requests
from datetime import datetime
from pathlib import Path
import shutil
import subprocess
from PIL import Image
import io

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
VAULT_PATH = Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/First Vault"

def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def convert_heic_to_jpeg(image_path):
    jpeg_path = Path(image_path).with_suffix(".jpeg")
    result = subprocess.run(
        ["sips", "-s", "format", "jpeg", str(image_path), "--out", str(jpeg_path)],
        capture_output=True
    )
    if result.returncode == 0:
        print(f"已将 HEIC 转换为 JPEG：{jpeg_path.name}")
        return str(jpeg_path)
    else:
        print("HEIC 转换失败")
        return None

def ocr_image(image_path):
    base64_image = encode_image(image_path)

    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={GEMINI_API_KEY}",
        headers={"Content-Type": "application/json"},
        json={
            "contents": [{
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": base64_image
                        }
                    },
                    {
                        "text": "你是一个精准的OCR助手。请识别用户提供的图片中的文字。包括中文手写体、英文和韩文。要求：1. 只输出识别结果，不要任何多余的废话（不要说'这是识别结果'等）。2. 尽量保持原有的段落换行和标点符号。3. 遇到极其潦草看不清的字，请结合上下文语境推测，如果实在无法推测可以用[?]代替。"
                    }
                ]
            }]
        }
    )
    result = response.json()
    if "candidates" not in result:
        print(f"API返回异常：{result}")
        return None
    return result["candidates"][0]["content"]["parts"][0]["text"]

def search_md_files(keyword):
    all_files = sorted(VAULT_PATH.glob("**/*.md"))
    if not keyword:
        return all_files
    return [f for f in all_files if keyword.lower() in f.stem.lower()]

def main():
    print("\n请输入图片路径（可以直接把图片拖入终端窗口）：")
    image_path = input().strip().strip("'\"")

    if not os.path.exists(image_path):
        print("图片不存在，请检查路径")
        return

    if Path(image_path).suffix.lower() == ".heic":
        image_path = convert_heic_to_jpeg(image_path)
        if not image_path:
            return

    while True:
        print("\n请输入笔记名称关键词搜索（直接回车显示全部）：")
        keyword = input().strip()
        results = search_md_files(keyword)

        if not results:
            print("没有找到匹配的笔记，请重新搜索")
            continue

        print(f"\n找到 {len(results)} 个笔记：")
        for i, f in enumerate(results):
            print(f"  {i+1}. {f.stem}")

        print("\n请输入序号选择（输入 0 重新搜索）：")
        idx = int(input().strip())
        if idx == 0:
            continue
        target_md = results[idx - 1]
        break

    print("\n正在识别图片文字...")
    recognized_text = ocr_image(image_path)
    if not recognized_text:
        print("识别失败，请检查 API Key 或网络连接")
        return
    print(f"\n识别结果：\n{recognized_text}")

    attachments_dir = VAULT_PATH / "attachments"
    attachments_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    ext = Path(image_path).suffix
    new_image_name = f"{timestamp}{ext}"
    shutil.copy2(image_path, attachments_dir / new_image_name)

    content = target_md.read_text(encoding="utf-8")
    insert = f"\n![[attachments/{new_image_name}]]\n\n{recognized_text}\n"

    if "## 手写笔记" in content:
        content = content.replace("## 手写笔记", f"## 手写笔记{insert}")
    else:
        content += f"\n## 手写笔记{insert}"

    target_md.write_text(content, encoding="utf-8")
    print(f"\n✅ 已成功写入「{target_md.stem}」")

if __name__ == "__main__":
    main()