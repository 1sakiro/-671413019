import os
import requests
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# กุญแจเชื่อมต่อระบบ
AIFORTHAI_KEY_DEFAULT = os.getenv("AIFORTHAI_API_KEY", "JI1yMBilkSsDnaM2ovkKcJ7BuUbcgZ0e")
THAILLM_KEY_DEFAULT = os.getenv("THAILLM_API_KEY", "gmFxQWdOIxSnMQjvKcUqJhuRkk5b3PEs")

EMONEWS_URL = "https://api.aiforthai.in.th/emonews/prediction"
THAILLM_URL = "http://thaillm.or.th/api/v1/chat/completions"

# ----------------- ตั้งค่าหน้าจอ -----------------
st.set_page_config(
    page_title="ตรวจสอบข่าวอารมณ์",
    page_icon="🍃",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- บังคับใช้เฉพาะโหมดสว่างและสไตล์จิบลิ -----------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Mitr:wght@300;400;500;600&family=Charm:wght@400;700&display=swap');

    /* ซ่อนปุ่ม Deploy และเมนูระบบของ Streamlit ทั้งหมด */
    .stDeployButton,
    [data-testid="stToolbarActions"],
    [data-testid="stHeaderActionElements"],
    #MainMenu,
    header [data-testid="stDecoration"],
    header [data-testid="stStatusWidget"] {
        display: none !important;
        visibility: hidden !important;
    }

    /* บังคับโทนสว่างตลอดเวลา (Only Light Theme) */
    :root, [data-testid="stAppViewContainer"], .stApp {
        color-scheme: light !important;
        background: linear-gradient(180deg, #fbf7ee 0%, #f4ede0 50%, #eae0cf 100%) !important;
        font-family: 'Mitr', sans-serif !important;
        color: #433422 !important;
    }

    /* แถบด้านข้าง */
    [data-testid="stSidebar"], [data-testid="stSidebar"] > div {
        background-color: #f3ece0 !important;
        border-right: 2px dashed #c4ad8f !important;
        color: #433422 !important;
    }

    /* แถบหัวเรื่องใหญ่ */
    .ghibli-banner {
        background: linear-gradient(135deg, #3d6044 0%, #4f7754 50%, #2f4835 100%);
        border: 3px solid #8e7354;
        border-radius: 24px;
        padding: 2.2rem 2.4rem;
        color: #fdfbf7;
        margin-bottom: 2rem;
        box-shadow: 0 12px 28px rgba(50, 40, 25, 0.15), inset 0 2px 4px rgba(255,255,255,0.2);
    }
    .ghibli-title {
        font-family: 'Charm', cursive, 'Mitr', sans-serif;
        font-size: 2.7rem;
        font-weight: 700;
        letter-spacing: 1px;
        color: #fff9e6;
        text-shadow: 2px 2px 4px rgba(30, 20, 10, 0.4);
        margin-bottom: 0.5rem;
    }
    .ghibli-subtitle {
        font-size: 1.15rem;
        color: #e5ecd6;
        line-height: 1.6;
        font-weight: 300;
    }

    /* ป้ายระบุ */
    .leaf-tag {
        display: inline-block;
        background: rgba(255, 250, 235, 0.22);
        color: #fffde8;
        padding: 0.25rem 0.85rem;
        border-radius: 20px;
        font-size: 0.85rem;
        border: 1px solid rgba(255, 255, 255, 0.35);
        margin-right: 0.5rem;
        margin-top: 0.4rem;
    }

    /* การ์ดผลลัพธ์ */
    .ghibli-card {
        background: #fffdf8 !important;
        border-radius: 18px;
        padding: 1.8rem;
        border: 2px solid #d8c7ad;
        box-shadow: 0 6px 16px rgba(90, 70, 45, 0.08);
        margin-top: 1rem;
        margin-bottom: 1.5rem;
    }

    /* กล่องคะแนน */
    .ghibli-box {
        background: #f7f1e5;
        border: 2px dashed #bba483;
        border-radius: 16px;
        padding: 1.2rem;
        text-align: center;
        color: #3b2c1a;
    }
    .ghibli-box-title {
        font-size: 0.95rem;
        color: #6d5b45;
        font-weight: 500;
    }
    .ghibli-box-value {
        font-size: 1.8rem;
        font-weight: 600;
        color: #2e4d34;
        margin-top: 0.3rem;
    }

    /* กล่องข้อความตอบกลับ */
    .ghibli-speech {
        background: #fbf9f3;
        border-left: 6px solid #4d7353;
        border-top: 1px solid #dfd3c3;
        border-right: 1px solid #dfd3c3;
        border-bottom: 1px solid #dfd3c3;
        border-radius: 0 18px 18px 0;
        padding: 1.5rem 1.8rem;
        font-size: 1.1rem;
        line-height: 1.8;
        color: #34281a;
        box-shadow: 0 4px 12px rgba(80, 60, 40, 0.06);
    }

    /* แท็บนำทาง */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #ede3d1;
        border-radius: 14px 14px 0 0;
        padding: 12px 24px;
        font-weight: 600;
        color: #5c4731 !important;
        border: 1px solid #d4c2a7;
        border-bottom: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: #fffdf8 !important;
        color: #27452d !important;
        border-top: 3px solid #3d6044 !important;
    }

    /* ปุ่มกด */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #446849 0%, #304d35 100%) !important;
        color: #fbfaf5 !important;
        border: 2px solid #233b28 !important;
        border-radius: 14px !important;
        padding: 0.6rem 1.8rem !important;
        font-size: 1.05rem !important;
        font-weight: 500 !important;
        box-shadow: 0 4px 10px rgba(45, 70, 49, 0.25) !important;
        transition: all 0.25s ease !important;
    }
    div.stButton > button:first-child:hover {
        background: linear-gradient(135deg, #537d59 0%, #3a5c40 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 14px rgba(45, 70, 49, 0.35) !important;
    }

    /* ช่องรับข้อความ */
    .stTextArea textarea {
        background-color: #fffefb !important;
        border: 2px solid #cfbeaa !important;
        border-radius: 14px !important;
        color: #382b1c !important;
        font-family: 'Mitr', sans-serif !important;
    }
    .stTextArea textarea:focus {
        border-color: #4f7754 !important;
        box-shadow: 0 0 0 2px rgba(79, 119, 84, 0.25) !important;
    }

    /* แถบเลื่อน */
    .stSlider [data-baseweb="slider"] {
        color: #4f7754 !important;
    }

    /* กล่องข้อมูลที่พับได้ */
    .streamlit-expanderHeader {
        background-color: #f7f1e5 !important;
        border-radius: 12px !important;
        color: #4e3c28 !important;
        border: 1px solid #d9cbba !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ----------------- ป้ายต้อนรับส่วนหัว -----------------
st.markdown(
    """
    <div class="ghibli-banner">
        <div class="ghibli-title">🌿 ตรวจสอบข่าวอารมณ์</div>
        <div class="ghibli-subtitle">
            พื้นที่พิจารณาและสำรวจความรู้สึกจากพาดหัวข่าว พร้อมสหายสนทนาภาษาไทย
            <br>
            <span class="leaf-tag">🍃 ตรวจจับอารมณ์ข้อความข่าว</span>
            <span class="leaf-tag">🌰 สหายสนทนาภาษาไทย</span>
            <span class="leaf-tag">🪵 สบายตาด้วยสีธรรมชาติ</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# ----------------- แถบเมนูด้านข้าง -----------------
with st.sidebar:
    st.markdown("### 🪵 กุญแจเปิดประตูเชื่อมต่อ")
    st.caption("บันทึกรหัสผ่านสำหรับเปิดใช้งานบริการภายนอก")

    aiforthai_key = st.text_input(
        "รหัสกุญแจเอไอสำหรับภาษาไทย",
        value=AIFORTHAI_KEY_DEFAULT,
        type="password",
        help="รหัสผ่านเชื่อมต่อบริการศูนย์วิจัยแห่งชาติ"
    )

    thaillm_key = st.text_input(
        "รหัสกุญแจโมเดลภาษาไทยปทุมมา",
        value=THAILLM_KEY_DEFAULT,
        type="password",
        help="รหัสผ่านสำหรับสื่อสารกับสหายปัญญาประดิษฐ์ปทุมมา"
    )

    st.divider()

    st.markdown("### 🍄 การทำงานของระบบ")
    st.markdown(
        """
        - **ตรวจสอบข่าวอารมณ์**: สังเกตความรู้สึกทั้งเจ็ดที่ซ่อนอยู่ในตัวอักษร
        - **สหายปทุมมา**: ผู้ช่วยแสนเฉลียวฉลาดที่พร้อมสนทนาและแต่งแต้มตัวอักษรภาษาไทย
        """
    )
    st.caption("รังสรรค์ด้วยความเรียบง่ายและเป็นธรรมชาติ")

# แปลงชื่ออารมณ์ภาษาอังกฤษเป็นภาษาไทย
EMOTION_THAI_MAP = {
    "joy": "สุขใจเบิกบาน",
    "happiness": "สุขสงบเปี่ยมสุข",
    "sadness": "เศร้าหมองหม่นใจ",
    "anger": "ขุ่นเคืองโกรธแค้น",
    "fear": "หวาดหวั่นพรั่นพรึง",
    "surprise": "ตื่นเต้นประหลาดใจ",
    "neutral": "สงบนิ่งเป็นกลาง",
    "disgust": "รังเกียจชิงชัง"
}

EMOTION_EMOJI_MAP = {
    "joy": "🌸",
    "happiness": "🍃",
    "sadness": "🌧️",
    "anger": "🔥",
    "fear": "🍂",
    "surprise": "✨",
    "neutral": "🪵",
    "disgust": "🍄"
}

# ----------------- แท็บการทำงาน -----------------
tab1, tab2 = st.tabs([
    "🍃 ค้นหาอารมณ์ในหัวข้อข่าว", 
    "🪵 สหายสนทนาปทุมมา"
])

# ================= แท็บ 1: วิเคราะห์อารมณ์ข่าว =================
with tab1:
    st.markdown("### 🍃 ห้องอ่านความรู้สึกจากพาดหัวข่าว")
    st.write("สังเกตและจำแนกมิติอารมณ์ที่ซ่อนอยู่ภายในถ้อยคำข่าวสารภาษาไทย")

    news_text = st.text_area(
        "ข้อความพาดหัวข่าวที่ต้องการให้ตรวจสอบ:", 
        value="นักวิจัยพบแหล่งน้ำสะอาดกลางป่าลึก ช่วยฟื้นฟูสัตว์ป่าที่กำลังขาดแคลน", 
        height=100,
        placeholder="พิมพ์หรือวางข้อความข่าวภาษาไทยลงในช่องนี้..."
    )

    btn_read_emotion = st.button("🌱 เริ่มตรวจสอบความรู้สึก", type="primary")

    if btn_read_emotion:
        clean_news = news_text.strip()
        if not clean_news:
            st.warning("🍂 กรุณาใส่ข้อความข่าวก่อนเริ่มค้นหาความรู้สึก")
        elif not aiforthai_key.strip():
            st.error("🍂 กรุณาใส่รหัสกุญแจเชื่อมต่อในแถบเมนูด้านข้างก่อน")
        else:
            headers = {"apikey": aiforthai_key.strip()}
            params = {"text": clean_news}

            with st.spinner("🌿 สายลมกำลังนำพาข้อความไปพิจารณา..."):
                try:
                    res = requests.get(EMONEWS_URL, headers=headers, params=params, timeout=15)
                    if res.status_code == 200:
                        data = res.json()
                        st.success("🌾 อ่านความรู้สึกเรียบร้อยแล้ว!")

                        results = None
                        if isinstance(data, dict):
                            if "result" in data and isinstance(data["result"], dict):
                                results = data["result"]
                            elif data.get("status") == "success" and "result" in data:
                                results = data["result"]
                            elif any(isinstance(v, (int, float)) for v in data.values()):
                                results = {k: v for k, v in data.items() if isinstance(v, (int, float))}

                        if results:
                            # หาลำดับอารมณ์เด่นชัดที่สุด
                            top_key = max(results, key=results.get)
                            score_val = results[top_key]
                            
                            thai_emotion = EMOTION_THAI_MAP.get(str(top_key).lower(), str(top_key))
                            emoji_icon = EMOTION_EMOJI_MAP.get(str(top_key).lower(), "🍃")

                            # แปลงชื่ออารมณ์ทั้งหมดเป็นภาษาไทย
                            thai_results = {
                                EMOTION_THAI_MAP.get(str(k).lower(), str(k)): float(v)
                                for k, v in results.items()
                            }

                            st.markdown(
                                f"""
                                <div class="ghibli-card">
                                    <div style="display: flex; gap: 1.2rem; flex-wrap: wrap;">
                                        <div class="ghibli-box" style="flex: 1; min-width: 160px; border-color: #557b5a;">
                                            <div class="ghibli-box-title">อารมณ์เด่นชัดที่สุด</div>
                                            <div class="ghibli-box-value">{emoji_icon} {thai_emotion}</div>
                                        </div>
                                        <div class="ghibli-box" style="flex: 1; min-width: 160px; border-color: #8c7353;">
                                            <div class="ghibli-box-title">ระดับความมั่นใจ</div>
                                            <div class="ghibli-box-value">{score_val:.2%}</div>
                                        </div>
                                        <div class="ghibli-box" style="flex: 1; min-width: 160px; border-color: #a48e71;">
                                            <div class="ghibli-box-title">จำนวนมิติอารมณ์</div>
                                            <div class="ghibli-box-value">{len(thai_results)} ด้าน</div>
                                        </div>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                            # กราฟแท่งโทนธรรมชาติ
                            st.subheader("📊 สัดส่วนความรู้สึกในแต่ละด้าน")
                            df_chart = pd.DataFrame(list(thai_results.items()), columns=["มิติอารมณ์", "สัดส่วนความรู้สึก"])
                            df_chart = df_chart.sort_values(by="สัดส่วนความรู้สึก", ascending=False)
                            st.bar_chart(df_chart.set_index("มิติอารมณ์"), color="#4f7754")

                            with st.expander("📜 เปิดดูบันทึกข้อมูลฉบับเต็ม"):
                                st.json(data)
                        else:
                            st.warning("🍄 ได้รับผลตอบกลับ แต่ไม่พบข้อมูลอารมณ์ในรูปแบบที่คุ้นเคย")
                            st.json(data)
                    else:
                        st.error(f"🍂 พบความขัดข้องจากปลายทาง (รหัส {res.status_code}): {res.text}")
                except requests.exceptions.Timeout:
                    st.error("⌛ การเชื่อมต่อใช้เวลานานเกินกำหนด กรุณาลองใหม่อีกครั้ง")
                except Exception as e:
                    st.error(f"🍂 ไม่สามารถสื่อสารกับภายนอกได้: {e}")

# ================= แท็บ 2: สหายสนทนาปทุมมา =================
with tab2:
    st.markdown("### 🪵 ห้องสนทนากับสหายปทุมมา")
    st.write("ปรึกษา แลกเปลี่ยน หรือขอคำแนะนำเรื่องราวต่างๆ ด้วยภาษาไทยที่ลื่นไหลและนุ่มนวล")

    col_ask, col_adjust = st.columns([3, 1])

    with col_ask:
        user_prompt = st.text_area(
            "ข้อความหรือคำถามที่ต้องการสนทนา:",
            value="ช่วยเล่าเรื่องราวความสำคัญของการรักษาธรรมชาติและป่าไม้ให้ฟังอย่างอบอุ่นใจหน่อย",
            height=120,
            placeholder="พิมพ์เรื่องราวหรือคำถามที่ต้องการปรึกษา..."
        )

    with col_adjust:
        st.markdown("**🍂 ปรับแต่งการตอบ:**")
        temperature = st.slider("ระดับจินตนาการ", 0.0, 1.0, 0.3, 0.05, help="ค่ายิ่งน้อย คำตอบยิ่งสุขุมและตรงจุด")
        max_tokens = st.number_input("ความยาวสูงสุดของถ้อยคำ", min_value=128, max_value=4096, value=2048, step=128)

    btn_send_chat = st.button("💬 ส่งข้อความถึงสหายปทุมมา", type="primary")

    if btn_send_chat:
        clean_prompt = user_prompt.strip()
        if not clean_prompt:
            st.warning("🍂 กรุณาพิมพ์ข้อความก่อนส่ง")
        elif not thaillm_key.strip():
            st.error("🍂 กรุณาใส่รหัสกุญแจเชื่อมต่อในแถบเมนูด้านข้างก่อน")
        else:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {thaillm_key.strip()}"
            }
            payload = {
                "model": "pathumma-thaillm-qwen3-8b-think-3.0.0",
                "messages": [
                    {
                        "role": "system",
                        "content": "คุณคือสหายปัญญาประดิษฐ์นามว่าปทุมมา ผู้มีความสุภาพ อบอุ่น เป็นมิตร และรักในธรรมชาติ ตอบคำถามเป็นภาษาไทยอย่างสละสลวย ชัดเจน และอ่านเข้าใจง่าย"
                    },
                    {
                        "role": "user", 
                        "content": clean_prompt
                    }
                ],
                "max_tokens": int(max_tokens),
                "temperature": float(temperature)
            }

            with st.spinner("🌰 สหายปทุมมากำลังใคร่ครวญและเรียบเรียงถ้อยคำ..."):
                try:
                    res = requests.post(THAILLM_URL, headers=headers, json=payload, timeout=60)
                    if res.status_code == 200:
                        result = res.json()
                        reply = result['choices'][0]['message']['content']

                        st.markdown("#### 🌿 ถ้อยคำจากสหายปทุมมา:")
                        st.markdown(
                            f"""
                            <div class="ghibli-speech">
                                {reply}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        with st.expander("📜 เปิดดูบันทึกข้อมูลฉบับเต็ม"):
                            st.json(result)
                    else:
                        st.error(f"🍂 เกิดข้อผิดพลาดจากปลายทาง (รหัส {res.status_code}): {res.text}")
                except requests.exceptions.Timeout:
                    st.error("⌛ สหายปทุมมาใช้เวลาใคร่ครวญนานเกินกำหนด กรุณาลองใหม่อีกครั้ง")
                except Exception as e:
                    st.error(f"🍂 การส่งข้อความขัดข้อง: {e}")
