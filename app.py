import os
from dotenv import load_dotenv # 新增：引入工具
load_dotenv() # 新增：代码启动时，自动去读取旁边 .env 文件里的密码

import streamlit as st
import requests
import base64

st.set_page_config(page_title="AI 智能画稿", layout="centered")
st.title("🎨 我的 AI 艺术生成器")

import os  # 确保文件最上方引入了 os 库

# 接口地址
URL = "https://nowcoding.ai/v1/images/generations"

# ⭐️ 关键修改：让代码去系统的“环境变量”里寻找叫 MY_API_KEY 的值
API_KEY = os.getenv("MY_API_KEY")

# 增加一个安全检查：如果没找到 Key，就在网页上提示报错，不再继续往下跑
if not API_KEY:
    st.error("系统错误：未检测到 API Key 环境变量，请在服务器后台配置！")
    st.stop()


# 网页上现在只剩下画面描述的输入框了
prompt = st.text_area("请输入画面描述 (支持中文和英文):", placeholder="例如：大海")

if st.button("开始生成 ✨", type="primary"):
    if not prompt:
        st.warning("请输入描述词！")
    else:
        with st.spinner("AI 正在疯狂作画中，请稍候..."):
            headers = {
                "Authorization": f"Bearer {API_KEY}",  # 后台自动调用这个 Key
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            }
            
            payload = {
                "model": "gpt-image-2",
                "prompt": prompt,
                "n": 1,
                "size": "1024x1024"
            }
            
            try:
                response = requests.post(URL, headers=headers, json=payload)
                
                if response.status_code == 200:
                    res_data = response.json()
                    
                    try:
                        # 翻译图片乱码
                        b64_string = res_data["data"][0]["b64_json"]
                        image_bytes = base64.b64decode(b64_string)
                        
                        # 展示图片
                        st.image(image_bytes, caption="生成结果（右键可另存为）", use_container_width=True)
                        st.success("✨ 生成成功啦！")
                        
                    except KeyError:
                        st.error("解析图片失败。")
                        st.json(res_data)
                        
                else:
                    st.error(f"请求失败！\n状态码: {response.status_code}\n原因: {response.text}")
                    
            except Exception as e:
                st.error(f"发生错误: {e}")
