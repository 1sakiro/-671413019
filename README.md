# 📰 Thai AI Intelligence Hub (AIForThai EmoNews + ThaiLLM Pathumma)

เว็บแอปพลิเคชันสำหรับวิเคราะห์อารมณ์หัวข้อข่าวและสนทนาถาม-ตอบด้วย AI สัญชาติไทย พัฒนาด้วย **Python** และ **Streamlit**

---

## 🌟 ฟีเจอร์หลัก (Features)

1. **Tab 1: AIForThai EmoNews (วิเคราะห์อารมณ์ข่าว)** 📊
   - กรอกหัวข้อข่าวภาษาไทยเพื่อประเมินอารมณ์ 7 รูปแบบ
   - แสดงอารมณ์หลักด้วยการ์ด Metric
   - แสดงกราฟแท่งเปรียบเทียบคะแนนความเชื่อมั่นของแต่ละอารมณ์ด้วย `st.bar_chart`
   - ดูข้อมูลผลลัพธ์แบบ Raw JSON จาก API
   - Endpoint: `https://api.aiforthai.in.th/emonews/prediction` (GET)
   - Header: `apikey`

2. **Tab 2: ThaiLLM (Pathumma AI Chat)** 🤖
   - พูดคุย สอบถาม และสั่งให้โมเดลช่วยเขียนหรือวิเคราะห์เนื้อหา
   - ขับเคลื่อนด้วยโมเดลภาษาไทย **Pathumma 3.0** (`pathumma-thaillm-qwen3-8b-think-3.0.0`)
   - รองรับการแสดงผล Markdown และดูข้อมูล Raw JSON Response
   - Endpoint: `http://thaillm.or.th/api/v1/chat/completions` (POST)
   - Header: `Authorization: Bearer <THAILLM_KEY>`

3. **Sidebar สำหรับตั้งค่า API Keys** 🔑
   - สามารถระบุหรือแก้ไข API Keys ของทั้งสองระบบผ่านหน้า Sidebar ได้ทันที หรือโหลดจากไฟล์ `.env`

---

## 📂 โครงสร้างโปรเจกต์ (Project Structure)

```text
├── app.py              # แอปพลิเคชัน Streamlit หลัก (EmoNews + ThaiLLM)
├── requirements.txt    # รายการ Dependencies (streamlit, requests, pandas, python-dotenv)
├── .env.example        # ไฟล์ตัวอย่างสำหรับการตั้งค่า API Keys
├── .gitignore          # ละเว้นไฟล์ที่ไม่ต้องการ commit ขึ้น Git
└── README.md           # เอกสารคู่มือการติดตั้งและการใช้งาน
```

---

## 🚀 การติดตั้งและรันในเครื่อง (Local Setup)

### 1. โคลนคลังโค้ด (Clone Repository)
```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>
```

### 2. ติดตั้ง Dependencies
```bash
pip install -r requirements.txt
```

### 3. ตั้งค่า API Keys ใน `.env` (ทางเลือก)
คัดลอกไฟล์ `.env.example` เป็น `.env`:
```bash
copy .env.example .env    # Windows
cp .env.example .env      # Linux / macOS
```
กำหนดค่าคีย์ของคุณ:
```env
AIFORTHAI_API_KEY=JI1yMBilkSsDnaM2ovkKcJ7BuUbcgZ0e
THAILLM_API_KEY=gmFxQWdOIxSnMQjvKcUqJhuRkk5b3PEs
```

### 4. สั่งรันแอปพลิเคชัน
```bash
streamlit run app.py
```
เปิดเบราว์เซอร์ไปที่ `http://localhost:8501`

---

## ☁️ การนำขึ้น GitHub & Streamlit Community Cloud (Deployment Guide)

### 1. Commit และ Push ขึ้น GitHub
```bash
git init
git add .
git commit -m "feat: Add EmoNews and ThaiLLM Pathumma Streamlit app"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo-name>.git
git push -u origin main
```

### 2. Deploy บน Streamlit Community Cloud
1. ไปที่ [share.streamlit.io](https://share.streamlit.io/) แล้วล็อกอินด้วย GitHub
2. เลือก Repository และ Branch: `main`, Main file path: `app.py`
3. ในส่วน **Advanced settings -> Secrets** ระบุ:
   ```toml
   AIFORTHAI_API_KEY = "JI1yMBilkSsDnaM2ovkKcJ7BuUbcgZ0e"
   THAILLM_API_KEY = "gmFxQWdOIxSnMQjvKcUqJhuRkk5b3PEs"
   ```
4. กด **Deploy!**
