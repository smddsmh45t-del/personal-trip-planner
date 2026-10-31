import os
import json
import base64
import httpx
import asyncio
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 智谱客户端（用于行程生成）
client = OpenAI(
    api_key=os.environ.get("ZAI_API_KEY"),
    base_url="https://open.bigmodel.cn/api/paas/v4/",
)

PERSONA_HINTS = {
    "特种兵": "每日6-8个景点，用餐时间不超过30分钟，早起晚归，节奏极快。",
    "文艺青年": "每日2-3个点，优先书店、咖啡馆、画廊、老建筑，留白多，避开人流密集区。",
    "街溜子": "单日步行8-15公里，路线连贯不折返，巷弄探索优先，少坐车。",
    "自然充电宝": "每日1-2个自然点位，公园、绿道、山、水优先，低强度，少排队。",
    "本地人体验卡": "单城市停留久，每日1-2个深度体验（市集、工坊、本地导览），重复到访同一区域。",
    "干饭猎人": "行程围绕吃什么展开，每日3-4餐重点标注，本地小馆、夜市优先，景点作为餐间填充。",
    "躺平度假官": "每日最多1个点，酒店和度假村权重高，午后不安排硬行程。",
    "遛娃指挥官": "每日2-3个点，室内外结合，午休时段锁定，避开长排队。",
    "追光摄影师": "日出、蓝调时刻锁定，机位标注，单点停留时间长。",
    "历史考据党": "遗址、博物馆、老城优先，配讲解或导览，单点深度停留。",
    "购物血拼侠": "商圈、奥特莱斯、本地市集优先，预留大块购物时段，预算向购物倾斜。",
    "夜行生物": "午后起步，夜市、酒吧、夜景优先，上午留空。",
    "独行侠": "灵活可改，单人友好餐厅，安全区域标注，社交活动可选不强制。",
    "抠门旅行家": "免费景点优先，公共交通优先，青旅或民宿，每日餐饮上限低。",
    "随缘漫游者": "不做详细攻略，每天只定一个大致方向，行程松散。",
    "仪式感信徒": "每座城市必须安排一件“当地人才做的事”，如逛菜市场、坐公交到终点站。",
    "反向旅游人": "专挑冷门小城、非热门时段，避开一切网红点。",
    "碳水教信徒": "行程围绕面食、米饭、小吃展开，一天多顿不嫌多。",
    "插座依赖症": "每2小时必须能坐下充电，咖啡馆和插座是刚需。",
    "博物馆钉子户": "一个馆能待一整天，行程按闭馆时间倒排。",
}

class TripRequest(BaseModel):
    destination: str
    days: int
    budget: int
    persona: str

@app.post("/generate")
async def generate_trip(req: TripRequest):
    hint = PERSONA_HINTS.get(req.persona, "按照常规旅行节奏安排。")
    system_prompt = f"""
import os
import json
import re
import httpx
import asyncio
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 智谱客户端（用于文本生成）
client = OpenAI(
    api_key=os.environ.get("ZAI_API_KEY"),
    base_url="https://open.bigmodel.cn/api/paas/v4/",
)

class TripRequest(BaseModel):
    destination: str
    days: int
    budget: int
    persona: str

@app.post("/generate")
async def generate_trip(req: TripRequest):
    system_prompt = f"""
你是一位顶级的旅行策划专家，能够深度模仿不同的人格来制定旅行计划。
你的任务是严格、完全、100%地扮演指定人格，并产出极其详尽和结构化的旅行计划。

**1. 严格扮演人格：**
*   **人格：** {req.persona}
*   **口吻：** 你的所有回答，包括每一个字，都必须符合这个人的说话方式、价值观和关注点。

**2. 旅行基本信息：**
*   **目的地：** {req.destination}
*   **天数：** {req.days}
*   **人均预算：** {req.budget} 元

**3. 输出结构（必须严格遵守此 Markdown 格式，不要输出多余的 HTML 标签）：**

## ✨ [你的旅行主题，用人设口吻命名]

### 📝 行程总览
*   **核心精神:** (用一句话总结这次旅行的灵魂)
*   **预算评估:** (基于预算，用人设口吻评价一下是“绰绰有余”还是“需要精打细算”)
*   **行程流转:** (用 A -> B -> C 的形式画出每日核心地点)

---

### 📅 每日详解

**(为每一天生成以下内容)**

#### **Day 1: [给第一天起个符合人设的名字]**
*   **上午:** [地点名称]。**人设点评:** (为什么你会来这)。**交通:** (详细说明如何到达)。
*   **午餐:** [餐厅名称]。**人设测评:** (为何推荐这家)。**人均:** (大约价格)。
*   **下午:** [地点名称]。**人设点评:** (为什么你会来这)。**交通:** (详细说明如何到达)。
*   **晚餐:** [餐厅名称]。**人设测评:** (为何推荐这家)。**人均:** (大约价格)。
*   **住宿:** [酒店或区域建议]。**人设测评:** (为什么住这)。

**(重复 Day 2, Day 3 ...)**

---

### 💡 人设专属Tips
*   **Tip 1:** (给出第一条只有这个人格才会想到的建议)
*   **Tip 2:** (给出第二条...)
*   **Tip 3:** (给出第三条...)

【重要附加要求】
在输出完上述所有 Markdown 文本后，你必须在最后附加一段 JSON 格式数据，用 ```json 和 ``` 包裹，用于给前端地图提取坐标。JSON 格式必须如下（不要输出其他文字）：
```json
{{
  "locations": [
    {{"name": "地点名称", "lng": 116.4074, "lat": 39.9042}}
  ]
}}
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="glm-4-flash",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"生成计划，必须是 JSON 格式。"}
                ],
                response_format={"type": "json_object"},
                max_tokens=2500,
            )
            content = response.choices[0].message.content
            if content and content.strip():
                return json.loads(content)
        except Exception as e:
            print(f"重试 {attempt}: {e}")
    return {"error": "生成失败，请重试。"}


# ================= 生成像素小人（Replicate） =================
@app.post("/generate-avatar")
async def generate_avatar(file: UploadFile = File(...)):
    # 1. 读取照片并转为 Base64 Data URI
    contents = await file.read()
    base64_image = base64.b64encode(contents).decode("utf-8")
    data_uri = f"data:{file.content_type};base64,{base64_image}"

    async with httpx.AsyncClient(timeout=120) as http_client:
        # 2. 发起生成任务
        try:
            response = await http_client.post(
                "https://api.replicate.com/v1/models/retro-diffusion/rd-plus/predictions",
                headers={
                    "Authorization": f"Token {os.environ.get('REPLICATE_API_TOKEN')}",
                    "Content-Type": "application/json",
                },
                json={
                    "input": {
                        "prompt": "A cute pixel art character, full body, korean ins style, white background, 8-bit",
                        "image": data_uri,          # 传入照片
                        "strength": 0.65,           # 控制相似度，建议 0.5 - 0.75 之间
                        "style": "classic",
                        "width": 256,
                        "height": 256
                    }
                },
            )
            prediction = response.json()
            
            if "urls" not in prediction:
                return {"error": "发起请求失败", "details": prediction}

            # 3. 轮询获取结果
            poll_url = prediction["urls"]["get"]
            for _ in range(30):  # 最多等 60 秒
                poll_resp = await http_client.get(
                    poll_url,
                    headers={"Authorization": f"Token {os.environ.get('REPLICATE_API_TOKEN')}"}
                )
                poll_data = poll_resp.json()
                
                if poll_data["status"] == "succeeded":
                    return {"image_url": poll_data["output"][0]}
                elif poll_data["status"] == "failed":
                    return {"error": "生成失败", "details": poll_data}
                
                await asyncio.sleep(2)
            
            return {"error": "生成超时，请重试"}
            
        except Exception as e:
            return {"error": f"发生异常: {str(e)}"}