import streamlit as st
import requests
import base64
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="AI 智能画稿", layout="centered")
st.title("🎨 我的 AI 艺术生成器")

# 读取环境变量密码
API_KEY = os.getenv("MY_API_KEY")
if not API_KEY:
    st.error("系统错误：未检测到 API Key 环境变量，请联系管理员配置！")
    st.stop()

# 核心接口地址
URL_GEN = "https://api.nowcoding.ai/v1/images/generations"

st.write("请在下方输入您的创意，AI 将为您绘制专属画作：")
prompt = st.text_area("画面描述 (支持中文和英文):", placeholder="例如：90年代的结婚照，复古风格，高画质...")

if st.button("开始生成 ✨", type="primary"):
    if not prompt:
        st.warning("请输入描述词！")
    else:
        with st.spinner("AI 正在疯狂作画中，请稍候..."):
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
                    st.image(img_bytes, caption="您的 AI 画作", use_container_width=True)
                    st.download_button("⬇️ 下载高清原图", data=img_bytes, file_name="AI_Art.png", mime="image/png", type="primary")
                    st.success("✨ 生成成功啦！")
                else:
                    st.error(f"生成失败，状态码: {res.status_code} 原因: {res.text}")
            except Exception as e:
                st.error(f"网络请求发生错误: {e}")
