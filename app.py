import streamlit as st
import requests
import base64
import os
import random
from dotenv import load_dotenv

load_dotenv()

# ==================== 1. 系统级配置与暗黑全局美化 ====================
st.set_page_config(page_title="AIGC 智能影像生成终端", layout="centered")

# 注入殿堂级暗黑科技 CSS 样式
st.markdown("""
<style>
    /* 全局暗黑背景微调 */
    .stApp {
        background-color: #0b0f19 !important;
        color: #e2e8f0 !important;
    }
    /* 按钮高级霓虹发光与悬浮动效 */
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
    /* 主要提交按钮高亮 */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #00c6ff 0%, #0072ff 100%) !important;
        color: white !important;
        border: none !important;
    }
    div.stButton > button[kind="primary"]:hover {
        box-shadow: 0 0 20px rgba(0, 114, 255, 0.8) !important;
    }
    /* 输入框毛玻璃质感 */
    .stTextArea textarea, .stTextInput input, .stSelectbox cubic-bezier {
        background-color: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #ffffff !important;
        border-radius: 8px !important;
    }
    .stTextArea textarea:focus {
        border-color: #00ecff !important;
        box-shadow: 0 0 8px rgba(0, 236, 255, 0.3) !important;
    }
    /* 折叠面板美化 */
    .stDetails {
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        background-color: rgba(15, 23, 42, 0.4) !important;
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# 初始化系统级状态变量
if "current_placeholder" not in st.session_state:
    st.session_state.current_placeholder = "请输入创意描述..."
if "is_loading" not in st.session_state:
    st.session_state.is_loading = False
if "history_images" not in st.session_state:
    st.session_state.history_images = []
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
        "model": "gpt-5.3-codex",
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
        "model": "gpt-5.3-codex",
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

# 单张图片核心请求包装
def send_image_request(payload_data):
    headers = {"Authorization": f"Bearer {IMAGE_API_KEY}", "User-Agent": "Mozilla/5.0"}
    try:
        res = requests.post(URL_GEN, headers=headers, json=payload_data)
        if res.status_code == 200:
            return base64.b64decode(res.json()["data"][0]["b64_json"])
    except:
        pass
    return None

# ==================== 3. 页面视觉大横幅 ====================
st.markdown("""
<div style="background: linear-gradient(90deg, #020617 0%, #1e1b4b 50%, #030712 100%); padding: 25px; border-radius: 12px; margin-bottom: 25px; border: 1px solid rgba(99, 102, 241, 0.2); box-shadow: 0 4px 20px rgba(0,0,0,0.5);">
    <h2 style="color: #ffffff; margin: 0; text-align: center; font-family: 'Segoe UI', Arial; letter-spacing: 3px; font-weight: 700;">ART COGNITION TERMINAL</h2>
    <p style="color: #00ecff; margin: 6px 0 0 0; text-align: center; font-size: 13px; font-weight: 600; letter-spacing: 1px;">智能艺术协同终端 · 3.0 终极至尊版</p>
</div>
""", unsafe_allow_html=True)

# ==================== 4. 核心控制组件区 ====================
col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button("🎲 从云端库抓取随机灵感", disabled=st.session_state.is_loading, use_container_width=True):
        st.session_state.is_loading = True
        with st.spinner("📊 正在解算分布式灵感网络..."):
            st.session_state.current_placeholder = get_random_prompt_from_cloud(CHAT_API_KEY)
        st.session_state.is_loading = False
        st.rerun()
with col_btn2:
    enable_translate = st.toggle("🌐 激活中译英咒语优化引擎", value=True)

# 🧩 功能一：快捷拼接矩阵（Prompt Builder）
st.write("🧩 **词穷拯救者 · 核心快捷修饰标签 (点击快速追加):**")
tag_cols = st.columns(4)
added_tags = ""
with tag_cols[0]:
    if st.button("🌅 丁达尔神光", use_container_width=True): added_tags += ", tyndall effect, volumetric lighting"
    if st.button("🔮 虚幻引擎5", use_container_width=True): added_tags += ", unreal engine 5 render"
with tag_cols[1]:
    if st.button("💥 极致细节", use_container_width=True): added_tags += ", hyper-detailed, 8k resolution"
    if st.button("📸 100mm微距", use_container_width=True): added_tags += ", 100mm macro lens photography"
with tag_cols[2]:
    if st.button("🎨 赛博霓虹", use_container_width=True): added_tags += ", cyberpunk aesthetic, neon neon glowing"
    if st.button("🍃 极简主义", use_container_width=True): added_tags += ", minimalism, elegant clean composition"
with tag_cols[3]:
    if st.button("🎞️ 经典胶片", use_container_width=True): added_tags += ", 35mm film photography, vintage grain"
    if st.button("🏛️ 史诗宏大", use_container_width=True): added_tags += ", epic scale, breathtaking scenery"

# 文本框组件
base_prompt = st.text_area(
    "核心图像创意输入区 (支持中英文、支持上方标签组合):", 
    placeholder=st.session_state.current_placeholder,
    height=90
)

# 组合最终用户输入的初始词
user_input_prompt = base_prompt if base_prompt else (
    "" if st.session_state.current_placeholder.startswith("请输入创意") else st.session_state.current_placeholder
)
if added_tags and user_input_prompt:
    user_input_prompt += added_tags

# 🎭 功能二：单图风格调色盘
style_list = {
    "✨ 无滤镜自由发挥": "",
    "🎬 电影级纪实感": ", cinematic lighting, 35mm photograph, depth of field, masterpiece",
    "🍃 宫崎骏动漫风": ", Studio Ghibli style, beautiful anime aesthetic, hand-drawn, vibrant colors",
    "💻 赛博朋克风": ", cyberpunk style, neon glowing, rainy night streets with reflections",
    "🖋️ 传统国风写意": ", traditional Chinese ink wash painting, elegant brush strokes, zen concept",
    "🧸 皮克斯3D动画": ", 3D animation character in Pixar style, cute design, highly detailed clay texture"
}
chosen_style = st.selectbox("🎯 单图渲染模式下期望追加的风格滤镜：", list(style_list.keys()))

# 高级折叠面板
with st.expander("🛠️ 影像精细化渲染高级控制面板", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        aspect_ratio = st.selectbox("📐 图像画幅构图比例：", ["1:1 标准方形 (1024x1024)", "16:9 宽银幕壁纸 (1024x576)", "9:16 移动端海报 (576x1024)"])
    with col2:
        quality = st.selectbox("🎭 影像画质纯度：", ["standard", "hd"])
    negative_prompt = st.text_input("🚫 负向排除词:", placeholder="例如：变形、低画质、模糊")
    
    st.markdown("---")
    use_seed = st.checkbox("🔒 锁定特征种子 (连环画分镜专用)", value=False)
    custom_seed = st.number_input("专属种子流水号：", min_value=1, max_value=9999999, value=88888)

size_mapping = {"1:1 标准方形 (1024x1024)": "1024x1024", "16:9 宽银幕壁纸 (1024x576)": "1024x576", "9:16 移动端海报 (576x1024)": "576x1024"}
chosen_size = size_mapping[aspect_ratio]

# ==================== 5. 影像异步构建分发中枢 ====================
action_col1, action_col2 = st.columns(2)

# 渲染单张图
with action_col1:
    if st.button("开始构建单张影像 ✨", type="primary", use_container_width=True):
        if not user_input_prompt:
            st.warning("系统提示：当前输入框内容为空！")
        else:
            display_text = user_input_prompt
            with st.spinner("算力分配中..."):
                if enable_translate:
                    user_input_prompt = translate_and_optimize_prompt(CHAT_API_KEY, user_input_prompt)
                user_input_prompt += style_list[chosen_style]
                
            with st.spinner("核心矩阵正在绘制影像..."):
                payload = {"model": "gpt-image-2", "prompt": user_input_prompt, "n": 1, "size": chosen_size, "quality": quality}
                if negative_prompt: payload["negative_prompt"] = negative_prompt
                if use_seed: payload["seed"] = custom_seed
                
                img_bytes = send_image_request(payload)
                if img_bytes:
                    st.success("✨ 影像构建完成！")
                    st.image(img_bytes, caption="当前生成的单图影像", use_container_width=True)
                    st.download_button("⬇️ 下载高清原图", data=img_bytes, file_name="AIGC_Single.png", mime="image/png")
                    st.session_state.history_images.insert(0, {"prompt": display_text, "bytes": img_bytes, "label": "单图渲染"})
                else:
                    st.error("影像矩阵数据溢出，构建失败，请重试。")

# 🎭 功能三：盲盒四联画对比
with action_col2:
    if st.button("🎲 一键生成四种画风对比", use_container_width=True):
        if not user_input_prompt:
            st.warning("系统提示：请输入描述词以供四联矩阵演化！")
        else:
            display_text = user_input_prompt
            with st.spinner("🌐 翻译中枢正在全局统一解算语义..."):
                if enable_translate:
                    optimized_base = translate_and_optimize_prompt(CHAT_API_KEY, user_input_prompt)
                else:
                    optimized_base = user_input_prompt

            st.info("🚀 风格对比矩阵已启动，正在并行渲染 4 张不同艺术画作...")
            
            # 准备四种不同画风的咒语
            modes = [
                ("🎬 电影纪实", style_list["🎬 电影级纪实感"]),
                ("🍃 宫崎动漫", style_list["🍃 宫崎骏动漫风"]),
                ("🖋️ 国风水墨", style_list["🖋️ 传统国风写意"]),
                ("🧸 皮克斯3D", style_list["🧸 皮克斯3D动画"])
            ]
            
            quad_results = []
            # 建立四次后台流水线渲染
            for name, suffix in modes:
                with st.spinner(f"正在同步构建【{name}】维度的影像数据..."):
                    payload = {"model": "gpt-image-2", "prompt": optimized_base + suffix, "n": 1, "size": chosen_size, "quality": quality}
                    if negative_prompt: payload["negative_prompt"] = negative_prompt
                    if use_seed: payload["seed"] = custom_seed
                    
                    res_bytes = send_image_request(payload)
                    if res_bytes:
                        quad_results.append((name, res_bytes))
            
            # 在前端进行 2x2 并排经典排版
            if len(quad_results) > 0:
                st.success("✨ 四联艺术对比矩阵构建完成！")
                q_cols = st.columns(2)
                for idx, (name, b_data) in enumerate(quad_results):
                    with q_cols[idx % 2]:
                        st.image(b_data, caption=f"画风: {name}", use_container_width=True)
                        st.download_button(f"⬇️ 下载 {name}", data=b_data, file_name=f"{name}.png", mime="image/png", key=f"quad_{idx}")
                        # 顺便全部塞入历史展厅
                        st.session_state.history_images.insert(0, {"prompt": display_text, "bytes": b_data, "label": name})
            else:
                st.error("矩阵算力阻塞，未能成功获取对比图。")

# ==================== 6. 核心功能四：历史陈列室与一键回填 ====================
if st.session_state.history_images:
    st.markdown("---")
    st.markdown("### 📜 历史创作成果陈列室 (本次会话)")
    cols = st.columns(2)
    for index, item in enumerate(st.session_state.history_images):
        with cols[index % 2]:
            st.image(item["bytes"], use_container_width=True)
            st.caption(f"🎨 [{item['label']}] {item['prompt'][:15]}...")
            
            # 经典一键回填技术
            if st.button(f"🔄 提取此提示词回填", key=f"reback_{index}"):
                st.session_state.input_text_value = item["prompt"]
                st.rerun()
