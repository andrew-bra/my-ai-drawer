import streamlit as st
import requests
import base64
import os
import random
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ==================== 1. 系统级配置与缓存初始化 ====================
st.set_page_config(page_title="智能影像生成控制台", layout="centered")

# 定义本地缓存文件夹
CACHE_DIR = "image_cache"
MANIFEST_FILE = os.path.join(CACHE_DIR, "manifest.json")

# 确保缓存目录和索引账本存在
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

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

# 初始化状态变量
if "current_placeholder" not in st.session_state:
    st.session_state.current_placeholder = "等待获取灵感，或直接在此输入您的创意..."
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

# ==================== 2. 云端获取反赛博轮盘函数 ====================
def get_random_prompt_from_cloud(api_key):
    themes = [
        "古代国风水墨（如：侠客、竹林、红灯笼、泼墨山水）",
        "大自然与写实摄影（如：微距露珠、深海鲸鱼、森林晨光、高清产品照）",
        "欧洲魔幻奇幻（如：独角兽、中世纪骑士、神秘城堡、飞龙翱翔）",
        "复古温馨胶片（如：90年代老街、温馨午后、怀旧照、颗粒感）",
        "童话治愈插画（如：小巧可爱的Pip、魔法森林、梦幻绘本风格）",
        "野生动物史诗（如：远古巨兽、雪原狼群、雄鹰展翅、震撼构图）"
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

# 本地资产保存函数
def save_asset_to_local(prompt_text, img_bytes):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"img_{timestamp}.png"
    filepath = os.path.join(CACHE_DIR, filename)
    
    # 写入二进制图片
    with open(filepath, "wb") as f:
        f.write(img_bytes)
        
    # 追加账本清单
    manifest = load_manifest()
    new_entry = {
        "id": timestamp,
        "filename": filename,
        "prompt": prompt_text,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    manifest.insert(0, new_entry)
    save_manifest(manifest)

# ==================== 3. 页面视觉与输入区 ====================
st.title("💻 智绘AI：专业级图像内容生成系统")
st.write("请在下方输入您的创意描述，本系统将为您调用核心大模型进行全功能影像构建：")

# 按钮：获取灵感（带防刷新锁）
if st.button("🎲 从云端获取随机灵感", disabled=st.session_state.is_loading):
    st.session_state.is_loading = True
    with st.spinner("📊 正在检索创意数据库并构建核心提示词..."):
        st.session_state.current_placeholder = get_random_prompt_from_cloud(CHAT_API_KEY)
    st.session_state.is_loading = False
    st.rerun()

prompt = st.text_area(
    "输入画面描述 (支持中文和英文):", 
    placeholder=st.session_state.current_placeholder
)

# ==================== 4. 2.0版高级控制面板 ====================
with st.expander("🛠️ 影像精细化渲染高级控制面板", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        aspect_ratio = st.selectbox(
            "📐 图像构图画幅比例：",
            ["1:1 标准方形 (1024x1024)", "16:9 宽银幕壁纸 (1024x576)", "9:16 移动端海报 (576x1024)"]
        )
    with col2:
        quality = st.selectbox("🎭 影像生成模式：", ["standard", "hd"])
        
    negative_prompt = st.text_input("🚫 负向提示词 (不希望出现的元素):", placeholder="例如：变形、低画质、模糊")
    
    st.markdown("---")
    use_seed = st.checkbox("🔒 固定特征种子 (连环画微调专用)", value=False)
    custom_seed = st.number_input("设置固定种子数值：", min_value=1, max_value=9999999, value=88888)

size_mapping = {
    "1:1 标准方形 (1024x1024)": "1024x1024",
    "16:9 宽银幕壁纸 (1024x576)": "1024x576",
    "9:16 移动端海报 (576x1024)": "576x1024"
}
chosen_size = size_mapping[aspect_ratio]

# ==================== 5. 任务提交与渲染 ====================
if st.button("开始生成 ✨", type="primary"):
    final_prompt = prompt if prompt else (
        None if st.session_state.current_placeholder.startswith("等待获取") else st.session_state.current_placeholder
    )
    
    if not final_prompt:
        st.warning("请输入描述词，或先点击获取灵感！")
    else:
        with st.spinner("AI 正在解析全功能影像，请稍候..."):
            payload = {
                "model": "gpt-image-2", 
                "prompt": final_prompt, 
                "n": 1, 
                "size": chosen_size,
                "quality": quality
            }
            if negative_prompt:
                payload["negative_prompt"] = negative_prompt
            if use_seed:
                payload["seed"] = custom_seed
                
            headers = {
                "Authorization": f"Bearer {IMAGE_API_KEY}",
                "User-Agent": "Mozilla/5.0"
            }
            try:
                res = requests.post(URL_GEN, headers=headers, json=payload)
                if res.status_code == 200:
                    b64 = res.json()["data"][0]["b64_json"]
                    img_bytes = base64.b64decode(b64)
                    
                    st.success("✨ 影像构建成功！并已自动缓存至本地！")
                    st.image(img_bytes, caption="生成影像结果", use_container_width=True)
                    
                    # 核心改动：生图成功后，立刻持久化到本地硬盘
                    save_asset_to_local(final_prompt, img_bytes)
                    st.rerun() # 刷新页面，让下方的本地列表同步显示
                else:
                    st.error(f"构建失败，状态码: {res.status_code} 原因: {res.text}")
            except Exception as e:
                st.error(f"网络请求发生错误: {e}")

# ==================== 6. 本地硬盘持久化展厅与物理删除 ====================
manifest_data = load_manifest()

if manifest_data:
    st.markdown("---")
    st.markdown("### 📜 本地硬盘持久化历史列表")
    
    for idx, item in enumerate(manifest_data):
        filepath = os.path.join(CACHE_DIR, item["filename"])
        if os.path.exists(filepath):
            with st.container():
                col_img, col_info = st.columns([1, 1.2])
                with col_img:
                    st.image(filepath, use_container_width=True)
                with col_info:
                    st.markdown(f"**📅 缓存时间:** `{item['time']}`")
                    st.markdown(f"**🎨 初始提示词:**")
                    st.write(item["prompt"])
                    
                    # 功能控制组
                    ctrl_col1, ctrl_col2 = st.columns(2)
                    with ctrl_col1:
                        # 一键把历史提示词填回输入框
                        if st.button("🔄 提取词回填", key=f"back_{item['id']}_{idx}"):
                            st.session_state.input_text_value = item["prompt"]
                            st.rerun()
                    with ctrl_col2:
                        # 物理删除：从硬盘和清单同步抹除
                        if st.button("🗑️ 物理删除文件", key=f"del_{item['id']}_{idx}"):
                            if os.path.exists(filepath):
                                os.remove(filepath)
                            updated_manifest = [x for x in manifest_data if x["id"] != item["id"]]
                            save_manifest(updated_manifest)
                            st.success("文件已从磁盘物理抹除！")
                            st.rerun()
            st.markdown("---")
