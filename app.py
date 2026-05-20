import streamlit as st
import requests
import base64
import os
import random  # 新增：引入随机库
from dotenv import load_dotenv

load_dotenv()

# 1. 升级为官方、专业的系统级名称
st.set_page_config(page_title="AI 图像内容全功能创作平台", layout="centered")
st.title("💻 智绘AI：专业级图像内容生成系统")

# 读取环境变量密码
API_KEY = os.getenv("MY_API_KEY")
if not API_KEY:
    st.error("系统错误：未检测到 API Key 环境变量，请联系管理员配置！")
    st.stop()

# 核心接口地址
URL_GEN = "https://api.nowcoding.ai/v1/images/generations"

# 2. 内置一套涵盖多种高级风格的专业创意文案库
PROMPT_EXAMPLES = [
    "90年代的复古胶片结婚照，温馨柔和的光影，颗粒感细腻，高清晰度，写实风格",
    "赛博朋克风的未来都市，霓虹灯光交织，雨夜街道倒影，超高画质，电影级视效",
    "科幻插画：一只身穿高科技宇航服的橘猫队长在火星表面漫步，极具科技感与细节描绘",
    "一幅莫奈印象派风格的向日葵花海，阳光明媚，油画笔触浓郁而富有生命力",
    "概念艺术：一个科技感十足的智能扫地机器人在废土世界中自主觉醒，机械结构精细",
    "宏大的中世纪奇幻城堡，巨龙在云雾缭绕的山巅翱翔，史诗级CG画质，全景构图",
    "一只有着聪慧眼神的哈士奇正在全神贯注地操作充满全息投影的计算机控制台，高度写实"
]

# 在系统缓存中初始化一个随机推荐词
if "current_placeholder" not in st.session_state:
    st.session_state.current_placeholder = random.choice(PROMPT_EXAMPLES)

st.write("请在下方输入您的创意描述，本系统将为您调用核心大模型进行全功能影像构建：")

# 3. 新增：允许手动随机抽样文案的按钮
if st.button("🎲 随机灵感推荐"):
    st.session_state.current_placeholder = random.choice(PROMPT_EXAMPLES)
    st.rerun()  # 触发系统重新渲染，立即刷新输入框的提示

prompt = st.text_area(
    "输入画面描述 (支持中文和英文):", 
    placeholder=f"例如：{st.session_state.current_placeholder}"
)

if st.button("开始生成 ✨", type="primary"):
    if not prompt:
        st.warning("请输入描述词！")
    else:
        with st.spinner("AI 正在解析全功能影像，请稍候..."):
            payload = {
                "model": "gpt-image-2", 
                "prompt": prompt, 
                "n": 1, 
                "size": "1024x1024"
            }
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "User-Agent": "Mozilla/5.0"
            }
            try:
                res = requests.post(URL_GEN, headers=headers, json=payload)
                if res.status_code == 200:
                    b64 = res.json()["data"][0]["b64_json"]
                    img_bytes = base64.b64decode(b64)
                    
                    # 展示图片与下载按钮
                    st.image(img_bytes, caption="生成影像结果", use_container_width=True)
                    st.download_button("⬇️ 下载高清原图", data=img_bytes, file_name="AI_Art.png", mime="image/png", type="primary")
                    st.success("✨ 影像构建成功！")
                else:
                    st.error(f"构建失败，状态码: {res.status_code} 原因: {res.text}")
            except Exception as e:
                st.error(f"网络请求发生错误: {e}")
