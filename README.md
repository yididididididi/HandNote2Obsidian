# 手写笔记OCR识别与Obsidian自动同步系统

独立设计并实现的手写笔记自动化同步工具，覆盖图片采集、OCR识别、文件写入全流程，解决手写内容无法在知识库中检索的痛点。

## 功能特性

- 调用 Google Gemini 3 Flash API 识别手写中英韩文
- 支持 HEIC 格式自动转换
- 关键词模糊搜索目标笔记
- 写入前人工确认与修改识别结果
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
