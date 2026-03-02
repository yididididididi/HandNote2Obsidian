# 手写笔记OCR识别与Obsidian自动同步系统

独立设计并实现的手写笔记自动化同步工具，覆盖图片采集、OCR识别、文件写入全流程，解决手写内容无法在知识库中检索的痛点。

## 功能特性

- 调用 Google Gemini 3 Flash API 识别手写中英韩文
- 支持 HEIC 格式自动转换
- 关键词模糊搜索目标笔记
- 图片自动归档至 Obsidian vault attachments
- 识别内容以 Markdown 格式插入指定 `## 手写笔记` 区块

## 环境要求

- macOS
- Python 3.9+
- Obsidian vault 存储在 iCloud

## 安装

pip3 install requests pillow

## 配置

打开 obsidian_ocr.py，填入以下信息：

GEMINI_API_KEY = "你的Gemini_API_KEY"
VAULT_PATH = Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/你的vault名称"

## 使用方法

python3 obsidian_ocr.py

## 使用流程

1. 将手写笔记图片拖入终端窗口
2. 输入关键词搜索目标笔记，选择序号
3. 等待 OCR 识别完成
4. 确认识别结果，按需修改
5. 自动写入 Obsidian 对应文件

## 注意事项

- 需要 VPN 才能访问 Gemini API
- 图片建议从桌面拖入，不要直接从照片 App 内部路径拖入
- 每个目标 .md 文件中预置 ## 手写笔记 区块可精确控制插入位置

## MCP 版本（Claude Code 集成）

`ocr_mcp_server.py` 是基于 [Model Context Protocol](https://modelcontextprotocol.io) 的升级版本，可直接集成到 Claude Code CLI，让 Claude 作为 AI agent 直接调用 OCR 和写入功能。

### 注册 MCP server

```bash
claude mcp add obsidian-ocr --scope user python3 ~/HandNote2Obsidian/ocr_mcp_server.py
```

### 可用工具

| 工具 | 说明 |
|------|------|
| `ocr_image` | 识别图片中的手写文字（中/英/韩） |
| `save_to_obsidian` | 将识别文字和图片保存到指定 Obsidian 笔记 |

### 使用方法

注册后，直接在 Claude Code 中用自然语言描述，例如：

> `/Users/yidi/Downloads/IMG_2321.HEIC 帮我把这张图存入 雪的练习生`

Claude 会自动调用 OCR 识别后写入对应笔记，无需任何额外操作。

### 配置

在 `~/HandNote2Obsidian/.env` 中填入：

```
GEMINI_API_KEY=你的Gemini_API_KEY
```

---

## 后续优化方向

- 做成双击运行的 Mac App，不需要开终端
- 支持批量处理多张图片
- 写入前显示识别结果供用户确认和修改


