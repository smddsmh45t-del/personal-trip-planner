<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const currentView = ref('home') 
const showUploadModal = ref(false)

const avatar = ref({
  name: '小像素',
  hairColor: '#5C4033', 
  clothColor: '#A8E6CF', 
  faceColor: '#FFE0B2'   
})

const generatingAvatar = ref(false)
const hasCustomImage = ref(false)

const visitedPlaces = ref([
  { name: '北京', lat: 39.9042, lng: 116.4074, date: '2023-10-01', diary: '爬了长城。' },
  { name: '上海', lat: 31.2304, lng: 121.4737, date: '2024-01-15', diary: '外滩夜景。' }
])

const personas = [
  '特种兵', '文艺青年', '街溜子', '自然充电宝', '本地人体验卡',
  '干饭猎人', '躺平度假官', '遛娃指挥官', '追光摄影师', '历史考据党',
  '购物血拼侠', '夜行生物', '独行侠', '抠门旅行家',
  '随缘漫游者', '仪式感信徒', '反向旅游人', '碳水教信徒', '插座依赖症', '博物馆钉子户'
]

const destination = ref('京都')
const days = ref(3)
const budget = ref(5000)
const persona = ref('自然充电宝')
const result = ref(null)
const loading = ref(false)

let map = null
let markersGroup = null
const mapContainer = ref(null)
const recordMapContainer = ref(null)
let recordMap = null

const newPoiName = ref('')
const newPoiTime = ref('09:00')

onMounted(() => {
  const savedAvatar = localStorage.getItem('pixelAvatar')
  if (savedAvatar) {
    const parsed = JSON.parse(savedAvatar)
    avatar.value.name = parsed.name
    avatar.value.hairColor = parsed.hairColor
    avatar.value.clothColor = parsed.clothColor
  }
  setTimeout(() => {
    if (currentView.value === 'planner') initPlannerMap()
    if (currentView.value === 'record') initRecordMap()
  }, 200)
})

watch(currentView, async (newVal) => {
  if (newVal === 'planner') {
    await nextTick()
    initPlannerMap()
  } else if (newVal === 'record') {
    await nextTick()
    initRecordMap()
  }
})

function saveAvatar() {
  const toSave = { name: avatar.value.name, hairColor: avatar.value.hairColor, clothColor: avatar.value.clothColor }
  localStorage.setItem('pixelAvatar', JSON.stringify(toSave))
}

function handlePhotoUpload(event) {
  const file = event.target.files[0]
  if (!file) return
  
  generatingAvatar.value = true
  showUploadModal.value = false 
  
  const reader = new FileReader()
  reader.onload = (e) => {
    const img = new Image()
    img.onload = () => {
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')
      canvas.width = 1
      canvas.height = 1
      ctx.drawImage(img, 0, 0, 1, 1)
      const [r, g, b] = ctx.getImageData(0, 0, 1, 1).data
      
      const hexColor = `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`
      
      setTimeout(() => {
        avatar.value.hairColor = hexColor
        hasCustomImage.value = true
        saveAvatar()
        generatingAvatar.value = false
      }, 1200)
    }
    img.src = e.target.result
  }
  reader.readAsDataURL(file)
}

function initPlannerMap() {
  if (!mapContainer.value) return
  if (map) { map.remove(); map = null }
  map = L.map(mapContainer.value).setView([35.0, 105.0], 4)
  L.tileLayer('https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}', { maxZoom: 18 }).addTo(map)
  markersGroup = L.layerGroup().addTo(map)
  setTimeout(() => map.invalidateSize(), 200)
  if (result.value) renderMarkers()
}

function renderMarkers() {
  if (!map || !markersGroup || !result.value) return
  markersGroup.clearLayers()
  const allLatLngs = []
  let count = 1
  result.value.daily_plans.forEach(day => {
    day.schedule.forEach(item => {
      if (item.poi && item.poi.lng && item.poi.lat) {
        allLatLngs.push([item.poi.lat, item.poi.lng])
        const customIcon = L.divIcon({
          className: 'custom-marker',
          html: `<div class="pixel-badge">${count}. ${item.poi.name}</div>`,
          iconSize: null
        })
        L.marker([item.poi.lat, item.poi.lng], { icon: customIcon }).addTo(markersGroup)
        count++
      }
    })
  })
  if (allLatLngs.length > 0) map.fitBounds(allLatLngs, { padding: [50, 50], maxZoom: 15 })
}

async function generate() {
  loading.value = true
  try {
    const res = await fetch('http://127.0.0.1:8000/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ destination: destination.value, days: days.value, budget: budget.value, persona: persona.value }),
    })
    const data = await res.json()
    if (data.error) { alert(data.error); result.value = null; return }
    result.value = data
    await nextTick()
    renderMarkers()
  } catch (err) {
    alert("请求后端失败！")
  } finally {
    loading.value = false
  }
}

function removePoi(dayIndex, scheduleIndex) {
  result.value.daily_plans[dayIndex].schedule.splice(scheduleIndex, 1)
  renderMarkers()
}

function addPoi(dayIndex) {
  if (!newPoiName.value.trim()) return
  const day = result.value.daily_plans[dayIndex]
  day.schedule.push({
    time: newPoiTime.value || '09:00',
    activity: `前往${newPoiName.value}`,
    poi: { name: newPoiName.value, lng: 135.78, lat: 34.99, note: '用户添加' }
  })
  newPoiName.value = ''
  renderMarkers()
}

function initRecordMap() {
  if (!recordMapContainer.value) return
  if (recordMap) { recordMap.remove(); recordMap = null }
  recordMap = L.map(recordMapContainer.value).setView([35.0, 105.0], 4)
  L.tileLayer('https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}', { maxZoom: 18 }).addTo(recordMap)
  visitedPlaces.value.forEach(place => {
    L.circleMarker([place.lat, place.lng], {
      radius: 12, fillColor: "#A8E6CF", color: "#4CAF50", weight: 4, opacity: 1, fillOpacity: 0.9
    }).addTo(recordMap).bindPopup(`<b>${place.name}</b><br>日期: ${place.date}`)
  })
  setTimeout(() => recordMap.invalidateSize(), 200)
}
</script>

<template>
  <!-- ================= 星露谷环球旅行背景 ================= -->
  <div class="stardew-bg">
    <!-- 天空、太阳与云朵 -->
    <div class="sky-layer">
      <div class="sun"></div>
      <div class="cloud c1"></div>
      <div class="cloud c2"></div>
    </div>
    
    <!-- 远处的世界景点（带柔光） -->
    <div class="landmark-layer">
      <!-- 富士山 -->
      <div class="landmark mt-fuji">
        <div class="snow-cap"></div>
      </div>
      <!-- 埃菲尔铁塔 -->
      <div class="landmark eiffel">
        <div class="body"></div>
        <div class="cross"></div>
      </div>
      <!-- 自由女神像 -->
      <div class="landmark liberty">
        <div class="torch"></div>
        <div class="body"></div>
        <div class="base"></div>
      </div>
      <!-- 埃及金字塔 -->
      <div class="landmark pyramid p1"></div>
      <div class="landmark pyramid p2"></div>
      <!-- 荷兰风车 -->
      <div class="landmark windmill">
        <div class="house"></div>
        <div class="blades"></div>
      </div>
    </div>

    <!-- 近处的森林、栅栏与草地 -->
    <div class="ground-layer">
      <div class="tree-bg t1"></div>
      <div class="tree-bg t2"></div>
      <div class="tree-bg t3"></div>
      <div class="fence"></div>
      
      <!-- 游荡的小鸡 -->
      <div class="chicken">
        <div class="chicken-body"></div>
        <div class="chicken-head"></div>
      </div>
    </div>
  </div>

  <div class="pixel-app">
    <!-- ================= 右上角悬浮小人 ================= -->
    <div v-if="currentView === 'home'" class="avatar-container" @click="currentView = 'avatar'">
      <div class="css-pixel-body">
        <div class="head" :style="{ backgroundColor: avatar.faceColor }">
          <div class="hair" :style="{ backgroundColor: avatar.hairColor }"></div>
          <div class="eyes"><div class="eye"></div><div class="eye"></div></div>
        </div>
        <div class="torso" :style="{ backgroundColor: avatar.clothColor }">
          <div class="arm left" :style="{ backgroundColor: avatar.clothColor }"></div>
          <div class="arm right" :style="{ backgroundColor: avatar.clothColor }"></div>
        </div>
      </div>
      <div class="avatar-name">{{ avatar.name }}</div>
    </div>

    <!-- ================= 主页面 (Home) ================= -->
    <div v-if="currentView === 'home'" class="home-view">
      <h1 class="pixel-title">欢迎回来，{{ avatar.name }}!</h1>
      
      <div class="ticket-container">
        <div class="boarding-pass" @click="currentView = 'planner'">
          <div class="bp-left">
            <div class="bp-header">BOARDING PASS</div>
            <div class="bp-route"><span class="city">HOME</span><span class="plane-icon">✈</span><span class="city">DREAM</span></div>
            <div class="bp-info">新建旅行计划 / 选人格生成</div>
          </div>
          <div class="bp-right"><div class="barcode"></div><div class="flight-no">FLT 001</div></div>
        </div>

        <div class="boarding-pass" @click="currentView = 'upcoming'">
          <div class="bp-left">
            <div class="bp-header">BOARDING PASS</div>
            <div class="bp-route"><span class="city">HOME</span><span class="plane-icon">✈</span><span class="city">KYOTO</span></div>
            <div class="bp-info">即将出发 / 清单·交通·酒店</div>
          </div>
          <div class="bp-right"><div class="barcode"></div><div class="flight-no">FLT 002</div></div>
        </div>

        <div class="boarding-pass" @click="currentView = 'record'">
          <div class="bp-left">
            <div class="bp-header">BOARDING PASS</div>
            <div class="bp-route"><span class="city">PAST</span><span class="plane-icon">✈</span><span class="city">MEMORY</span></div>
            <div class="bp-info">旅行记录 / 点亮世界地图</div>
          </div>
          <div class="bp-right"><div class="barcode"></div><div class="flight-no">FLT 003</div></div>
        </div>
      </div>
    </div>

    <!-- ================= 捏人页面 ================= -->
    <div v-if="currentView === 'avatar'" class="sub-view avatar-view">
      <button class="back-btn" @click="currentView = 'home'">⬅ 返回主页</button>
      <h2 class="pixel-title">设计你的专属向导</h2>

      <div class="avatar-stage">
        <div v-if="generatingAvatar" class="loading-spinner">
          ✨ 正在提取色彩...<br/>
        </div>
        
        <template v-else>
          <div class="css-pixel-body large">
            <div class="head" :style="{ backgroundColor: avatar.faceColor }">
              <div class="hair" :style="{ backgroundColor: avatar.hairColor }"></div>
              <div class="eyes"><div class="eye"></div><div class="eye"></div></div>
            </div>
            <div class="torso" :style="{ backgroundColor: avatar.clothColor }">
              <div class="arm left" :style="{ backgroundColor: avatar.clothColor }"></div>
              <div class="arm right" :style="{ backgroundColor: avatar.clothColor }"></div>
            </div>
          </div>
        </template>

        <div class="name-input-row">
          <label>向导名字：</label>
          <input v-model="avatar.name" @change="saveAvatar" class="pixel-input" />
        </div>
        
        <div class="action-buttons">
          <button class="pixel-btn upload-btn" @click="showUploadModal = true" :disabled="generatingAvatar">📷 照片提取颜色</button>
          <button v-if="hasCustomImage && !generatingAvatar" class="pixel-btn danger" @click="hasCustomImage = false; avatar.hairColor = '#5C4033'; saveAvatar()">🗑️ 恢复默认</button>
        </div>
      </div>
    </div>

    <!-- 弹窗等其余组件 -->
    <div v-if="showUploadModal" class="modal-overlay" @click.self="showUploadModal = false">
      <div class="pixel-modal">
        <h3>上传照片</h3>
        <p style="font-size: 12px; color: #666; margin-bottom: 15px;">系统会自动提取照片中的主色调，作为像素小人的新发色。</p>
        <input type="file" accept="image/*" @change="handlePhotoUpload" class="pixel-input" />
        <button class="pixel-btn" style="margin-top: 15px;" @click="showUploadModal = false">取消</button>
      </div>
    </div>

    <!-- 模块 1：新建旅行计划 -->
    <div v-if="currentView === 'planner'" class="sub-view">
      <button class="back-btn" @click="currentView = 'home'">⬅ 返回主页</button>
      <h2 class="pixel-title">新建旅行计划</h2>
      
      <div class="planner-inputs">
        <input v-model="destination" placeholder="目的地" class="pixel-input" />
        <input v-model.number="days" type="number" class="pixel-input" style="width: 80px;" />
        <input v-model.number="budget" type="number" class="pixel-input" style="width: 120px;" />
        <select v-model="persona" class="pixel-input">
          <option v-for="p in personas" :key="p" :value="p">{{ p }}</option>
        </select>
        <button class="pixel-btn generate-btn" @click="generate" :disabled="loading">
          {{ loading ? '生成中...' : '生成计划' }}
        </button>
      </div>

      <div class="planner-content" v-if="result">
        <div class="schedule-list">
          <h3>{{ result.destination }} · {{ result.persona }}</h3>
          <p style="margin-bottom: 15px;">{{ result.persona_notes }}</p>
          <div v-for="(day, dIdx) in result.daily_plans" :key="dIdx" class="day-block">
            <h4>Day {{ day.day }}：{{ day.theme }}</h4>
            <div v-for="(item, sIdx) in day.schedule" :key="sIdx" class="schedule-item">
              <span class="time">{{ item.time }}</span>
              <div class="poi-info">
                <strong>{{ item.poi.name }}</strong>
              </div>
              <button class="pixel-btn danger" @click="removePoi(dIdx, sIdx)">删除</button>
            </div>
            <div class="add-poi-row">
              <input v-model="newPoiTime" placeholder="时间" class="pixel-input" style="width: 80px;" />
              <input v-model="newPoiName" placeholder="地点名称" class="pixel-input" style="flex:1;" />
              <button class="pixel-btn success" @click="addPoi(dIdx)">添加</button>
            </div>
          </div>
        </div>
        <div class="map-box">
          <div ref="mapContainer" style="width:100%; height:100%;"></div>
        </div>
      </div>
    </div>

    <!-- 模块 2：即将出发 -->
    <div v-if="currentView === 'upcoming'" class="sub-view">
      <button class="back-btn" @click="currentView = 'home'">⬅ 返回主页</button>
      <h2 class="pixel-title">即将出发：京都之旅</h2>
      
      <div class="upcoming-grid">
        <div class="boarding-pass vertical">
          <div class="bp-header">CHECKLIST</div>
          <h3>📋 旅行清单</h3>
          <ul class="pixel-list">
            <li><input type="checkbox" checked> 护照 / 签证</li>
            <li><input type="checkbox"> 转换插头</li>
            <li><input type="checkbox"> 换洗衣服</li>
            <li><input type="checkbox"> 相机</li>
          </ul>
          <button class="pixel-btn" style="margin-top: 10px;">+ 添加物品</button>
        </div>
        
        <div class="boarding-pass vertical">
          <div class="bp-header">TRANSPORT & HOTEL</div>
          <h3>✈️ 交通 & 酒店</h3>
          <div class="info-row"><strong>航班：</strong> CA1234 (10:00)</div>
          <div class="info-row"><strong>酒店：</strong> 京都大和鲁内酒店</div>
          <div class="info-row"><strong>入住：</strong> 10月24日 - 10月27日</div>
          <button class="pixel-btn" style="margin-top: 10px;">+ 编辑信息</button>
        </div>

        <div class="boarding-pass full-width">
          <div class="bp-header">PLANNED SPOTS</div>
          <h3>📍 计划打卡点</h3>
          <div class="tag-group">
            <span class="pixel-tag">金阁寺</span>
            <span class="pixel-tag">清水寺</span>
            <span class="pixel-tag">伏见稻荷大社</span>
          </div>
          <button class="pixel-btn" style="margin-top: 10px;">+ 添加打卡点</button>
        </div>
      </div>
    </div>

    <!-- 模块 3：旅行记录 -->
    <div v-if="currentView === 'record'" class="sub-view">
      <button class="back-btn" @click="currentView = 'home'">⬅ 返回主页</button>
      <h2 class="pixel-title">我的旅行足迹</h2>
      
      <div class="record-layout">
        <div class="map-box record-map">
          <div ref="recordMapContainer" style="width:100%; height:100%;"></div>
        </div>
        
        <div class="diary-panel boarding-pass vertical">
          <div class="bp-header">TRAVEL DIARY</div>
          <h3>📖 旅行日记</h3>
          <div v-for="(place, idx) in visitedPlaces" :key="idx" class="diary-card">
            <h4>{{ place.name }} <span class="date">{{ place.date }}</span></h4>
            <p>{{ place.diary }}</p>
          </div>
          <button class="pixel-btn" style="width: 100%; margin-top: 15px;">+ 写新日记</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
/* ================= 星露谷风格基础 ================= */
:root {
  --sky-top: #87CEEB;       
  --sky-bottom: #E0F7FA;    
  --grass-front: #7CB342;   
  --grass-back: #AED581;    
  --wood: #795548;          
  --pixel-border: #3E2723;  
  --pixel-primary: #FFB300; 
  --pixel-font: 'ZCOOL KuaiLe', 'Press Start 2P', sans-serif;
}

body {
  margin: 0; font-family: var(--pixel-font); color: var(--pixel-border);
  background-color: var(--sky-top); overflow-x: hidden; min-height: 100vh;
}

/* ================= 环球背景 ================= */
.stardew-bg {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0; z-index: -1;
  overflow: hidden;
  background: linear-gradient(to bottom, var(--sky-top) 0%, var(--sky-bottom) 60%);
}

.sun { position: absolute; top: 5%; right: 15%; width: 60px; height: 60px; background: #FFD54F; border-radius: 50%; box-shadow: 0 0 20px #FFD54F, 0 0 40px #FFCA28; animation: pulse-sun 4s infinite alternate; }
@keyframes pulse-sun { from { transform: scale(1); } to { transform: scale(1.1); } }

.cloud { position: absolute; background: #fff; border-radius: 10px; box-shadow: 8px 8px 0 rgba(0,0,0,0.05); }
.cloud::before, .cloud::after { content: ''; position: absolute; background: #fff; border-radius: 50%; }
.c1 { width: 100px; height: 30px; top: 15%; left: 10%; animation: float 25s infinite linear; }
.c1::before { width: 50px; height: 50px; top: -25px; left: 15px; }
.c1::after { width: 40px; height: 40px; top: -15px; right: 15px; }
.c2 { width: 80px; height: 25px; top: 25%; right: 25%; animation: float 20s infinite linear reverse; }
.c2::before { width: 40px; height: 40px; top: -20px; left: 10px; }
@keyframes float { 0% { transform: translateX(-50px); } 100% { transform: translateX(100vw); } }

/* ================= 世界景点图层 ================= */
.landmark-layer {
  position: absolute; bottom: 150px; width: 100%; height: 300px;
  filter: brightness(1.1) contrast(0.9) drop-shadow(0 10px 0 rgba(0,0,0,0.1));
  opacity: 0.8; /* 融入背景，不抢 UI 风头 */
}

.landmark { position: absolute; bottom: 0; }

/* 富士山 */
.mt-fuji { left: 5%; width: 0; height: 0; border-left: 120px solid transparent; border-right: 120px solid transparent; border-bottom: 180px solid #78909C; }
.mt-fuji .snow-cap { position: absolute; left: -40px; top: 0; width: 0; height: 0; border-left: 40px solid transparent; border-right: 40px solid transparent; border-bottom: 60px solid #FFF; }

/* 埃菲尔铁塔 */
.eiffel { left: 25%; width: 40px; height: 160px; background: #5D4037; clip-path: polygon(50% 0, 100% 100%, 0 100%); }
.eiffel .body { position: absolute; bottom: 0; left: 10px; width: 20px; height: 100px; background: #5D4037; }
.eiffel .cross { position: absolute; top: 20px; left: 5px; width: 30px; height: 6px; background: #5D4037; }

/* 自由女神 */
.liberty { left: 55%; width: 50px; height: 170px; }
.liberty .torch { position: absolute; top: 0; right: 10px; width: 12px; height: 40px; background: #FFB300; border-radius: 4px; box-shadow: 0 0 15px #FFB300; }
.liberty .body { position: absolute; bottom: 20px; left: 5px; width: 40px; height: 110px; background: #80CBC4; clip-path: polygon(20% 0, 80% 0, 100% 100%, 0 100%); }
.liberty .base { position: absolute; bottom: 0; left: -10px; width: 70px; height: 20px; background: #A1887F; }

/* 金字塔 */
.pyramid { width: 0; height: 0; border-left: 80px solid transparent; border-right: 80px solid transparent; border-bottom: 100px solid #FFCA28; }
.p1 { left: 70%; }
.p2 { left: 78%; border-left-width: 60px; border-right-width: 60px; border-bottom-width: 80px; border-bottom-color: #FFB300; }

/* 风车 */
.windmill { right: 5%; width: 60px; height: 120px; }
.windmill .house { position: absolute; bottom: 0; left: 10px; width: 40px; height: 80px; background: #D7CCC8; clip-path: polygon(50% 0, 100% 30%, 100% 100%, 0 100%, 0 30%); }
.windmill .blades { position: absolute; top: 10px; left: 30px; width: 80px; height: 10px; background: #fff; border: 3px solid var(--pixel-border); animation: spin 5s infinite linear; transform-origin: 0 50%; }
.windmill .blades::before { content: ''; position: absolute; top: -30px; left: 30px; width: 10px; height: 70px; background: #fff; border: 3px solid var(--pixel-border); }
@keyframes spin { 100% { transform: rotate(360deg); } }

/* ================= 近景大地 ================= */
.ground-layer { position: absolute; bottom: 0; width: 100%; height: 150px; background: var(--grass-front); border-top: 6px solid var(--wood); box-shadow: 0 -10px 0 rgba(0,0,0,0.1); z-index: 2; }
.ground-layer::before { content: ''; position: absolute; top: 10px; left: 0; width: 100%; height: 100%; background-image: radial-gradient(var(--grass-back) 2px, transparent 2px); background-size: 20px 20px; }

.tree-bg { position: absolute; bottom: 120px; width: 30px; height: 70px; background: var(--wood); border: 4px solid var(--pixel-border); z-index: 3; }
.tree-bg::before { content: ''; position: absolute; top: -60px; left: -35px; width: 100px; height: 100px; background: #558B2F; border-radius: 20% 20% 50% 50%; border: 4px solid var(--pixel-border); box-shadow: inset -10px -10px 0 rgba(0,0,0,0.2), 0 10px 0 rgba(0,0,0,0.1); }
.t1 { left: 2%; transform: scale(1.2); }
.t2 { right: 2%; transform: scale(1); }

.fence { position: absolute; bottom: 0; left: 0; width: 100%; height: 50px; background: repeating-linear-gradient(90deg, transparent, transparent 30px, var(--wood) 30px, var(--wood) 40px); z-index: 4; }
.fence::after { content: ''; position: absolute; top: 15px; left: 0; width: 100%; height: 10px; background: var(--wood); border-top: 4px solid var(--pixel-border); border-bottom: 4px solid var(--pixel-border); }

/* 走动的小鸡 */
.chicken { position: absolute; bottom: 20px; left: 10%; width: 30px; height: 25px; animation: walk-chicken 15s infinite linear; z-index: 5; }
.chicken-body { position: absolute; bottom: 0; left: 0; width: 25px; height: 18px; background: #FFF; border: 3px solid var(--pixel-border); border-radius: 50% 50% 20% 20%; }
.chicken-head { position: absolute; top: 0; right: 0; width: 15px; height: 15px; background: #FFF; border: 3px solid var(--pixel-border); border-radius: 50%; }
.chicken-head::after { content: ''; position: absolute; top: -6px; left: 2px; width: 6px; height: 6px; background: #F44336; border: 2px solid var(--pixel-border); }
@keyframes walk-chicken { 0% { transform: translateX(0) scaleX(1); } 45% { transform: translateX(200px) scaleX(1); } 50% { transform: translateX(200px) scaleX(-1); } 95% { transform: translateX(0) scaleX(-1); } 100% { transform: translateX(0) scaleX(1); } }


/* ================= UI 组件（保持清新） ================= */
.pixel-app { max-width: 1200px; margin: 0 auto; padding: 20px; position: relative; z-index: 10; }
.pixel-title { text-align: center; font-size: 40px; color: #fff; text-shadow: 3px 3px 0px var(--pixel-border), 6px 6px 0px rgba(0,0,0,0.2); letter-spacing: 2px; margin-bottom: 40px; }
.pixel-input { border: 4px solid var(--pixel-border); background: #fff; padding: 10px 14px; font-family: inherit; font-size: 16px; outline: none; border-radius: 8px; box-shadow: 4px 4px 0px rgba(0,0,0,0.15); }
.pixel-btn { background: #fff; border: 4px solid var(--pixel-border); padding: 10px 20px; font-family: inherit; font-weight: bold; font-size: 16px; cursor: pointer; border-radius: 8px; box-shadow: 4px 4px 0px rgba(0,0,0,0.15); transition: all 0.1s; }
.pixel-btn:active { transform: translate(4px, 4px); box-shadow: 0px 0px 0px rgba(0,0,0,0.15); }
.pixel-btn:disabled { background: #eee; cursor: not-allowed; color: #999; }
.pixel-btn.danger { background: #FFCDD2; color: #B71C1C; }
.pixel-btn.success { background: #C8E6C9; color: #1B5E20; }
.pixel-btn.generate-btn { background: var(--pixel-primary); color: #fff; }

/* 捏人页面 */
.avatar-view { display: flex; flex-direction: column; align-items: center; }
.avatar-stage { display: flex; flex-direction: column; align-items: center; background: #fff; border: 4px solid var(--pixel-border); padding: 40px; box-shadow: 8px 8px 0px var(--wood); margin-bottom: 20px; width: 100%; max-width: 500px; border-radius: 16px; }
.name-input-row { display: flex; align-items: center; gap: 15px; margin-top: 20px; font-weight: bold; font-size: 18px; }
.action-buttons { display: flex; gap: 15px; margin-top: 30px; flex-wrap: wrap; justify-content: center; }
.loading-spinner { width: 200px; height: 200px; display: flex; justify-content: center; align-items: center; text-align: center; border: 4px dashed var(--pixel-primary); color: var(--pixel-border); font-weight: bold; margin-bottom: 20px; animation: pulse 1.5s infinite; padding: 10px; background: #fff; border-radius: 10px; }
@keyframes pulse { 0% { transform: scale(0.95); } 50% { transform: scale(1.05); } 100% { transform: scale(0.95); } }

/* 机票 */
.ticket-container { display: flex; flex-direction: column; gap: 25px; max-width: 800px; margin: 40px auto; }
.boarding-pass { display: flex; background: rgba(255,255,255,0.95); border: 4px solid var(--pixel-border); cursor: pointer; transition: transform 0.1s; position: relative; overflow: hidden; box-shadow: 8px 8px 0px rgba(0,0,0,0.2); border-radius: 12px; backdrop-filter: blur(5px); }
.boarding-pass:hover { transform: translate(-4px, -4px); box-shadow: 12px 12px 0px rgba(0,0,0,0.2); }
.bp-left { flex: 1; padding: 24px; border-right: 4px dashed #ddd; position: relative; }
.bp-left::before, .bp-left::after { content: ''; position: absolute; right: -14px; width: 20px; height: 20px; background: var(--grass-front); border: 4px solid var(--pixel-border); border-radius: 50%; }
.bp-left::before { top: -14px; }
.bp-left::after { bottom: -14px; }
.bp-right { width: 160px; padding: 20px; display: flex; flex-direction: column; justify-content: center; align-items: center; background: #fafafa; }
.bp-header { font-size: 14px; color: #888; letter-spacing: 2px; margin-bottom: 20px; font-weight: bold; }
.bp-route { display: flex; justify-content: space-between; align-items: center; font-size: 28px; font-weight: bold; margin-bottom: 20px; }
.bp-route .plane-icon { font-size: 32px; color: var(--pixel-primary); }
.bp-info { font-size: 16px; color: #555; }
.barcode { width: 90px; height: 60px; background: repeating-linear-gradient(90deg, var(--pixel-border), var(--pixel-border) 3px, #fff 3px, #fff 6px, var(--pixel-border) 6px, var(--pixel-border) 9px); margin-bottom: 15px; }
.flight-no { font-size: 16px; font-weight: bold; }
.boarding-pass.vertical { flex-direction: column; cursor: default; border-radius: 12px; }
.boarding-pass.vertical:hover { transform: none; box-shadow: 8px 8px 0px rgba(0,0,0,0.2); }
.boarding-pass.vertical .bp-header { border-bottom: 2px dashed #ddd; padding-bottom: 10px; margin-bottom: 15px; }
.boarding-pass.full-width { grid-column: 1 / -1; }

/* 右上角悬浮小人 */
.avatar-container { position: fixed; top: 30px; right: 30px; text-align: center; cursor: pointer; z-index: 100; display: flex; flex-direction: column; align-items: center; background: rgba(255,255,255,0.95); padding: 15px; border: 4px solid var(--pixel-border); box-shadow: 6px 6px 0px var(--wood); border-radius: 16px; backdrop-filter: blur(4px); }
.avatar-name { background: var(--pixel-border); color: #fff; padding: 6px 14px; font-size: 14px; margin-top: 10px; border-radius: 6px; white-space: nowrap; }

/* CSS 像素小人 */
.css-pixel-body { width: 60px; height: 110px; display: flex; flex-direction: column; align-items: center; position: relative; }
.css-pixel-body.large { transform: scale(2.5); margin: 60px 0 40px 0; }
.css-pixel-body .head { width: 48px; height: 48px; border: 4px solid var(--pixel-border); border-radius: 8px; position: relative; z-index: 2; }
.css-pixel-body .hair { position: absolute; top: -4px; left: -4px; right: -4px; height: 24px; border: 4px solid var(--pixel-border); border-radius: 8px 8px 0 0; border-bottom: none; }
.css-pixel-body .eyes { display: flex; justify-content: space-around; margin-top: 18px; }
.css-pixel-body .eye { width: 6px; height: 6px; background: var(--pixel-border); }
.css-pixel-body .torso { width: 52px; height: 56px; border: 4px solid var(--pixel-border); border-radius: 8px; margin-top: -4px; z-index: 1; position: relative; }
.css-pixel-body .arm { position: absolute; top: 0; width: 14px; height: 40px; border: 4px solid var(--pixel-border); }
.css-pixel-body .arm.left { left: -18px; border-radius: 6px 0 0 6px; }
.css-pixel-body .arm.right { right: -18px; border-radius: 0 6px 6px 0; }

/* 其他页面组件 */
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.4); display: flex; justify-content: center; align-items: center; z-index: 200; }
.pixel-modal { background: #fff; border: 4px solid var(--pixel-border); padding: 24px; width: 320px; box-shadow: 8px 8px 0px var(--pixel-primary); border-radius: 12px; }
.sub-view { margin-top: 20px; }
.back-btn { background: #fff; border: 4px solid var(--pixel-border); padding: 8px 16px; font-family: inherit; font-size: 16px; font-weight: bold; cursor: pointer; margin-bottom: 20px; box-shadow: 4px 4px 0px rgba(0,0,0,0.1); border-radius: 8px; }
.back-btn:active { transform: translate(4px, 4px); box-shadow: none; }
.planner-inputs { display: flex; gap: 15px; flex-wrap: wrap; margin-bottom: 30px; background: rgba(255,255,255,0.95); padding: 20px; border: 4px solid var(--pixel-border); box-shadow: 8px 8px 0px rgba(0,0,0,0.1); border-radius: 12px; }
.planner-content { display: flex; gap: 20px; flex-wrap: wrap; }
.schedule-list { flex: 1; min-width: 350px; }
.map-box { flex: 1; min-width: 350px; height: 600px; border: 4px solid var(--pixel-border); box-shadow: 8px 8px 0px var(--wood); border-radius: 12px; overflow: hidden; background: #fff; }
.day-block { border: 4px dashed #B2EBF2; padding: 15px; margin-bottom: 20px; background: #fff; border-radius: 12px; }
.schedule-item { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; background: #F0FDF4; padding: 10px; border: 3px solid var(--pixel-border); box-shadow: 3px 3px 0px rgba(0,0,0,0.1); border-radius: 8px; }
.schedule-item .time { font-weight: bold; width: 50px; color: var(--pixel-primary); }
.schedule-item .poi-info { flex: 1; }
.add-poi-row { display: flex; gap: 10px; margin-top: 15px; }
.pixel-badge { background: var(--pixel-primary); color: #fff; padding: 4px 8px; font-size: 13px; border: 3px solid var(--pixel-border); white-space: nowrap; box-shadow: 3px 3px 0px rgba(0,0,0,0.2); border-radius: 6px; }
.upcoming-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.pixel-list { list-style: none; padding: 0; }
.pixel-list li { margin-bottom: 12px; font-size: 16px; }
.info-row { margin-bottom: 12px; font-size: 16px; }
.pixel-tag { display: inline-block; background: #B2EBF2; border: 3px solid var(--pixel-border); padding: 4px 10px; margin: 5px; font-size: 14px; font-weight: bold; border-radius: 8px; }
.record-layout { display: flex; gap: 20px; flex-wrap: wrap; }
.record-map { flex: 2; height: 500px; }
.diary-panel { flex: 1; min-width: 300px; background: rgba(255,255,255,0.95); padding: 20px; border: 4px solid var(--pixel-border); box-shadow: 8px 8px 0px var(--wood); border-radius: 12px; }
.diary-card { border-bottom: 3px dashed #ddd; padding-bottom: 15px; margin-bottom: 15px; }
.diary-card h4 { margin: 0 0 8px 0; display: flex; justify-content: space-between; font-size: 18px; color: var(--pixel-primary); }
.diary-card .date { font-size: 12px; color: #888; }
</style>