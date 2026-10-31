# 戏精旅行规划局 (Personal Trip Planner)

让你的旅行，人设先行！

这是一个基于大语言模型（LLM）的个性化旅行规划器。不同于传统的旅游攻略，本项目引入了“人格（Persona）”的概念。用户可以选择“特种兵”、“文艺青年”、“自然充电宝”等 20 种不同的人格，AI 会完全代入该人格的口吻、价值观和节奏，生成极其详尽的行程计划。

## ✨ 核心功能

- **20种预设人格**：从“干饭猎人”到“历史考据党”，满足各种旅行偏好。
- **戏精级 Prompt 调教**：生成的行程包含大量“人设点评”，不仅是路线，更是情绪价值。
- **Markdown 结构化渲染**：前端完美解析每日详解、Tips 和预算评估。
- **Leaflet 地图打点**：后端自动从 AI 返回的文本中分离出经纬度 JSON，在前端地图上高亮显示所有地点。
- **星露谷像素风 UI**：纯 CSS 绘制的天空、云朵、世界地标（富士山、自由女神像等），搭配专属像素小人，可自定义发色、衣服、生日等。
- **本地持久化**：小人的设定保存在浏览器中。

## 🛠️ 技术栈

- **前端**：Vue 3 + Vite + Leaflet (高德瓦片) + `marked` (Markdown 渲染)
- **后端**：FastAPI + 智谱 AI (GLM-4-Flash) + Python

## 🚀 如何运行

### 1. 启动后端
```bash
# 进入项目根目录
pip install fastapi uvicorn openai python-dotenv httpx
# 配置你的 API Key
# 在根目录创建 .env，写入 ZAI_API_KEY=你的智谱Key
uvicorn main:app --reload --port 8000
