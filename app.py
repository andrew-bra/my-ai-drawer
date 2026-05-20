import streamlit as st
import requests
import base64
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="AI 创意视觉系统", layout="centered")
st.title("个人智能视觉创意中心")

# 分别读取两个环境变量密码
IMAGE_API_KEY = os.getenv("MY_IMAGE_API_KEY")
CHAT_API_KEY = os.getenv("MY_CHAT_API_KEY")

if not IMAGE_API_KEY or not CHAT_API_KEY:
    st.error("系统错误：未检测到完整的 API Key 环境变量，请在 Secrets 中配置双密钥！")
    st.stop()

# 核心接口地址
URL_GEN = "https://nowcoding.ai/v1/images/generations"
URL_CHAT = "https://nowcoding.ai/v1/chat/completions"

# ==================== 使用“聊天密钥”获取灵感 ====================
def get_random_prompt_from_cloud(api_key):
    import random # 确保函数里能用随机数
    
    # 1. 强行在本地挑出一个风格主题，直接砸给AI，不让它自己选
    themes = [
        "古代国风水墨（如：侠客、竹林、红灯笼、泼墨山水）",
        "大自然与写实摄影（如：微距露珠、深海鲸鱼、森林晨光、高清产品照）",
        "欧洲魔幻奇幻（如：独角兽、中世纪骑士、神秘城堡、飞龙翱翔）",
        "复古温馨胶片（如：90年代老街、温馨午后、怀旧照、颗粒感）",
        "童话治愈插画（如：小巧可爱的Pip、魔法森林、梦幻绘本风格）",
        "野生动物史诗（如：远古巨兽、雪原狼群、雄鹰展翅、震撼构图）"
    ]
    chosen_theme = random.choice(themes) # 每次点击，Python会在后台盲盒抽一个风格

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
            # 核心修改：强制输出服务器返回的详细原生错误信息！
            return f"报错啦！状态码 {res.status_code}，服务器说：{res.text}"
    except Exception as e:
        return f"网络连接超时：{e}"

if "current_placeholder" not in st.session_state:
    st.session_state.current_placeholder = "等待获取云端灵感，或直接在此输入您的创意..."

st.write("请在下方输入您的创意描述，本系统将为您调用核心大模型进行全功能影像构建：")

# 升级版：加入状态锁，防止在获取过程中重复触发刷新
if "is_loading" not in st.session_state:
    st.session_state.is_loading = False

# 只有在非加载状态下才允许点击
if st.button("🎲 获取随机灵感创意", disabled=st.session_state.is_loading):
    st.session_state.is_loading = True  # 锁定状态
    
    with st.spinner("📊 正在获取..."):
        # 真正开始去向模型要灵感
        st.session_state.current_placeholder = get_random_prompt_from_cloud(CHAT_API_KEY)
        
    st.session_state.is_loading = False  # 解锁状态
    st.rerun()  # 刷新页面展示新词

prompt = st.text_area(
    "输入画面描述 (支持中文和英文):", 
    placeholder=st.session_state.current_placeholder
)

if st.button("开始生成 ✨", type="primary"):
    final_prompt = prompt if prompt else st.session_state.current_placeholder
    
    if final_prompt == "等待获取云端灵感，或直接在此输入您的创意...":
        st.warning("请输入描述词，或先点击获取灵感！")
    else:
        with st.spinner("AI 正在解析全功能影像，请稍候..."):
            payload = {
                "model": "gpt-image-2", 
                "prompt": final_prompt, 
                "n": 1, 
                "size": "1024x1024"
            }
            # 使用画图专用密钥
            headers = {
                "Authorization": f"Bearer {IMAGE_API_KEY}",
                "User-Agent": "Mozilla/5.0"
            }
            try:
                res = requests.post(URL_GEN, headers=headers, json=payload)
                if res.status_code == 200:
                    b64 = res.json()["data"][0]["b64_json"]
                    img_bytes = base64.b64decode(b64)
                    
                    st.image(img_bytes, caption="生成影像结果", use_container_width=True)
                    st.download_button("⬇️ 下载高清原图", data=img_bytes, file_name="AI_Art.png", mime="image/png", type="primary")
                    st.success("✨ 影像构建成功！")
                else:
                    st.error(f"构建失败，状态码: {res.status_code} 原因: {res.text}")
            except Exception as e:
                st.error(f"网络请求发生错误: {e}")
