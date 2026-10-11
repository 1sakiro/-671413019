# -*- coding: utf-8 -*-
"""
Thai AI Intelligence Hub
วิเคราะห์อารมณ์จากพาดหัวข่าว (AIForThai EmoNews) และสนทนาถาม-ตอบ (ThaiLLM Pathumma 3.0)
ธีม: ห้องข่าว (Newsroom) - น้ำเงินหมึก + แดงข่าวด่วน
"""

import os
import re
import html as htmllib
from datetime import datetime

import requests
import streamlit as st
from dotenv import load_dotenv

# ──────────────────────────────────────────────────────────────
# 1. ENV & CONSTANTS
# ──────────────────────────────────────────────────────────────
load_dotenv()

# หมายเหตุ: ไม่ฝังคีย์จริงไว้ในโค้ดแล้ว ใส่ในไฟล์ .env หรือกรอกในแถบด้านข้าง
AIFORTHAI_KEY_DEFAULT = os.getenv("AIFORTHAI_API_KEY", "")
THAILLM_KEY_DEFAULT = os.getenv("THAILLM_API_KEY", "")

EMONEWS_URL = "https://api.aiforthai.in.th/emonews/prediction"
# ThaiLLM มี 2 เส้นทาง ระบบจะลองตามลำดับจนกว่าจะสำเร็จ (ใช้คีย์เดียวกัน)
THAILLM_ENDPOINTS = [
    ("http://thaillm.or.th/api/v1/chat/completions", "pathumma-thaillm-qwen3-8b-think-3.0.0"),
    ("http://thaillm.or.th/api/pathumma/v1/chat/completions", "/model"),
]

EMOTION_META = {
    "joy":       {"thai": "สุขใจ / เบิกบาน",      "en": "Joy",      "color": "#d97706"},
    "happiness": {"thai": "สุขสงบ / ผ่อนคลาย",    "en": "Happiness", "color": "#15803d"},
    "sadness":   {"thai": "เศร้าหมอง / หม่นใจ",   "en": "Sadness",  "color": "#2563eb"},
    "anger":     {"thai": "ขุ่นเคือง / โมโห",     "en": "Anger",    "color": "#d7263d"},
    "fear":      {"thai": "หวาดหวั่น / กังวล",    "en": "Fear",     "color": "#7c3aed"},
    "surprise":  {"thai": "ประหลาดใจ / ตื่นเต้น", "en": "Surprise", "color": "#0891b2"},
    "neutral":   {"thai": "เป็นกลาง / สงบนิ่ง",   "en": "Neutral",  "color": "#64748b"},
    "disgust":   {"thai": "รังเกียจ / ชิงชัง",    "en": "Disgust",  "color": "#92400e"},
}
FALLBACK_COLOR = "#0b1f3a"

SAMPLE_NEWS = [
    ("นวัตกรรมสิ่งแวดล้อม",
     "นักวิจัยไทยประสบความสำเร็จ ผลิตระบบกรองน้ำชีวภาพช่วยฟื้นฟูชุมชนริมแม่น้ำ"),
    ("เยาวชนคว้าแชมป์โลก",
     "ทีมเยาวชนไทยคว้าแชมป์หุ่นยนต์กู้ภัยโลก สร้างชื่อเสียงกระหึ่มเวทีสากล"),
    ("เตือนภัยพายุฝน",
     "กรมอุตุฯ เตือนรับมือพายุดีเปรสชัน เสี่ยงน้ำท่วมฉับพลันและดินถล่ม 15 จังหวัด"),
    ("ตลาดหุ้นผันผวน",
     "นักลงทุนจับตาความไม่แน่นอนของเศรษฐกิจโลก ส่งผลตลาดหุ้นไทยปิดลบเล็กน้อย"),
]

SAMPLE_PROMPTS = [
    ("แนวทางลดโลกร้อน",
     "ช่วยแนะนำ 5 แนวทางง่ายๆ ในชีวิตประจำวันเพื่อช่วยลดภาวะโลกร้อนและดูแลสิ่งแวดล้อมให้ยั่งยืน"),
    ("แต่งกลอนแปดแสงตะวัน",
     "ช่วยแต่งกลอนแปดภาษาไทย 2 บท เกี่ยวกับความอบอุ่นของแสงตะวันยามเช้าและพลังใจในการเริ่มต้นวันใหม่"),
    ("คุณค่าของ Thai AI",
     "การมีโมเดลภาษาไทยเฉพาะทางอย่าง Pathumma มีความสำคัญและสร้างประโยชน์อย่างไรต่อสังคมไทย?"),
]

DEFAULT_HEADLINE = "นักวิจัยพบแหล่งน้ำสะอาดกลางป่าลึก ช่วยฟื้นฟูสัตว์ป่าที่กำลังขาดแคลน"
DEFAULT_CHAT = "ช่วยสรุปข่าวนี้ให้เข้าใจง่าย และบอกว่าข่าวลักษณะนี้ส่งผลต่ออารมณ์ผู้อ่านอย่างไร"

THAI_DAYS = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]
THAI_MONTHS = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
               "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]


def thai_dateline() -> str:
    n = datetime.now()
    return f"วัน{THAI_DAYS[n.weekday()]}ที่ {n.day} {THAI_MONTHS[n.month - 1]} {n.year + 543}"


def compact(markup: str) -> str:
    """บีบ HTML ให้เป็นบรรทัดเดียว ป้องกัน Markdown ตีความย่อหน้าเป็น code block"""
    return "".join(line.strip() for line in markup.splitlines())


def post_thaillm(headers: dict, payload: dict):
    """เรียก ThaiLLM ตามลำดับ endpoint จนกว่าจะได้ 200 คืนค่า (response, url ที่ใช้)"""
    last = None
    for url, model in THAILLM_ENDPOINTS:
        body = dict(payload, model=model)
        try:
            res = requests.post(url, headers=headers, json=body, timeout=60)
        except requests.exceptions.Timeout:
            raise
        except requests.exceptions.RequestException:
            continue
        last = (res, url)
        if res.status_code == 200:
            return last
        if res.status_code in (401, 403):  # คีย์ไม่ถูกต้อง ลองเส้นทางอื่นก็ไม่ช่วย
            break
    if last is None:
        raise requests.exceptions.ConnectionError("เชื่อมต่อเซิร์ฟเวอร์ ThaiLLM ไม่ได้ ตรวจสอบอินเทอร์เน็ต")
    return last


def split_think(reply: str):
    """แยกส่วนกระบวนการคิด (<think>) ออกจากคำตอบสุดท้าย รองรับกรณีมีแต่ </think> หรือถูกตัดกลางคัน"""
    reply = reply or ""
    if "</think>" in reply:
        think, answer = reply.split("</think>", 1)
        return think.replace("<think>", "").strip(), answer.strip()
    if "<think>" in reply:
        return reply.replace("<think>", "").strip(), ""
    return "", reply.strip()


def emo_info(key) -> dict:
    return EMOTION_META.get(
        str(key).lower(),
        {"thai": str(key), "en": str(key), "color": FALLBACK_COLOR},
    )


# ──────────────────────────────────────────────────────────────
# 2. PAGE CONFIG
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="วิเคราะห์อารมณ์จากพาดหัวข่าว - Thai AI Intelligence Hub",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────
# 3. CSS - NEWSROOM THEME
#    หมึกน้ำเงิน #0b1f3a | แดงข่าวด่วน #d7263d | กระดาษ #f3f5f8
# ──────────────────────────────────────────────────────────────
CSS = r"""
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+Thai:wght@600;700&family=Prompt:wght@400;500;600&display=swap');
    :root {
        --navy: #0b2a6b;
        --navy-2: #123f8f;
        --ink: #0b1f3a;
        --red: #d7263d;
        --red-dark: #b01c30;
        --paper: #ffffff;
        --tint: #f1f4f9;
        --rule: #d5dbe3;
        --muted: #55657d;
        --serif: 'Noto Serif Thai', 'Prompt', Georgia, serif;
        --sans: 'Prompt', 'Noto Sans Thai', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    /* ฟอนต์ (ไม่แตะ icon font) */
    html, body, .stApp,
    .stApp p, .stApp li, .stApp label, .stApp textarea, .stApp input,
    .stApp button, [data-testid="stCaptionContainer"],
    [data-testid="stExpander"] summary p {
        font-family: var(--sans) !important;
        -webkit-font-smoothing: antialiased;
        text-rendering: optimizeLegibility;
    }
    .stApp p, .stApp li { line-height: 1.7; }
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5 {
        font-family: var(--serif) !important;
        color: var(--navy) !important;
        font-weight: 700 !important;
        line-height: 1.45 !important;
        letter-spacing: 0 !important;
    }
    [class*="material-symbols"], [class*="material-icons"],
    [data-testid="stIconMaterial"], [data-testid*="Icon"] {
        font-family: "Material Symbols Rounded", "Material Icons" !important;
        font-style: normal !important;
        line-height: 1 !important;
        white-space: nowrap !important;
    }

    /* Chrome ของ Streamlit */
    header[data-testid="stHeader"] { background: transparent !important; box-shadow: none !important; }
    .stDeployButton, [data-testid="stAppDeployButton"], [data-testid="stToolbarActions"],
    [data-testid="stMainMenu"], #MainMenu, [data-testid="stDecoration"] { display: none !important; }

    [data-testid="stAppViewContainer"], .stApp { background: var(--paper) !important; color: var(--ink); }
    .main .block-container, [data-testid="stMainBlockContainer"] {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        max-width: 1080px !important;
    }

    /* แถบธงไตรรงค์บางๆ ด้านบนสุดของหน้า (แดง-ขาว-น้ำเงิน-ขาว-แดง) */
    .stApp::before {
        content: ""; position: fixed; top: 0; left: 0; right: 0; height: 6px;
        z-index: 1000000; pointer-events: none;
        background: linear-gradient(90deg,
            var(--red) 0 16.66%, #ffffff 16.66% 33.33%,
            var(--navy) 33.33% 66.66%, #ffffff 66.66% 83.33%, var(--red) 83.33% 100%);
    }

    /* Masthead */
    .masthead { background: var(--navy); border-radius: 12px; overflow: hidden; margin-bottom: 1.5rem; }
    .masthead-body { padding: 1.6rem 2rem 1.5rem; }
    .masthead-top {
        display: flex; align-items: center; justify-content: space-between;
        gap: 12px; margin-bottom: 0.9rem; flex-wrap: wrap;
    }
    .masthead-badge {
        display: inline-flex; align-items: center; gap: 8px;
        background: var(--red); color: #fff !important;
        font-size: 0.82rem; font-weight: 600;
        padding: 0.2rem 0.8rem; border-radius: 4px;
    }
    .masthead-badge::before { content: ""; width: 7px; height: 7px; border-radius: 50%; background: #fff; }
    .masthead-date { color: #c3d0e6 !important; font-size: 0.85rem; }
    .masthead-title {
        font-family: var(--serif) !important;
        font-size: 2.3rem; font-weight: 700;
        color: #ffffff !important;
        margin: 0 0 0.4rem 0; line-height: 1.4;
    }
    .masthead-sub { color: rgba(255, 255, 255, 0.88) !important; font-size: 0.97rem; margin: 0; max-width: 720px; }
    .ticker { display: flex; align-items: stretch; background: var(--red); overflow: hidden; }
    .ticker-label {
        background: #ffffff; color: var(--red) !important;
        font-weight: 600; font-size: 0.85rem;
        padding: 0.5rem 1.1rem; white-space: nowrap; flex-shrink: 0;
    }
    .ticker-window { overflow: hidden; flex: 1; display: flex; align-items: center; }
    .ticker-track { display: inline-flex; white-space: nowrap; animation: ticker-scroll 55s linear infinite; }
    .ticker-track span { color: #ffffff !important; font-size: 0.87rem; font-weight: 500; padding: 0 2rem; position: relative; }
    .ticker-track span::after {
        content: ""; position: absolute; right: 0; top: 50%;
        width: 5px; height: 5px; margin-top: -2.5px; background: #fff; border-radius: 50%;
    }
    @keyframes ticker-scroll { from { transform: translateX(0); } to { transform: translateX(-50%); } }
    @media (prefers-reduced-motion: reduce) { .ticker-track { animation: none; } }

    /* Tabs: ป้ายช่องข่าว */
    .stTabs [data-baseweb="tab-list"] { gap: 4px; margin-bottom: 1.25rem; }
    .stTabs [data-baseweb="tab-border"] { background-color: var(--navy) !important; height: 2px !important; }
    .stTabs [data-baseweb="tab"] {
        background: var(--tint); padding: 0.6rem 1.2rem; height: auto;
        border-radius: 8px 8px 0 0;
    }
    .stTabs [data-baseweb="tab"] p { color: var(--navy) !important; font-weight: 500; font-size: 0.97rem; }
    .stTabs [data-baseweb="tab"]:hover { background: #e3e9f3; }
    .stTabs [aria-selected="true"] { background: var(--navy) !important; }
    .stTabs [aria-selected="true"] p { color: #ffffff !important; font-weight: 600; }
    .stTabs [data-baseweb="tab-highlight"] { background-color: var(--red) !important; height: 3px !important; }

    /* หัวข้อส่วน */
    .section-head {
        font-family: var(--serif); font-size: 1.2rem; font-weight: 700;
        color: var(--navy); margin: 0.25rem 0 0.2rem; line-height: 1.5;
        border-left: 6px solid var(--red); padding-left: 0.7rem;
    }
    .section-desc { color: var(--muted); font-size: 0.9rem; margin: 0 0 1rem 0.95rem; }
    .field-label { color: var(--navy); font-size: 0.88rem; font-weight: 600; margin: 0.25rem 0 0.4rem; }

    /* Inputs */
    [data-testid="stTextInput"] [data-baseweb="input"],
    [data-testid="stTextArea"] [data-baseweb="textarea"],
    [data-testid="stNumberInput"] [data-baseweb="input"] {
        background: #fff !important; border: 1px solid #aab6c8 !important;
        border-radius: 10px !important; box-shadow: none !important;
    }
    [data-testid="stTextInput"] [data-baseweb="input"]:focus-within,
    [data-testid="stTextArea"] [data-baseweb="textarea"]:focus-within,
    [data-testid="stNumberInput"] [data-baseweb="input"]:focus-within {
        border-color: var(--navy) !important; box-shadow: 0 0 0 3px rgba(11, 42, 107, 0.15) !important;
    }
    [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea, [data-testid="stNumberInput"] input {
        background: transparent !important; color: var(--ink) !important; font-size: 0.97rem !important;
    }
    [data-testid="stTextArea"] textarea { line-height: 1.7 !important; }
    [data-testid="stTextInput"] [data-baseweb="input"] > div:last-child,
    [data-testid="stTextInput"] button { background: transparent !important; border: none !important; color: var(--muted) !important; }
    [data-testid="stTextInput"] button:hover { color: var(--navy) !important; }

    /* Buttons */
    [data-testid="stBaseButton-secondary"] {
        background: #fff !important; border: 1px solid var(--navy) !important;
        border-left: 5px solid var(--red) !important; border-radius: 8px !important;
        min-height: 46px; padding: 0.5rem 0.9rem !important;
        justify-content: flex-start !important; box-shadow: none !important;
        transition: background 0.15s ease;
    }
    [data-testid="stBaseButton-secondary"] p { color: var(--navy) !important; font-weight: 600 !important; font-size: 0.92rem !important; margin: 0 !important; }
    [data-testid="stBaseButton-secondary"]:hover { background: var(--navy) !important; border-color: var(--navy) !important; border-left-color: var(--red) !important; }
    [data-testid="stBaseButton-secondary"]:hover p { color: #fff !important; }
    [data-testid="stBaseButton-primary"] {
        background: var(--red) !important; border: none !important; border-radius: 10px !important;
        min-height: 48px; padding: 0.6rem 1.6rem !important; box-shadow: none !important;
        transition: background 0.15s ease;
    }
    [data-testid="stBaseButton-primary"] p { color: #fff !important; font-weight: 600 !important; font-size: 0.97rem !important; margin: 0 !important; }
    [data-testid="stBaseButton-primary"]:hover { background: var(--red-dark) !important; }
    .stButton button:focus-visible { outline: 3px solid rgba(11, 42, 107, 0.4) !important; outline-offset: 2px; }

    /* Sidebar: น้ำเงินกรมท่า */
    [data-testid="stSidebar"], [data-testid="stSidebar"] > div { background: var(--navy) !important; border-right: none !important; }
    [data-testid="stSidebarCollapseButton"] *, [data-testid="stSidebarCollapsedControl"] * { color: #ffffff !important; fill: #ffffff !important; }
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"], [data-testid="stSidebar"] [data-testid="stCaptionContainer"] * { color: #b8c6dd !important; }
    [data-testid="stSidebar"] code { background: rgba(255, 255, 255, 0.14) !important; color: #ffffff !important; }
    [data-testid="stSidebar"] hr { border-color: rgba(255, 255, 255, 0.2) !important; }
    .side-title { font-family: var(--serif); font-size: 1.2rem; font-weight: 700; color: #ffffff; margin-bottom: 0.15rem; }
    .side-desc { font-size: 0.85rem; color: #b8c6dd; line-height: 1.5; margin-bottom: 1rem; }
    .api-row { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin: 0.5rem 0 0.15rem; }
    .api-name { font-size: 0.92rem; font-weight: 600; color: #ffffff; white-space: nowrap; }
    .pill { white-space: nowrap; font-size: 0.74rem; font-weight: 600; padding: 0.1rem 0.6rem; border-radius: 999px; flex-shrink: 0; }
    .pill-ok { background: #e8f6ee; color: #11693a; border: 1px solid #b5e0c6; }
    .pill-no { background: #fdecee; color: #b01c30; border: 1px solid #f5c2c9; }
    .api-desc { font-size: 0.82rem; color: #b8c6dd; margin-bottom: 0.5rem; }

    /* ผลวิเคราะห์: ใบข่าว */
    .result-card {
        background: #fff; border: 1px solid var(--rule);
        border-top: 5px solid var(--c); border-radius: 10px;
        padding: 1.4rem 1.75rem 1.5rem; margin: 1.25rem 0 1rem;
    }
    .result-tag {
        display: inline-block; background: var(--navy); color: #fff;
        font-size: 0.8rem; font-weight: 600; padding: 0.15rem 0.7rem;
        border-radius: 4px; margin-bottom: 0.75rem;
    }
    .result-headline {
        font-family: var(--serif); font-size: 1.4rem; font-weight: 700; color: var(--navy);
        line-height: 1.55; margin: 0 0 1.25rem; padding: 0; border: 0;
    }
    .result-main {
        display: flex; align-items: center; gap: 1.25rem; flex-wrap: wrap;
        padding-top: 1.25rem; border-top: 1px solid var(--rule);
    }
    .ring {
        width: 92px; height: 92px; border-radius: 50%; flex-shrink: 0;
        background: conic-gradient(var(--c) calc(var(--p) * 1%), #e4e9f0 0);
        display: flex; align-items: center; justify-content: center;
    }
    .ring-in {
        width: 70px; height: 70px; border-radius: 50%; background: #fff;
        display: flex; align-items: center; justify-content: center;
        font-weight: 600; font-size: 0.98rem; color: var(--navy);
    }
    .result-label { color: var(--muted); font-size: 0.85rem; }
    .result-emotion { font-family: var(--serif); font-size: 1.7rem; font-weight: 700; color: var(--c); line-height: 1.4; }
    .result-conf { color: var(--muted); font-size: 0.85rem; }

    .bars-card { background: #fff; border: 1px solid var(--rule); border-radius: 10px; padding: 1.25rem 1.75rem 1.4rem; margin-bottom: 1rem; }
    .bars-title {
        font-family: var(--serif); font-weight: 700; font-size: 1.02rem; color: var(--navy);
        margin-bottom: 1rem; border-left: 5px solid var(--red); padding-left: 0.6rem;
    }
    .bar-row { display: flex; align-items: center; gap: 12px; margin-bottom: 0.7rem; }
    .bar-row:last-child { margin-bottom: 0; }
    .bar-name { width: 168px; flex-shrink: 0; font-size: 0.9rem; color: var(--ink); display: flex; align-items: center; gap: 8px; }
    .bar-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
    .bar-track { flex: 1; height: 12px; background: #e9edf3; border-radius: 6px; overflow: hidden; }
    .bar-fill { height: 100%; border-radius: 6px; }
    .bar-val { width: 62px; text-align: right; font-size: 0.88rem; font-weight: 600; color: var(--ink); flex-shrink: 0; }
    .bar-row.top .bar-name { font-weight: 600; }

    [data-testid="stExpander"] details { background: #fff; border: 1px solid var(--rule) !important; border-radius: 10px; }

    @media (max-width: 768px) {
        .masthead-body { padding: 1.25rem 1.1rem 1.1rem; }
        .masthead-title { font-size: 1.55rem; }
        .masthead-date { display: none; }
        .result-card, .bars-card { padding: 1.1rem; }
        .result-headline { font-size: 1.15rem; }
        .bar-name { width: 112px; font-size: 0.82rem; }
        .bar-val { width: 54px; font-size: 0.82rem; }
    }
"""

def minify_css(text: str) -> str:
    """ลบคอมเมนต์และบรรทัดว่าง รวมเป็นบรรทัดเดียว กัน Markdown ตัดบล็อก <style> กลางคัน"""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"\s+", " ", text).strip()


st.markdown(f"<style>{minify_css(CSS)}</style>", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# 4. MASTHEAD
# ──────────────────────────────────────────────────────────────
ticker_items = "".join(f"<span>{htmllib.escape(t)}</span>" for _, t in SAMPLE_NEWS)

st.markdown(
    compact(f"""
    <div class="masthead">
        <div class="masthead-body">
            <div class="masthead-top">
                <span class="masthead-badge">Thai AI Intelligence Hub</span>
                <span class="masthead-date">{thai_dateline()}</span>
            </div>
            <h1 class="masthead-title">วิเคราะห์อารมณ์จากพาดหัวข่าว</h1>
            <p class="masthead-sub">ตรวจจับอารมณ์จากข่าวภาษาไทยด้วย AIForThai EmoNews และสนทนาถาม-ตอบกับ ThaiLLM Pathumma 3.0</p>
        </div>
        <div class="ticker">
            <div class="ticker-label">ข่าวตัวอย่าง</div>
            <div class="ticker-window"><div class="ticker-track">{ticker_items}{ticker_items}</div></div>
        </div>
    </div>
    """),
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────
# 5. SIDEBAR
# ──────────────────────────────────────────────────────────────
def api_block(name: str, desc: str, ready: bool) -> str:
    pill = '<span class="pill pill-ok">● พร้อมใช้งาน</span>' if ready else '<span class="pill pill-no">● ยังไม่ระบุ</span>'
    return compact(f"""
        <div class="api-row"><span class="api-name">{name}</span>{pill}</div>
        <div class="api-desc">{desc}</div>
    """)


with st.sidebar:
    st.markdown(
        compact("""
        <div class="side-title">การตั้งค่า API Keys</div>
        <div class="side-desc">จัดเก็บสิทธิ์การเข้าถึงบริการภายนอก (บันทึกไว้ในเซสชัน)</div>
        """),
        unsafe_allow_html=True,
    )

    # สถานะ "พร้อมใช้งาน" อิงจากค่าที่กรอกอยู่จริง ไม่ใช่แค่ค่าใน .env
    ai_slot = st.empty()
    aiforthai_key = st.text_input(
        "AIForThai API Key", value=AIFORTHAI_KEY_DEFAULT, type="password",
        placeholder="กรอกคีย์ AIForThai...", label_visibility="collapsed", key="sb_aiforthai",
    )
    ai_slot.markdown(
        api_block("AIForThai EmoNews", "วิเคราะห์อารมณ์หัวข้อข่าว (สวทช.)", bool(aiforthai_key.strip())),
        unsafe_allow_html=True,
    )

    st.write("")

    llm_slot = st.empty()
    thaillm_key = st.text_input(
        "ThaiLLM API Key", value=THAILLM_KEY_DEFAULT, type="password",
        placeholder="กรอกคีย์ ThaiLLM...", label_visibility="collapsed", key="sb_thaillm",
    )
    llm_slot.markdown(
        api_block("ThaiLLM Pathumma", "โมเดลภาษาไทย Pathumma 3.0", bool(thaillm_key.strip())),
        unsafe_allow_html=True,
    )

    st.divider()
    st.caption("ค่าเริ่มต้นโหลดจากไฟล์ `.env` อัตโนมัติ")

# ──────────────────────────────────────────────────────────────
# 6. TABS
# ──────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["วิเคราะห์อารมณ์ข่าว (EmoNews)", "สหายสนทนาปทุมมา (ThaiLLM)"])

# session_state ทำให้ปุ่มตัวอย่างเติมข้อความลงช่องได้ทันที
st.session_state.setdefault("news_text", DEFAULT_HEADLINE)
st.session_state.setdefault("chat_text", DEFAULT_CHAT)


def set_state(key: str, value: str):
    st.session_state[key] = value


# ══════════════ TAB 1: EmoNews ══════════════
with tab1:
    st.markdown(
        compact("""
        <div class="section-head">วิเคราะห์มิติอารมณ์จากหัวข้อข่าว</div>
        <div class="section-desc">ป้อนพาดหัวข่าวภาษาไทยเพื่อประเมินความรู้สึกเชิงลึกของผู้รับสาร</div>
        <div class="field-label">ตัวอย่างข่าวทดสอบ</div>
        """),
        unsafe_allow_html=True,
    )

    r1a, r1b = st.columns(2)
    r2a, r2b = st.columns(2)
    for col, (idx, (label, text)) in zip((r1a, r1b, r2a, r2b), enumerate(SAMPLE_NEWS)):
        with col:
            st.button(label, use_container_width=True, key=f"btn_sample_{idx}",
                      on_click=set_state, args=("news_text", text))

    news_text = st.text_area(
        "ข้อความพาดหัวข่าว:", key="news_text", height=95,
        placeholder="พิมพ์หรือวางข้อความพาดหัวข่าวที่ต้องการวิเคราะห์...",
    )

    col_btn, col_info = st.columns([1.3, 3.7])
    with col_btn:
        btn_analyze = st.button("วิเคราะห์อารมณ์", type="primary", use_container_width=True)
    with col_info:
        st.caption(f"จำนวนตัวอักษร: {len(news_text)} ตัว")

    if btn_analyze:
        cleaned_headline = news_text.strip()
        if not cleaned_headline:
            st.warning("กรุณาระบุข้อความพาดหัวข่าวก่อนเริ่มวิเคราะห์")
        elif not aiforthai_key.strip():
            st.error("กรุณาระบุ AIForThai API Key ในแถบเมนูด้านข้างก่อนใช้งาน")
        else:
            headers = {"apikey": aiforthai_key.strip()}
            params = {"text": cleaned_headline}

            with st.spinner("กำลังประมวลผลผ่าน AIForThai EmoNews..."):
                try:
                    res = requests.get(EMONEWS_URL, headers=headers, params=params, timeout=15)
                    if res.status_code == 200:
                        data = res.json()

                        results = None
                        if isinstance(data, dict):
                            if "result" in data and isinstance(data["result"], dict):
                                results = data["result"]
                            elif data.get("status") == "success" and "result" in data:
                                results = data["result"]
                            elif any(isinstance(v, (int, float)) for v in data.values()):
                                results = {k: v for k, v in data.items() if isinstance(v, (int, float))}

                        if results:
                            top_key = max(results, key=results.get)
                            top_score = float(results[top_key])
                            top = emo_info(top_key)
                            pct = max(min(top_score * 100, 100), 0)

                            # ใบข่าว: พาดหัว + อารมณ์เด่น + วงกลมความมั่นใจ
                            st.markdown(
                                compact(f"""
                                <div class="result-card" style="--c: {top['color']}; --p: {pct:.1f};">
                                    <div class="result-tag">พาดหัวข่าวที่วิเคราะห์</div>
                                    <blockquote class="result-headline">{htmllib.escape(cleaned_headline)}</blockquote>
                                    <div class="result-main">
                                        <div class="ring"><div class="ring-in">{pct:.1f}%</div></div>
                                        <div>
                                            <div class="result-label">อารมณ์เด่นของพาดหัวนี้</div>
                                            <div class="result-emotion">{top['thai']}</div>
                                            <div class="result-conf">{top['en']} · ความมั่นใจ {top_score:.2%}</div>
                                        </div>
                                    </div>
                                </div>
                                """),
                                unsafe_allow_html=True,
                            )

                            # แท่งสัดส่วนทุกอารมณ์ เรียงมาก → น้อย
                            rows = []
                            sorted_results = sorted(results.items(), key=lambda x: float(x[1]), reverse=True)
                            for i, (k, v) in enumerate(sorted_results):
                                info = emo_info(k)
                                score = float(v)
                                width = max(min(score * 100, 100), 1.5)
                                rows.append(f"""
                                    <div class="bar-row{' top' if i == 0 else ''}">
                                        <div class="bar-name"><span class="bar-dot" style="background:{info['color']}"></span>{info['thai']}</div>
                                        <div class="bar-track"><div class="bar-fill" style="width:{width:.1f}%; background:{info['color']}"></div></div>
                                        <div class="bar-val">{score:.2%}</div>
                                    </div>
                                """)
                            st.markdown(
                                compact(f"""
                                <div class="bars-card">
                                    <div class="bars-title">สัดส่วนคะแนนความเชื่อมั่นของแต่ละอารมณ์</div>
                                    {''.join(rows)}
                                </div>
                                """),
                                unsafe_allow_html=True,
                            )

                            with st.expander("ดูข้อมูลดิบ (Raw JSON Response)"):
                                st.json(data)
                        else:
                            st.warning("ได้รับผลตอบกลับ แต่ไม่พบโครงสร้างข้อมูลอารมณ์ที่รองรับ")
                            st.json(data)
                    else:
                        st.error(f"เซิร์ฟเวอร์ตอบกลับรหัสข้อผิดพลาด ({res.status_code}): {res.text}")
                except requests.exceptions.Timeout:
                    st.error("การเชื่อมต่อหมดเวลา (Timeout) กรุณาลองใหม่อีกครั้ง")
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาด: {e}")

# ══════════════ TAB 2: ThaiLLM ══════════════
with tab2:
    st.markdown(
        compact("""
        <div class="section-head">สนทนากับสหายปทุมมา (Pathumma 3.0)</div>
        <div class="section-desc">โมเดลภาษาไทยตอบคำถาม สรุปความ และให้คำแนะนำอย่างเป็นธรรมชาติ</div>
        <div class="field-label">ตัวอย่างหัวข้อสนทนา</div>
        """),
        unsafe_allow_html=True,
    )

    cols = st.columns(3)
    for col, (idx, (label, text)) in zip(cols, enumerate(SAMPLE_PROMPTS)):
        with col:
            st.button(label, use_container_width=True, key=f"btn_prompt_{idx}",
                      on_click=set_state, args=("chat_text", text))

    col_text, col_opts = st.columns([3, 1.2])
    with col_text:
        chat_input = st.text_area(
            "ข้อความหรือคำถามที่ต้องการสนทนา:", key="chat_text", height=140,
            placeholder="พิมพ์เรื่องราว คำถาม หรือคำสั่งที่ต้องการให้ปทุมมาช่วย...",
        )
    with col_opts:
        st.markdown('<div class="field-label">การปรับแต่ง</div>', unsafe_allow_html=True)
        temperature = st.slider(
            "ความคิดสร้างสรรค์ (Temp)", min_value=0.0, max_value=1.0, value=0.35, step=0.05,
            help="ค่าน้อย = แม่นยำ สุขุม | ค่ามาก = หลากหลาย สร้างสรรค์",
        )
        max_tokens = st.number_input("ความยาวสูงสุด (Tokens)", min_value=128, max_value=4096, value=2048, step=128)

    btn_send_chat = st.button("ส่งข้อความถึงปทุมมา", type="primary")

    if btn_send_chat:
        cleaned_chat = chat_input.strip()
        if not cleaned_chat:
            st.warning("กรุณาระบุข้อความก่อนส่ง")
        elif not thaillm_key.strip():
            st.error("กรุณาระบุ ThaiLLM API Key ในแถบเมนูด้านข้างก่อนส่งข้อความ")
        else:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {thaillm_key.strip()}",
            }
            payload = {
                "model": "pathumma-thaillm-qwen3-8b-think-3.0.0",
                "messages": [
                    {
                        "role": "system",
                        "content": "คุณคือสหายปัญญาประดิษฐ์นามว่าปทุมมา ผู้มีความสุภาพ อบอุ่น เป็นมิตร และรักในความก้าวหน้า ตอบคำถามเป็นภาษาไทยอย่างสละสลวย ชัดเจน และอ่านเข้าใจง่าย ใช้ Markdown เพื่อจัดระเบียบเนื้อหาให้น่าอ่าน",
                    },
                    {"role": "user", "content": cleaned_chat},
                ],
                "max_tokens": int(max_tokens),
                "temperature": float(temperature),
            }

            with st.spinner("สหายปทุมมากำลังคิดและเรียบเรียงคำตอบ..."):
                try:
                    res, used_url = post_thaillm(headers, payload)
                    if res.status_code == 200:
                        result = res.json()
                        choice = result["choices"][0]
                        message = choice.get("message", {})
                        think_content, actual_reply = split_think(message.get("content") or "")
                        if not think_content:
                            think_content = (message.get("reasoning_content") or message.get("reasoning") or "").strip()

                        st.markdown('<div class="section-head" style="margin-top:1rem">คำตอบจากสหายปทุมมา</div>',
                                    unsafe_allow_html=True)

                        if think_content:
                            with st.expander("ดูกระบวนการคิด", expanded=False):
                                st.markdown(think_content)

                        if actual_reply:
                            with st.container(border=True):
                                st.markdown(actual_reply)
                            if choice.get("finish_reason") == "length":
                                st.caption("คำตอบอาจถูกตัดเพราะถึงขีดจำกัด Tokens ลองเพิ่มค่าความยาวสูงสุด")
                        else:
                            st.warning("โมเดลยังไม่ได้เขียนคำตอบสุดท้าย (ใช้ Tokens หมดระหว่างคิด) ลองเพิ่มค่า ความยาวสูงสุด (Tokens) แล้วส่งใหม่")

                        st.caption(f"เชื่อมต่อผ่าน {used_url}")
                        with st.expander("ดูข้อมูลดิบ (Raw JSON Response)"):
                            st.json(result)
                    else:
                        st.error(f"เซิร์ฟเวอร์ตอบกลับรหัสผิดพลาด ({res.status_code}): {res.text}")
                        if res.status_code in (401, 403):
                            st.info("ตรวจสอบ ThaiLLM API Key อีกครั้ง ตัวพิมพ์เล็ก-ใหญ่ต้องตรงทุกตัวอักษร แนะนำให้คัดลอกจากหน้าผู้ให้บริการโดยตรง")
                except requests.exceptions.Timeout:
                    st.error("การตอบกลับใช้เวลานานเกินกำหนด กรุณาลองใหม่อีกครั้ง")
                except Exception as e:
                    st.error(f"การเชื่อมต่อขัดข้อง: {e}")
