import streamlit as st
import requests
import base64
import os
import random
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ==================== 1. 系统级配置与液态玻璃全局 UI ====================
st.set_page_config(page_title="智能影像生成控制台", layout="centered")

# 注入至尊液态玻璃 (Glassmorphism) 专属 CSS 样式
st.markdown("""
<style>
    /* 1. 铺设液态玻璃必需的幽邃数字渐变背景底色 */
    .stApp {
        background: radial-gradient(circle at 90% 10%, rgba(30, 50, 100, 1) 0%, rgba(10, 15, 30, 1) 60%) !important;
        color: #e2e8f0 !important;
    }

    /* 2. 输入框、下拉菜单、高级面板全部液态玻璃化 */
    .stTextArea textarea, .stTextInput input, .stSelectbox select, .stDetails {
        background: rgba(255, 255, 255, 0.04) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        color: #ffffff !important;
        border-radius: 12px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2) !important;
    }
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: rgba(0, 236, 255, 0.5) !important;
        box-shadow: 0 0 10px rgba(0, 236, 255, 0.2) !important;
    }

    /* 3. 霓虹液态微光按钮 */
    .stButton>button {
        border-radius: 10px !important;
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(8px) !important;
        -webkit-backdrop-filter: blur(8px) !important;
        color: #00ecff !important;
        border: 1px solid rgba(0, 236, 255, 0.15) !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        background: rgba(0, 236, 255, 0.1) !important;
        box-shadow: 0 0 18px rgba(0, 236, 255, 0.4) !important;
        border-color: #00ecff !important;
        color: #ffffff !important;
        transform: translateY(-1px);
    }

    /* 4. 主提交按钮高亮液态渐变 */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, rgba(0, 198, 255, 0.4) 0%, rgba(0, 114, 255, 0.4) 100%) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        color: white !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, rgba(0, 198, 255, 0.6) 0%, rgba(0, 114, 255, 0.6) 100%) !important;
        box-shadow: 0 0 25px rgba(0, 114, 255, 0.6) !important;
    }

    /* 5. 历史卡片晶莹美化 */
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column"] {
        background: rgba(255, 255, 255, 0.02) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.04) !important;
        border-radius: 12px;
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 2. 核心：隐形签名持久化隔离中枢 ====================
# 如果当前用户的浏览器是第一次打开，为其生成一个永久的独立设备标签，存在会话中
if "user_device_id" not in st.session_state:
    # 巧妙利用服务器端的隐形钥匙文件，如果是新访客就发个新钥匙
    st.session_state.user_device_id = str(uuid.uuid4())[:8]

# 根据这个浏览器的无感钥匙，创建它专属的服务器隐藏卡槽
USER_DIR = os.path.join("image_cache", f"user_{st.session_state.user_device_id}")
MANIFEST_FILE = os.path.join(USER_DIR, "manifest.json")

if not os.path.exists(USER_DIR):
    os.makedirs(USER_DIR)

def load_manifest():
    if os.path.exists(MANIFEST_FILE):
        try:
            with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_manifest(data):
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 状态变量初始化
if "current_placeholder" not in st.session_state:
    st.session_state.current_placeholder = "点击下方按钮获取灵感，或在此直接输入您的创意描述..."
if "is_loading" not in st.session_state:
    st.session_state.is_loading = False
if "input_text_value" not in st.session_state:
    st.session_state.input_text_value = ""

if st.session_state.input_text_value:
    st.session_state.current_placeholder = st.session_state.input_text_value
    st.session_state.input_text_value = ""

IMAGE_API_KEY = os.getenv("MY_IMAGE_API_KEY")
CHAT_API_KEY = os.getenv("MY_CHAT_API_KEY")

URL_GEN = "https://nowcoding.ai/v1/images/generations"
URL_CHAT = "https://nowcoding.ai/v1/chat/completions"

# ==================== 3. 大模型工具函数 ====================
def get_random_prompt_from_cloud(api_key):
    themes = ["古代国风水墨", "大自然与写实摄影", "欧洲魔幻奇幻", "复古温馨胶片", "童话治愈插画", "野生动物史诗"]
    chosen_theme = random.choice(themes)
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "gpt-5.4-mini",
        "messages": [
            {"role": "system", "content": "你是一个充满想象力的顶级AI绘画提示词专家。"},
            {"role": "user", "content": f"请为我定制一条AI绘图提示词。主题：【{chosen_theme}】。要求：不出现赛博朋克、机甲。直接输出内容，不要废话，60字内，中文。"}
        ],
        "temperature": 1.0
    }
    try:
        res = requests.post(URL_CHAT, headers=headers, json=payload, timeout=10)
        return res.json()["choices"][0]["message"]["content"].strip() if res.status_code == 200 else "灵感检索失败"
    except:
        return "服务器连接超时"

def translate_and_optimize_prompt(api_key, user_prompt):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "gpt-5.4-mini",
        "messages": [
            {"role": "system", "content": "You are a master of AI art prompts, skilled in Midjourney and DALL-E 3 syntax."},
            {"role": "user", "content": f"请把这句中文提示词翻译成高阶英文绘图咒语：'{user_prompt}'。扩充细节，加入光影、镜头修饰词。直接输出最终的英文提示词，绝对不含中文和解释。"}
        ],
        "temperature": 0.7
    }
    try:
        res = requests.post(URL_CHAT, headers=headers, json=payload, timeout=10)
        return res.json()["choices"][0]["message"]["content"].strip() if res.status_code == 200 else user_prompt
    except:
        return user_prompt

# ==================== 4. 液态玻璃美学横幅与主页面 ====================
st.markdown("""
<div style="background: linear-gradient(135deg, rgba(255, 255, 255, 0.07) 0%, rgba(255, 255, 255, 0.01) 100%); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); padding: 25px; border-radius: 16px; margin-bottom: 25px; border: 1px solid rgba(255, 255, 255, 0.12); box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);">
    <h2 style="color: #ffffff; margin: 0; text-align: center; font-family: 'Segoe UI', Arial; letter-spacing: 2px; font-weight: 600;">AIGC 智能影像生成控制台</h2>
    <p style="color: #00ecff; margin: 5px 0 0 0; text-align: center; font-size: 13px; font-weight: bold; letter-spacing: 1px;">PREMIUM PRODUCTION WORKSTATION · 液态玻璃私密版</p>
</div>
""", unsafe_allow_html=True)

col_btn1, col_btn2 = st.columns([1, 1])
with col_btn1:
    if st.button("🎲 获取随机灵感创意", disabled=st.session_state.is_loading, use_container_width=True):
        st.session_state.is_loading = True
        with st.spinner("📊 正在检索创意数据库并构建核心提示词..."):
            st.session_state.current_placeholder = get_random_prompt_from_cloud(CHAT_API_KEY)
        st.session_state.is_loading = False
        st.rerun()
with col_btn2:
    enable_translate = st.toggle("🌐 开启中译英智能咒语优化引擎", value=True)

prompt = st.text_area("核心图像描述 (支持中文及英文):", placeholder=st.session_state.current_placeholder, height=100)

st.write("🎨 **艺术风格大调色盘 (一键加缀大师级艺术滤镜):**")
style_list = {
    "✨ 无滤镜自由发挥": "",
    "🎬 电影级纪实感": ", cinematic lighting, 35mm photograph, dramatic lighting, shot on IMAX, depth of field, masterwork",
    "🍃 宫崎骏动漫风": ", Studio Ghibli style, beautiful anime aesthetic, hand-drawn illustration, vibrant colors",
    "💻 赛博朋克风": ", cyberpunk style, neon glowing, rainy night streets with reflections, holographic projections",
    "🌻 梵高后印象派": ", oil on canvas in Vincent van Gogh style, thick textured brush strokes, vibrant swirling colors",
    "🖋️ 传统国风写意": ", traditional Chinese ink wash painting, ethereal watercolor wash, elegant brush strokes, zen",
    "🎞️ 90年代黑白胶片": ", 1990s monochrome film photography, black and white, classic cinematic grain, high contrast"
}
chosen_style = st.selectbox("选择期望追加的视觉艺术风格：", list(style_list.keys()))

with st.expander("🛠️ 影像精细化渲染高级控制面板", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        aspect_ratio = st.selectbox("📐 图像构图画幅比例：", ["1:1 标准方形 (1024x1024)", "16:9 宽银幕壁纸 (1024x576)", "9:16 移动端海报 (576x1024)"])
    with col2:
        quality = st.selectbox("🎭 影像生成质量：", ["standard", "hd"])
    negative_prompt = st.text_input("🚫 负向提示词 (排除画面多余元素):", placeholder="例如：变形、低画质、模糊")
    st.markdown("---")
    use_seed = st.checkbox("固定特征种子 (开启后可微调文字进行画面连贯创作)", value=False)
    custom_seed = st.number_input("设置固定的随机种子数值：", min_value=1, max_value=9999999, value=88888)

size_mapping = {"1:1 标准方形 (1024x1024)": "1024x1024", "16:9 宽银幕壁纸 (1024x576)": "1024x576", "9:16 移动端海报 (576x1024)": "576x1024"}
chosen_size = size_mapping[aspect_ratio]

# ==================== 5. 影像渲染与无感缓存 ====================
action_col1, action_col2 = st.columns(2)

with action_col1:
    if st.button("开始构建单张影像 ✨", type="primary", use_container_width=True):
        if not user_input_prompt:
            st.warning("系统提示：当前输入为空！")
        else:
            display_prompt = user_input_prompt
            with st.spinner("🌐 正在进化为高阶艺术英文咒语..."):
                if enable_translate: user_input_prompt = translate_and_optimize_prompt(CHAT_API_KEY, user_input_prompt)
                user_input_prompt += style_list[chosen_style]

            with st.spinner("AI 正在绘制影像..."):
                payload = {"model": "gpt-image-2", "prompt": user_input_prompt, "n": 1, "size": chosen_size, "quality": quality}
                if negative_prompt: payload["negative_prompt"] = negative_prompt
                if use_seed: payload["seed"] = custom_seed
                
                headers = {"Authorization": f"Bearer {IMAGE_API_KEY}", "User-Agent": "Mozilla/5.0"}
                try:
                    res = requests.post(URL_GEN, headers=headers, json=payload)
                    if res.status_code == 200:
                        b64 = res.json()["data"][0]["b64_json"]
                        img_bytes = base64.b64decode(b64)
                        
                        st.success("✨ 核心影像构建完成！")
                        st.image(img_bytes, caption="当前生成的影像结果", use_container_width=True)
                        
                        # 无感持久化落盘
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                        filename = f"img_{timestamp}.png"
                        filepath = os.path.join(USER_DIR, filename)
                        with open(filepath, "wb") as f: f.write(img_bytes)
                        
                        manifest = load_manifest()
                        style_label = chosen_style.split(" ")[0] if chosen_style else "✨ 无滤镜"
                        manifest.insert(0, {"id": timestamp, "filename": filename, "prompt": display_prompt, "style": style_label, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
                        save_manifest(manifest)
                        st.rerun()
                    else:
                        st.error(f"影像构建失败: {res.text}")
                except Exception as e:
                    st.error(f"发生错误: {e}")

with action_col2:
    if st.button("🎲 一键生成四种画风对比", use_container_width=True):
        if not user_input_prompt:
            st.warning("系统提示：请输入描述词！")
        else:
            display_prompt = user_input_prompt
            with st.spinner("🌐 统一解算语义中..."):
                if enable_translate: optimized_base = translate_and_optimize_prompt(CHAT_API_KEY, user_input_prompt)
                else: optimized_base = user_input_prompt

            st.info("🚀 风格对比矩阵已启动，正在并行渲染...")
            modes = [("🎬 电影纪实", style_list["🎬 电影级纪实感"]), ("🍃 宫崎动漫", style_list["🍃 宫崎骏动漫风"]), ("🖋️ 国风水墨", style_list["🖋️ 传统国风写意"]), ("🧸 皮克斯3D", style_list["🧸 皮克斯3D动画"])]
            
            for name, suffix in modes:
                with st.spinner(f"正在同步构建【{name}】影像..."):
                    payload = {"model": "gpt-image-2", "prompt": optimized_base + suffix, "n": 1, "size": chosen_size, "quality": quality}
                    if negative_prompt: payload["negative_prompt"] = negative_prompt
                    if use_seed: payload["seed"] = custom_seed
                    
                    res_bytes = send_image_request(payload)
                    if res_bytes:
                        save_asset_to_local(display_prompt, res_bytes, name)
            st.success("✨ 对比矩阵安全归廊！")
            st.rerun()

# ==================== 6. 隐形隔离私密画廊 ====================
manifest_data = load_manifest()
if manifest_data:
    st.markdown("---")
    st.markdown("### 📜 您的私人历史画廊 (设备专属留存)")
    cols = st.columns(2)
    for index, item in enumerate(manifest_data):
        filepath = os.path.join(USER_DIR, item["filename"])
        if os.path.exists(filepath):
            with cols[index % 2]:
                st.image(filepath, use_container_width=True)
                st.caption(f"🎨 [{item.get('style', '未分类')}] {item['prompt'][:18]}...")
                ctrl1, ctrl2 = st.columns(2)
                with ctrl1:
                    if st.button("🔄 回填", key=f"bk_{item['id']}"):
                        st.session_state.input_text_value = item["prompt"]
                        st.rerun()
                with ctrl2:
                    if st.button("🗑️ 删除", key=f"dl_{item['id']}"):
                        if os.path.exists(filepath): os.remove(filepath)
                        updated_manifest = [x for x in manifest_data if x["id"] != item["id"]]
                        save_manifest(updated_manifest)
                        st.rerun()
