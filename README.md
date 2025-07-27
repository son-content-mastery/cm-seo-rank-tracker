# ระบบติดตาม SEO Rank Tracker

แอปพลิเคชันติดตามอันดับ SEO ที่สร้างด้วย Python Flask, PostgreSQL และ Celery สำหรับการติดตามอันดับคำหลักอัตโนมัติ รายงานอีเมล และการวิเคราะห์ข้อมูล

## ฟีเจอร์หลัก

- **ติดตามอันดับอัตโนมัติ**: ตรวจสอบรายสัปดาห์โดยใช้ SerpAPI
- **รายงานอีเมล**: รายงาน HTML สวยงามพร้อมการเปลี่ยนแปลงอันดับ
- **แดชบอร์ดเว็บ**: ดูอันดับปัจจุบันและการเปลี่ยนแปลงแบบเรียลไทม์
- **REST API**: จุดเชื่อมต่อ JSON สำหรับการรวมระบบภายนอก
- **การประมวลผลเบื้องหลัง**: ประมวลผลแบบอะซิงค์ด้วย Celery
- **พร้อมใช้ Docker**: การปรับใช้แบบคอนเทนเนอร์สมบูรณ์
- **วิเคราะห์ตำแหน่ง**: ติดตามการปรับปรุง การลดลง และประวัติอันดับ
- **การจำกัดอัตรา**: การปฏิบัติตามการจำกัดอัตรา API ในตัว

## เริ่มต้นใช้งาน

### สิ่งที่ต้องเตรียมพร้อม (Prerequisite)

- Docker และ Docker Compose
- บัญชี SerpAPI และ API key
- บัญชี Gmail พร้อม app password (สำหรับรายงานอีเมล)

### 1. โคลนและตั้งค่า

```bash
# โคลนโครงการ
git clone <your-repo-url>
cd seo-rank-tracker

# คัดลอกไฟล์ environment
cp .env.example .env

# แก้ไข .env ด้วยการกำหนดค่าของคุณ
nano .env
```

### 2. กำหนดค่า Environment

อัปเดต `.env` ด้วยการตั้งค่าของคุณ:

```bash
# จำเป็น: SerpAPI key
SERPAPI_KEY=your_serpapi_key_here

# จำเป็น: ข้อมูลประจำตัว Gmail
GMAIL_USER=your-email@gmail.com
GMAIL_PASSWORD=your_gmail_app_password

# จำเป็น: โดเมนและอีเมลของคุณ
TARGET_DOMAIN=yourwebsite.com
RECIPIENT_EMAIL=your-email@gmail.com

# สร้าง secret key
SECRET_KEY=your_secret_key_here
```

### 3. ปรับใช้ด้วย Docker

```bash
# เริ่มบริการทั้งหมด
docker-compose up -d

# ตรวจสอบ logs
docker-compose logs -f

# เข้าถึงแอปพลิเคชัน
open http://localhost:5000
```

## โครงสร้างแอปพลิเคชัน

```
seo-rank-tracker/
├── docker-compose.yml          # การกำหนดค่าบริการ Docker
├── Dockerfile                  # คอนเทนเนอร์แอปพลิเคชัน
├── requirements.txt           # การพึ่งพา Python
├── .env.example              # เทมเพลต Environment
├── app/
│   ├── __init__.py           # Flask application factory
│   ├── config.py             # การตั้งค่าการกำหนดค่า
│   ├── models.py             # โมเดลฐานข้อมูล
│   ├── routes.py             # เส้นทางเว็บและจุดเชื่อมต่อ API
│   ├── tasks.py              # งาน Celery เบื้องหลัง
│   ├── templates/            # เทมเพลต HTML
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   └── keywords.html
│   ├── email_templates/      # เทมเพลตอีเมล
│   │   └── weekly_report.html
│   └── utils/                # โมดูลยูทิลิตี้
│       ├── serpapi_client.py # การรวม SerpAPI
│       ├── email_sender.py   # ฟังก์ชันอีเมล
│       └── report_generator.py # การสร้างรายงาน
└── migrations/
    └── init.sql              # สคีมาฐานข้อมูล
```

## 🔧 การกำหนดค่า

### ตัวแปร Environment

| ตัวแปร | คำอธิบาย | จำเป็น | ค่าเริ่มต้น |
|----------|-------------|----------|---------|
| `SERPAPI_KEY` | SerpAPI key ของคุณ | ใช่ | - |
| `GMAIL_USER` | ที่อยู่ Gmail สำหรับส่งรายงาน | ใช่ | - |
| `GMAIL_PASSWORD` | รหัสผ่านแอป Gmail | ใช่ | - |
| `TARGET_DOMAIN` | โดเมนที่จะติดตามอันดับ | ใช่ | yourwebsite.com |
| `RECIPIENT_EMAIL` | อีเมลสำหรับรับรายงาน | ใช่ | - |
| `SECRET_KEY` | Flask secret key | ใช่ | - |
| `DATABASE_URL` | สตริงการเชื่อมต่อ PostgreSQL | ไม่ | กำหนดค่าอัตโนมัติ |
| `REDIS_URL` | สตริงการเชื่อมต่อ Redis | ไม่ | กำหนดค่าอัตโนมัติ |

### การกำหนดค่าคำหลัก

คำหลักเริ่มต้นถูกกำหนดค่าใน `app/config.py` คุณสามารถ:

1. **แก้ไขไฟล์ config** เพื่อเปลี่ยน keywords ที่ต้องการ
2. **ใช้อินเทอร์เฟซเว็บ** เพื่อเพิ่ม/ลบคำหลัก
3. **ใช้ตัวแปร environment** (เพิ่ม `CUSTOM_KEYWORDS=keyword1,keyword2,keyword3`)

## การใช้งาน

### แดชบอร์ดเว็บ

เข้าถึงแดชบอร์ดที่ `http://localhost:5000`:

- **แดชบอร์ด**: ดูอันดับปัจจุบันและการเปลี่ยนแปลง
- **คำหลัก**: จัดการ keywords ที่กำลัง track
- **การตรวจสอบแบบแมนนวล**: เรียกการตรวจสอบอันดับทันที
- **ส่งรายงาน**: สร้างและส่งรายงานอีเมล

### จุดเชื่อมต่อ API

| จุดเชื่อมต่อ | วิธี | คำอธิบาย |
|----------|--------|-------------|
| `/api/rankings` | GET | อันดับปัจจุบัน (JSON) |
| `/api/keyword/{id}/history` | GET | ประวัติอันดับคำหลัก |
| `/health` | GET | การตรวจสอบสุขภาพแอปพลิเคชัน |
| `/trigger-check` | POST | การตรวจสอบอันดับแบบแมนนวล |
| `/send-report` | POST | ส่งรายงานอีเมล |

### ตัวอย่างการใช้งาน API

```bash
# รับอันดับปัจจุบัน
curl http://localhost:5000/api/rankings

# รับประวัติคำหลัก
curl http://localhost:5000/api/keyword/1/history?days=30

# ตรวจสอบสุขภาพ
curl http://localhost:5000/health
```

## Email Report

รายงานอีเมลรายสัปดาห์ประกอบด้วย:

- **สถิติสรุป**: คำหลักทั้งหมด อัตราความครอบคลุม ตำแหน่งเฉลี่ย
- **การวิเคราะห์การเปลี่ยนแปลง**: การปรับปรุง การลดลง อันดับใหม่
- **ตารางรายละเอียด**: คำหลักทั้งหมดพร้อมตำแหน่งและการเปลี่ยนแปลง
- **ตัวบ่งชี้ภาพ**: ตัวบ่งชี้การเปลี่ยนแปลงแบบสีรหัส

รายงานจะถูกส่งอัตโนมัติทุกวันจันทร์เวลา 9.00 น. UTC

## การจัดตารางเวลา

แอปพลิเคชันใช้ Celery Beat สำหรับการจัดตารางเวลา:

- **การตรวจสอบอันดับรายสัปดาห์**: วันจันทร์ 9:00 น. UTC
- **การทำความสะอาดข้อมูล**: วันอาทิตย์ 2:00 น. UTC (ลบข้อมูลที่เก่ากว่า 365 วัน)

### การดำเนินการแบบแมนนวล

```bash
# รันการตรวจสอบแบบแมนนวล
docker-compose exec web python -c "from app.tasks import run_manual_check; run_manual_check()"

# รันการทำความสะอาด
docker-compose exec web python -c "from app.tasks import run_manual_cleanup; run_manual_cleanup()"
```

## Database Schema

### ตาราง

- **keywords**: เก็บคำหลักที่ติดตาม
- **rankings**: ข้อมูลอันดับรายวัน
- **ranking_changes**: ประวัติการเปลี่ยนแปลงตำแหน่ง

### คุณสมบัติหลัก

- **การสร้างดัชนีอัตโนมัติ** เพื่อประสิทธิภาพการสืบค้นที่เหมาะสม
- **มุมมองฐานข้อมูล** สำหรับการสืบค้นที่ซับซ้อน
- **ฟังก์ชัน** สำหรับการคำนวณทางสถิติ
- **ข้อจำกัด** สำหรับความสมบูรณ์ของข้อมูล

## Development

### การพัฒนาในเครื่อง (Local Development)

```bash
# ติดตั้งการพึ่งพา
pip install -r requirements.txt

# ตั้งค่าฐานข้อมูลในเครื่อง
createdb seo_tracker
psql seo_tracker < migrations/init.sql

# รันเซิร์ฟเวอร์การพัฒนา Flask
export FLASK_APP=app
export FLASK_ENV=development
flask run

# รัน Celery worker (เทอร์มินัลแยก)
celery -A app.tasks worker --loglevel=info

# รัน Celery beat (เทอร์มินัลแยก)
celery -A app.tasks beat --loglevel=info
```

### การเพิ่มคุณสมบัติ

1. **โมเดล**: เพิ่มตารางใหม่ใน `app/models.py`
2. **เส้นทาง**: เพิ่มจุดเชื่อมต่อใน `app/routes.py`
3. **งาน**: เพิ่มงานเบื้องหลังใน `app/tasks.py`
4. **เทมเพลต**: เพิ่มเทมเพลต HTML ใน `app/templates/`
5. **ยูทิลิตี้**: เพิ่มยูทิลิตี้ใน `app/utils/`

## การแก้ไขปัญหา

### ปัญหาทั่วไป

**ปัญหา API Key**
```bash
# ตรวจสอบ SerpAPI key
curl "https://serpapi.com/account" -H "Authorization: Bearer YOUR_API_KEY"
```

**ปัญหาอีเมล**
```bash
# ทดสอบข้อมูลประจำตัว Gmail
python -c "import smtplib; smtplib.SMTP('smtp.gmail.com', 587).starttls()"
```

**ปัญหาฐานข้อมูล**
```bash
# ตรวจสอบการเชื่อมต่อฐานข้อมูล
docker-compose exec db psql -U seo_user -d seo_tracker -c "SELECT COUNT(*) FROM keywords;"
```

**ปัญหา Celery**
```bash
# ตรวจสอบสถานะ Celery
docker-compose exec worker celery -A app.tasks status
docker-compose exec scheduler celery -A app.tasks beat --dry-run
```

### บันทึก

```bash
# บันทึกแอปพลิเคชัน
docker-compose logs web

# บันทึก Worker
docker-compose logs worker

# บันทึก Scheduler
docker-compose logs scheduler

# บันทึกฐานข้อมูล
docker-compose logs db
```

## การปรับปรุงประสิทธิภาพ

### การจำกัดอัตรา

- การเรียก SerpAPI ถูกจำกัดอัตราเป็น 1.2 วินาทีระหว่างการร้องขอ
- กำหนดค่าได้ผ่านตัวแปร environment `SERPAPI_RATE_LIMIT`
- การประมวลผลแบบแบทช์สำหรับคำหลักหลายคำ

### การปรับปรุงฐานข้อมูล

- การทำความสะอาดข้อมูลเก่าอัตโนมัติ (365+ วัน)
- การสืบค้นที่มีดัชนีสำหรับการค้นหาที่รวดเร็ว
- มุมมองฐานข้อมูลสำหรับการรายงานที่ซับซ้อน

### การตรวจสอบ

- จุดเชื่อมต่อการตรวจสอบสุขภาพที่ `/health`
- การบันทึกที่ครอบคลุมทั่วทั้งแอปพลิเคชัน
- การตรวจสอบงานผ่าน Celery

## 🔒 ข้อควรพิจารณาด้านความปลอดภัย (Security Concern)

- **ตัวแปร Environment**: อย่าคอมมิตไฟล์ `.env`
- **API Keys**: ใช้ตัวแปร environment เท่านั้น
- **ฐานข้อมูล**: ใช้รหัสผ่านที่แข็งแกร่ง
- **อีเมล**: ใช้รหัสผ่านแอป Gmail ไม่ใช่รหัสผ่านบัญชี
- **เครือข่าย**: พิจารณากฎไฟร์วอลล์สำหรับการใช้งานจริง

## ใบอนุญาต

โครงการนี้ได้รับอนุญาตภายใต้ MIT License - ดูไฟล์ LICENSE สำหรับรายละเอียด

## 🤝 การมีส่วนร่วม

1. Fork repository
2. สร้าง feature branch
3. ทำการเปลี่ยนแปลงของคุณ
4. เพิ่มการทดสอบหากเหมาะสม
5. ส่ง pull request

## การสนับสนุน

สำหรับปัญหาและคำถาม:

1. ตรวจสอบ README นี้
2. ตรวจสอบบันทึกแอปพลิเคชัน
3. ตรวจสอบส่วนการแก้ไขปัญหา
4. เปิด issue บน GitHub

---

**Created by Son [contentmastery.io](https://contentmastery.io)**
