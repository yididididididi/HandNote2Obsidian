#!/usr/bin/env python3
"""MCP server for Obsidian OCR - 手写笔记识别与保存"""

import sys
import json
import os
import base64
import shutil
import subprocess
import difflib
import requests
from datetime import datetime
from pathlib import Path

# 加载 .env
env_path = Path.home() / "HandNote2Obsidian/.env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
VAULT_PATH = Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/First Vault"

TOOLS = [
    {
        "name": "ocr_image",
        "description": "使用 Gemini Flash 识别图片中的手写文字（支持中文、英文、韩文）。支持 HEIC、JPEG、PNG 格式。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "图片的绝对路径"
                }
            },
            "required": ["image_path"]
        }
    },
    {
        "name": "save_to_obsidian",
        "description": "将 OCR 识别的文字和图片保存到 Obsidian 笔记中。图片归档到 attachments，文字插入 ## 手写笔记 区块。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "要保存的 OCR 识别文字"
                },
                "note_name": {
                    "type": "string",
                    "description": "目标笔记名称（支持模糊匹配）"
                },
                "image_path": {
                    "type": "string",
                    "description": "原始图片的绝对路径"
                }
            },
            "required": ["text", "note_name", "image_path"]
        }
    }
]


def do_ocr(image_path: str) -> str:
    path = Path(image_path.strip().strip("'\""))
    if not path.exists():
        return f"错误：图片不存在 {path}"

    # HEIC 转换
    if path.suffix.lower() == ".heic":
        jpeg_path = path.with_suffix(".jpeg")
        result = subprocess.run(
            ["sips", "-s", "format", "jpeg", str(path), "--out", str(jpeg_path)],
            capture_output=True
        )
        if result.returncode == 0:
            path = jpeg_path
        else:
            return "HEIC 转换失败"

    mime_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    mime_type = mime_map.get(path.suffix.lower(), "image/jpeg")

    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={GEMINI_API_KEY}",
        headers={"Content-Type": "application/json"},
        json={
            "contents": [{
                "parts": [
                    {"inline_data": {"mime_type": mime_type, "data": b64}},
                    {"text": "你是一个精准的OCR助手。请识别用户提供的图片中的文字。包括中文手写体、英文和韩文。要求：1. 只输出识别结果，不要任何多余的废话。2. 尽量保持原有的段落换行和标点符号。3. 遇到极其潦草看不清的字，请结合上下文语境推测，如果实在无法推测可以用[?]代替。"}
                ]
            }]
        }
    )
    result = response.json()
    if "candidates" not in result:
        return f"API 返回异常：{result}"
    return result["candidates"][0]["content"]["parts"][0]["text"]


def do_save(text: str, note_name: str, image_path: str) -> str:
    all_files = sorted(VAULT_PATH.glob("**/*.md"))

    # 优先子字符串匹配
    matches = [f for f in all_files if note_name.lower() in f.stem.lower()]

    # 若无结果，用 difflib 模糊匹配（相似度 ≥ 0.4）
    if not matches:
        stems = [f.stem for f in all_files]
        close = difflib.get_close_matches(note_name, stems, n=3, cutoff=0.4)
        if close:
            matches = [f for f in all_files if f.stem in close]
            hint = "（模糊匹配）"
        else:
            all_stems = "、".join(stems[:20])
            return f"没有找到笔记「{note_name}」。库中笔记（前20）：{all_stems}"
    else:
        hint = ""

    target_md = matches[0]

    # 归档图片：统一转换为 JPEG
    path = Path(image_path.strip().strip("'\""))
    attachments_dir = VAULT_PATH / "attachments"
    attachments_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    new_image_name = f"{timestamp}.jpg"
    dest_path = attachments_dir / new_image_name

    result = subprocess.run(
        ["sips", "-s", "format", "jpeg", str(path), "--out", str(dest_path)],
        capture_output=True
    )
    if result.returncode != 0:
        return f"图片转换失败：{result.stderr.decode()}"

    # 写入笔记，宽度设为 300
    content = target_md.read_text(encoding="utf-8")
    insert = f"\n![[attachments/{new_image_name}|300]]\n\n{text}\n"

    if "## 手写笔记" in content:
        content = content.replace("## 手写笔记", f"## 手写笔记{insert}", 1)
    else:
        content += f"\n## 手写笔记{insert}"

    target_md.write_text(content, encoding="utf-8")
    return f"✅ 已写入「{target_md.stem}」{hint}，图片已归档为 {new_image_name}"


def send(msg):
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def handle(req):
    method = req.get("method", "")
    req_id = req.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0", "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "obsidian-ocr", "version": "1.0.0"}
            }
        }

    elif method in ("notifications/initialized", "initialized"):
        return None  # notification，无需回复

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0", "id": req_id,
            "result": {"tools": TOOLS}
        }

    elif method == "tools/call":
        name = req.get("params", {}).get("name", "")
        args = req.get("params", {}).get("arguments", {})
        try:
            if name == "ocr_image":
                result_text = do_ocr(args["image_path"])
            elif name == "save_to_obsidian":
                result_text = do_save(args["text"], args["note_name"], args["image_path"])
            else:
                result_text = f"未知工具: {name}"
        except Exception as e:
            result_text = f"执行出错: {e}"

        return {
            "jsonrpc": "2.0", "id": req_id,
            "result": {"content": [{"type": "text", "text": result_text}]}
        }

    else:
        if req_id is not None:
            return {
                "jsonrpc": "2.0", "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            }
        return None


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        response = handle(req)
        if response is not None:
            send(response)


if __name__ == "__main__":
    main()
