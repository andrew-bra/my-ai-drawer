import streamlit as st
import requests
import base64
import os
import random
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ==================== 1. 系统级配置与会话缓存初始化 ====================
st.set_page_config(page_title="智能影像生成控制台", layout="centered")

# 注入 3.0 专属殿堂级暗黑科技 CSS 样式
st.markdown("""
<style>
    .stApp { background-color: #0b0f19 !important; color: #e2e8f0 !important; }
    .stButton>button {
        border-radius: 8px !important;
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
        color: #00ecff !important;
        border: 1px solid rgba(0, 236, 255, 0.2) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        font-weight: 500 !important;
    }
    .stButton>button:hover {
        box-shadow: 0 0 15px rgba(0, 236, 255, 0.6) !important;
        border-color: #00ecff !important;
        transform: translateY(-2px);
        color: #ffffff !important;
    }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #00c6ff 0%, #0072ff 100%) !important;
        color: white !important;
        border: none !important;
    }
    div.stButton > button[kind="primary"]:hover {
        box-shadow: 0 0 20px rgba(0, 114, 255, 0.8) !important;
    }
    .stTextArea textarea, .stTextInput input, .stSelectbox select {
        background-color: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #ffffff !important;
        border-radius: 8px !important;
    }
    .stTextArea textarea:focus {
        border-color: #00ecff !important;
        box-shadow: 0 0 8px rgba(0, 236, 255, 0.3) !important;
    }
    .stDetails {
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        background-color: rgba(15, 23, 42, 0.4) !important;
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# 核心：使用 session_state 进行基于浏览器会话的物理隔离缓存！
if "history_images" not in st.session_state:
    st.session_state.history_images = []  # 每个访客都会有一个独立的空列表
    
if "current_placeholder" not in st.session_state:
    st.session_state.current_placeholder = "点击下方按钮获取灵感，或在此直接输入您的创意描述..."
if "is_loading" not in st.session_state:
    st.session_state.is_loading = False
if "input_text_value" not in st.session_state:
    st.session_state.input_text_value = ""

# 响应历史词回填逻辑
if st.session_state.input_text_value:
    st.session_state.current_placeholder = st.session_state.input_text_value
    st.session_state.input_text_value = "" # 用完清空

IMAGE_API_KEY = os.getenv("MY_IMAGE_API_KEY")
CHAT_API_KEY = os.getenv("MY_CHAT_API_KEY")

if not IMAGE_API_KEY or not CHAT_API_KEY:
    st.error("系统错误：未检测到完整的 API Key 环境变量，请在 Secrets 中配置双密钥！")
    st.stop()

URL_GEN = "https://nowcoding.ai/v1/images/generations"
URL_CHAT = "https://nowcoding.ai/v1/chat/completions"

# ==================== 2. 核心大模型工具函数 ====================
def get_random_prompt_from_cloud(api_key):
    themes = [
        "古代国风水墨（如：侠客、竹林、红灯笼、泼墨山水、写意意境）",
        "大自然与写实摄影（如：微距露珠、深海鲸鱼、森林晨光、高清产品照、影棚布光）",
        "欧洲魔幻奇幻（如：独角兽、中世纪骑士、神秘城堡、飞龙翱翔、史诗级画质）",
        "复古温馨胶片（如：90年代老街、温馨午后、怀旧照、细腻颗粒感、暖色调）",
        "童话治愈插画（如：魔法森林、梦幻绘本风格、星空下的萤火虫、色彩斑斓）",
        "野生动物史诗（如：远古巨兽、雪原狼群、雄鹰展翅、震撼构图、纤毫毕现）"
    ]
    chosen_theme = random.choice(themes)

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "gpt-5.4-mini",
        "messages": [
            {"role": "system", "content": "你是一个充满想象力的顶级AI绘画提示词专家。"},
            {"role": "user", "content": f"请为我定制一条极具画面感、高质量的AI绘图提示词。今天指定的硬性主题是：【{chosen_theme}】。要求：必须严格围绕这个主题发挥，绝对不准出现任何赛博朋克、机甲、科幻、未来的元素！直接输出提示词内容，不要有任何废话解释，控制在60个字以内，必须是中文。"}
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
            {"role": "user", "content": f"请把这句中文提示词翻译成高阶英文绘图咒语：'{user_prompt}'。请扩充细节，加入专业的光影、镜头（如 volumetric lighting, cinematic, 8k, hyper-detailed）等艺术修饰词。注意：直接输出最终的英文提示词，绝对不要包含任何中文、不要有解释、不要带引号。"}
        ],
        "temperature": 0.7
    }
    try:
        res = requests.post(URL_CHAT, headers=headers, json=payload, timeout=10)
        return res.json()["choices"][0]["message"]["content"].strip() if res.status_code == 200 else user_prompt
    except:
        return user_prompt

# ==================== 3. 经典至尊版 UI ====================
st.markdown("""
<div style="background: linear-gradient(90deg, #0f2027 0%, #203a43 50%, #2c5364 100%); padding: 22px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
    <h2 style="color: white; margin: 0; text-align: center; font-family: Arial; letter-spacing: 2px;">AIGC 智能影像生成控制台</h2>
    <p style="color: #00ecff; margin: 5px 0 0 0; text-align: center; font-size: 13px; font-weight: bold;">PREMIUM COMPREHENSIVE PRODUCTION WORKSTATION · 至尊全功能版</p>
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

prompt = st.text_area(
    "核心图像描述 (支持中文及英文):", 
    placeholder=st.session_state.current_placeholder,
    height=100
)

st.write("🎨 **艺术风格大调色盘 (一键加缀大师级艺术滤镜):**")
style_list = {
    "✨ 无滤镜自由发挥": "",
    "🎬 电影级纪实感 (Cinematic, anamorphic lens, dramatic lighting)": ", cinematic lighting, 35mm photograph, dramatic lighting, shot on IMAX, depth of field, masterwork",
    "🍃 宫崎骏动漫风 (Studio Ghibli style, anime aesthetics)": ", Studio Ghibli style, beautiful anime aesthetic, hand-drawn illustration, vibrant colors, nostalgic atmosphere",
    "💻 赛博朋克风 (Cyberpunk, neon glowing, rainy night)": ", cyberpunk style, neon glowing, rainy night streets with reflections, holographic projections, futuristic high-tech",
    "🌻 梵高后印象派 (Vincent van Gogh style, thick brush strokes)": ", oil on canvas in Vincent van Gogh style, thick textured brush strokes, vibrant swirling colors, post-impressionism",
    "🖋️ 传统国风写意 (Traditional Chinese ink painting style)": ", traditional Chinese ink wash painting, ethereal watercolor wash, elegant brush strokes, artistic artistic concept, zen",
    "🧸 皮克斯3D动画 (Pixar 3D animation style, cute character design)": ", 3D animation character in Pixar style, Disney aesthetics, cute, highly detailed clay texture, soft studio illumination",
    "🎞️ 90年代黑白胶片 (1990s monochrome film style, classic grain)": ", 1990s monochrome film photography, black and white, classic cinematic grain, nostalgic atmosphere, high contrast"
}
chosen_style = st.selectbox("选择期望追加的视觉艺术风格：", list(style_list.keys()))

with st.expander("🛠️ 影像精细化渲染高级控制面板", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        aspect_ratio = st.selectbox("📐 图像构图画幅比例：", ["1:1 标准方形 (1024x1024)", "16:9 宽银幕壁纸 (1024x576)", "9:16 移动端海报 (576x1024)"])
    with col2:
        quality = st.selectbox("🎭 影像生成质量：", ["standard (标准影像)", "hd (超清影像增强)"])
        
    negative_prompt = st.text_input("🚫 负向提示词 (排除画面多余元素):", placeholder="例如：变形、低画质、崩坏的肢体、模糊、水印")
    
    st.markdown("---")
    use_seed = st.checkbox("固定特征种子 (开启后可微调文字进行画面连贯创作)", value=False)
    custom_seed = st.number_input("设置固定的随机种子数值：", min_value=1, max_value=9999999, value=88888)

size_mapping = {"1:1 标准方形 (1024x1024)": "1024x1024", "16:9 宽银幕壁纸 (1024x576)": "1024x576", "9:16 移动端海报 (576x1024)": "576x1024"}
chosen_size = size_mapping[aspect_ratio]

if st.button("开始构建影像 ✨", type="primary"):
    final_prompt = prompt if prompt else (None if st.session_state.current_placeholder.startswith("点击下方按钮") else st.session_state.current_placeholder)
    
    if not final_prompt:
        st.warning("系统提示：检测到当前输入内容为空，请填写描述词或获取灵感！")
    else:
        display_prompt = final_prompt
        
        with st.spinner("AI 正在执行底层逻辑运算，请稍候..."):
            if enable_translate:
                with st.spinner("🌐 正在将提示词进化为高阶艺术英文咒语..."):
                    final_prompt = translate_and_optimize_prompt(CHAT_API_KEY, final_prompt)
            final_prompt += style_list[chosen_style]

        with st.spinner("AI 正在解析多维向量并绘制影像，请稍候..."):
            payload = {
                "model": "gpt-image-2", 
                "prompt": final_prompt, 
                "n": 1, 
                "size": chosen_size,
                "quality": quality.split(" ")[0]
            }
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
                    st.download_button("⬇️ 下载当前高清原图", data=img_bytes, file_name="AIGC_Result.png", mime="image/png", type="primary")
                    
                    # 绝对隔离策略：存入当前用户的私人浏览器临时内存池中
                    style_label = chosen_style.split(" ")[0] if chosen_style else "✨ 无滤镜"
                    unique_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
                    st.session_state.history_images.insert(0, {
                        "id": unique_id,
                        "prompt": display_prompt,
                        "style": style_label,
                        "bytes": img_bytes
                    })
                else:
                    st.error(f"影像构建失败，状态码: {res.status_code} 原因: {res.text}")
            except Exception as e:
                st.error(f"网络计算节点发生错误: {e}")

# ==================== 6. 专属私密陈列室 (绝对隔离 + 删除功能) ====================
if st.session_state.history_images:
    st.markdown("---")
    st.markdown("### 📜 您的私密创作陈列室 (本次会话)")
    cols = st.columns(2)
    for index, item in enumerate(st.session_state.history_images):
        with cols[index % 2]:
            st.image(item["bytes"], use_container_width=True)
            st.caption(f"🎨 [{item['style']}] {item['prompt'][:18]}...")
            
            ctrl1, ctrl2 = st.columns(2)
            with ctrl1:
                # 提取回填按钮
                if st.button("🔄 回填", key=f"bk_{item['id']}"):
                    st.session_state.input_text_value = item["prompt"]
                    st.rerun()
            with ctrl2:
                # 删除按钮：仅从当前访客的私有内存列表中移除
                if st.button("🗑️ 删除", key=f"dl_{item['id']}"):
                    st.session_state.history_images = [x for x in st.session_state.history_images if x["id"] != item["id"]]
                    st.rerun()
