import streamlit as st
import requests
import base64
import os
from io import BytesIO
from PIL import Image
from streamlit_drawable_canvas import st_canvas
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="AI 智能画稿 & P图工作站", layout="wide")
st.title("🎨 我的 AI 艺术生成与智能P图大师")

# 读取环境变量密码
API_KEY = os.getenv("MY_API_KEY")
if not API_KEY:
    st.error("系统错误：未检测到 API Key 环境变量，请检查配置！")
    st.stop()

# 定义导航模式
mode = st.sidebar.radio("选择工作模式：", ["✨ 纯文字生图", "🖌️ 智能P图（局部重绘）"])

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

# ==================== 模式 1：纯文字生图 ====================
if mode == "✨ 纯文字生图":
    URL_GEN = "https://api.nowcoding.ai/v1/images/generations"
    prompt = st.text_area("请输入画面描述 (支持中文和英文):", placeholder="例如：大海")
    
    if st.button("开始生成 ✨", type="primary"):
        if not prompt:
            st.warning("请输入描述词！")
        else:
            with st.spinner("AI 正在疯狂作画中..."):
                payload = {"model": "gpt-image-2", "prompt": prompt, "n": 1, "size": "1024x1024"}
                try:
                    res = requests.post(URL_GEN, headers=headers, json=payload)
                    if res.status_code == 200:
                        b64 = res.json()["data"][0]["b64_json"]
                        img_bytes = base64.b64decode(b64)
                        st.image(img_bytes, caption="生成结果", use_container_width=True)
                        st.download_button("⬇️ 下载高清原图", data=img_bytes, file_name="AI_art.png", mime="image/png", type="primary")
                    else:
                        st.error(f"失败: {res.text}")
                except Exception as e:
                    st.error(f"错误: {e}")

# ==================== 模式 2：智能P图 ====================
elif mode == "🖌️ 智能P图（局部重绘）":
    URL_EDIT = "https://api.nowcoding.ai/v1/images/edits"
    
    st.markdown("### 💡 使用说明：\n1. 上传一张任意格式的图片（**支持 PNG, JPG, JPEG**）。\n2. 用鼠标在右侧画板上**涂抹**需要修改/删掉的区域。\n3. 在下方输入咒语，告诉 AI 你想把涂抹区域改成什么。")
    
    # 核心改动：type 增加了 jpg 和 jpeg
    uploaded_file = st.file_uploader("第一步：上传待修改的图片", type=["png", "jpg", "jpeg"])
    
    if uploaded_file:
        # 核心改动：不管用户传什么，强行转换为带有透明通道的 RGBA 格式并缩放
        bg_image = Image.open(uploaded_file).convert("RGBA").resize((512, 512))
        
        st.write("第二步：请在下方图片上用鼠标【涂抹】需要修改的地方：")
        
        # 调出网页画板组件
        canvas_result = st_canvas(
            fill_color="rgba(0, 0, 0, 1)",  # 涂抹处变为不透明
            stroke_width=20,                 # 画笔粗细
            stroke_color="rgba(0, 0, 0, 1)",
            background_image=bg_image,       # 背景垫原图
            update_streamlit=True,
            height=512,
            width=512,
            drawing_mode="freedraw",
            key="canvas",
        )
        
        edit_prompt = st.text_input("第三步：请输入修改命令（你要把涂掉的地方改成什么？）", placeholder="例如：把这里换成一只橘猫")
        
        if st.button("开始智能 P图 🚀", type="primary"):
            if not edit_prompt:
                st.warning("请输入修改命令！")
            elif canvas_result.image_data is None:
                st.warning("请先在图片上涂抹要修改的区域！")
            else:
                with st.spinner("AI 正在施展变身术，请稍候..."):
                    try:
                        # 1. 准备原图数据包（统一导出为 AI 强制要求的 PNG 格式）
                        img_buffer = BytesIO()
                        bg_image.resize((1024, 1024)).save(img_buffer, format="PNG")
                        img_buffer.seek(0)
                        
                        # 2. 准备蒙版数据包
                        mask_data = canvas_result.image_data  
                        mask_image = Image.fromarray(mask_data.astype('uint8'), 'RGBA')
                        
                        # 反转透明度算法
                        r, g, b, a = mask_image.split()
                        final_mask = Image.merge("RGBA", (r, g, b, r)) 
                        
                        mask_buffer = BytesIO()
                        final_mask.resize((1024, 1024)).save(mask_buffer, format="PNG")
                        mask_buffer.seek(0)
                        
                        # 3. 发送给新中转商的表单请求
                        files = {
                            "image": ("image.png", img_buffer, "image/png"),
                            "mask": ("mask.png", mask_buffer, "image/png"),
                        }
                        data = {
                            "model": "gpt-image-2", 
                            "prompt": edit_prompt,
                            "n": 1,
                            "size": "1024x1024"
                        }
                        
                        edit_headers = {"Authorization": f"Bearer {API_KEY}"}
                        res = requests.post(URL_EDIT, headers=edit_headers, files=files, data=data)
                        
                        if res.status_code == 200:
                            b64 = res.json()["data"][0]["b64_json"]
                            out_bytes = base64.b64decode(b64)
                            st.image(out_bytes, caption="P图成功！", use_container_width=True)
                            st.download_button("⬇️ 下载完美成片", data=out_bytes, file_name="P_Result.png", mime="image/png")
                        else:
                            st.error(f"P图失败，服务商返回：{res.text}")
                    except Exception as e:
                        st.error(f"发生错误: {e}")
