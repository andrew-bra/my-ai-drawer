import streamlit as st
import requests
import base64
import os
import random
from dotenv import load_dotenv

load_dotenv()

# ==================== 1. 系统级专业配置 ====================
st.set_page_config(page_title="智能影像生成控制台", layout="centered")

# 初始化系统缓存变量
if "current_placeholder" not in st.session_state:
    st.session_state.current_placeholder = "点击下方按钮获取灵感，或在此直接输入您的创意描述..."
if "is_loading" not in st.session_state:
    st.session_state.is_loading = False
if "history_images" not in st.session_state:
    st.session_state.history_images = []  # 历史作品陈列室存储器

# 读取环境变量密码
IMAGE_API_KEY = os.getenv("MY_IMAGE_API_KEY")
CHAT_API_KEY = os.getenv("MY_CHAT_API_KEY")

if not IMAGE_API_KEY or not CHAT_API_KEY:
    st.error("系统错误：未检测到完整的 API Key 环境变量，请在 Secrets 中配置双密钥！")
    st.stop()

# 核心接口地址（已完美剔除 api.）
URL_GEN = "https://nowcoding.ai/v1/images/generations"
URL_CHAT = "https://nowcoding.ai/v1/chat/completions"

# ==================== 2. 云端获取反赛博轮盘函数 ====================
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

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
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
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"].strip()
        else:
            return f"报错啦！状态码 {res.status_code}，服务器说：{res.text}"
    except Exception as e:
        return f"网络连接超时：{e}"

# ==================== 3. 视觉美化：企业级科技横幅 ====================
st.markdown("""
<div style="background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%); padding: 22px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
    <h2 style="color: white; margin: 0; text-align: center; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; letter-spacing: 1px;">AIGC 智能影像生成系统</h2>
    <p style="color: #e0e0e0; margin: 5px 0 0 0; text-align: center; font-size: 14px;">专业级多模态计算与数字影像构建平台</p>
</div>
""", unsafe_allow_html=True)

st.write("请在下方调整参数并输入创意描述，系统将分配核心算力进行影像异步构建：")

# ==================== 4. 核心功能区 ====================

# 灵感生成防刷新按钮
if st.button("🎲 获取随机灵感创意", disabled=st.session_state.is_loading):
    st.session_state.is_loading = True
    with st.spinner("📊 正在检索创意数据库并构建核心提示词..."):
        st.session_state.current_placeholder = get_random_prompt_from_cloud(CHAT_API_KEY)
    st.session_state.is_loading = False
    st.rerun()

# 核心文本框
prompt = st.text_area(
    "核心图像描述 (支持中文及英文):", 
    placeholder=st.session_state.current_placeholder,
    height=100
)

# --- 新增功能：高级参数配置面板 ---
with st.expander("🛠️ 影像精细化渲染高级控制面板", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        # 尺寸矩阵切换
        aspect_ratio = st.selectbox(
            "📐 图像构图画幅比例：",
            ["1:1 标准方形 (1024x1024)", "16:9 宽银幕壁纸 (1024x576)", "9:16 移动端海报 (576x1024)"]
        )
    with col2:
        # 渲染画质切换
        quality = st.selectbox("🎭 影像生成模式：", ["standard (标准影像)", "hd (超清影像增强)"])
        
    # 负向提示词输入
    negative_prompt = st.text_input(
        "🚫 负向提示词 (不希望画面中出现的元素):", 
        placeholder="例如：变形、低画质、崩坏的肢体、模糊、水印"
    )

# 映射比例参数
size_mapping = {
    "1:1 标准方形 (1024x1024)": "1024x1024",
    "16:9 宽银幕壁纸 (1024x576)": "1024x576",
    "9:16 移动端海报 (576x1024)": "576x1024"
}
chosen_size = size_mapping[aspect_ratio]

# ==================== 5. 任务分发与提交 ====================
if st.button("开始构建影像 ✨", type="primary"):
    final_prompt = prompt if prompt else (None if st.session_state.current_placeholder.startswith("点击下方按钮") else st.session_state.current_placeholder)
    
    if not final_prompt:
        st.warning("系统提示：检测到当前输入内容为空，请填写描述词或获取灵感！")
    else:
        with st.spinner("AI 正在解析多维向量并生成影像，请稍候..."):
            # 构建标准的 OpenAI 图像请求体，加入尺寸和质量参数
            payload = {
                "model": "gpt-image-2", 
                "prompt": final_prompt, 
                "n": 1, 
                "size": chosen_size,
                "quality": quality.split(" ")[0]
            }
            # 如果中转商支持并在高级设置填了负面词，可以附带上去
            if negative_prompt:
                payload["negative_prompt"] = negative_prompt
                
            headers = {
                "Authorization": f"Bearer {IMAGE_API_KEY}",
                "User-Agent": "Mozilla/5.0"
            }
            try:
                res = requests.post(URL_GEN, headers=headers, json=payload)
                if res.status_code == 200:
                    b64 = res.json()["data"][0]["b64_json"]
                    img_bytes = base64.b64decode(b64)
                    
                    # 成果主展示区
                    st.success("✨ 核心影像构建完成！")
                    st.image(img_bytes, caption="当前生成的影像结果", use_container_width=True)
                    st.download_button("⬇️ 下载当前高清原图", data=img_bytes, file_name="AIGC_Result.png", mime="image/png", type="primary")
                    
                    # --- 新增功能：自动将成果收入历史陈列室 ---
                    st.session_state.history_images.insert(0, {"prompt": final_prompt, "bytes": img_bytes})
                    
                else:
                    st.error(f"影像构建失败，状态码: {res.status_code} 原因: {res.text}")
            except Exception as e:
                st.error(f"网络计算节点发生错误: {e}")

# ==================== 6. 新增：历史创作成果陈列室 ====================
if st.session_state.history_images:
    st.markdown("---")
    st.markdown("### 📜 历史创作成果陈列室 (本次会话)")
    
    # 使用 Streamlit 布局做双列瀑布流陈列
    cols = st.columns(2)
    for index, item in enumerate(st.session_state.history_images):
        with cols[index % 2]:
            st.image(item["bytes"], use_container_width=True)
            st.caption(f"🎨 描述: {item['prompt'][:20]}...")
