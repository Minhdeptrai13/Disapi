# dapi — Discord User API Wrapper Production-Grade

<div align="center">

![dapi](https://img.shields.io/badge/dapi-Production%20Ready-5865F2?style=for-the-badge&logo=discord&logoColor=white)

**Async-First • Realistic Fingerprinting • Full Gateway • Type-Safe**

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Async-First](https://img.shields.io/badge/async-first-brightgreen)](https://docs.python.org/3/library/asyncio.html)

**Siêu mạnh • Fingerprint cực thật • Production Ready**

</div>

---

## ⚠️ Cảnh Báo Điều Khoản Dịch Vụ

**Sử dụng selfbot (tự động hóa tài khoản người dùng) vi phạm nghiêm trọng [Điều khoản Dịch vụ](https://discord.com/terms) và [Hướng dẫn Cộng đồng](https://discord.com/guidelines) của Discord.**

- ❌ Tài khoản có nguy cơ **bị khóa vĩnh viễn** không báo trước.
- ❌ Discord đang liên tục cải tiến hệ thống phát hiện.
- **Thư viện này chỉ dành cho mục đích giáo dục và nghiên cứu.**

**Tác giả không chịu bất kỳ trách nhiệm nào** nếu tài khoản của bạn bị ban hoặc gặp vấn đề. Sử dụng hoàn toàn **tại rủi ro của riêng bạn**.

---

## ✨ Tính Năng Nổi Bật

### Core
- ✅ **Async-First** với `httpx` + `asyncio` + `websockets`
- ✅ **Full Type Hints** & hỗ trợ mypy
- ✅ **Context Manager** an toàn
- ✅ **Production-Grade** error handling & logging

### Fingerprinting Siêu Thực
- Browser Headers mới nhất (Chrome 131 / Edge 131 / Firefox 133 - 2026)
- Super-Properties giống hệt Discord Web
- Sec-CH-UA Client Hints
- User-Agent Rotation ngẫu nhiên
- Realistic Build Number

### HTTP REST API
- Modular API design
- **Smart Rate Limiting** (Global + Per-bucket)
- Auto-retry + Exponential backoff + Jitter
- Hỗ trợ HTTP/SOCKS5 Proxy

### Gateway WebSocket
- Full IDENTIFY & RESUME
- Auto-reconnect thông minh
- Heartbeat tracking + Latency
- Zlib Compression
- Event decorator `@client.event()`
- Lazy Guild Loading

### Models & Type Safety
- TypedDict Models đầy đủ
- Automatic data validation
- Snowflake ID & Timestamp handling

---

## 📦 Cài Đặt

### Từ PyPI
```bash
pip install dapi
Từ Source (Development)
Bashgit clone https://github.com/Minhdeptrai13/dapi.git
cd dapi
pip install -e ".[dev]"

🎬 Hướng Dẫn Nhanh
Async Style (Khuyến nghị)
Pythonimport asyncio
from dapi import Client

async def main():
    async with Client("YOUR_TOKEN_HERE") as client:
        user = await client.login()
        print(f"✅ Logged in as {user.username}#{user.discriminator}")

        # Gửi tin nhắn
        await client.messages.send("channel_id", "Hello World! ⚡")

        # Set presence
        await client.presence.set_custom_status("Running with dapi 🔥")

asyncio.run(main())
Sync Style
Pythonfrom dapi import SyncClient

with SyncClient("YOUR_TOKEN_HERE") as client:
    client.login()
    client.messages.send("channel_id", "Hello from dapi!")
    client.presence.set_status("idle")

📚 Ví Dụ
1. Gửi Embed
Pythonawait client.messages.send(
    "channel_id",
    content="Check this out!",
    embed={
        "title": "dapi is Awesome",
        "description": "Production-grade Discord selfbot library",
        "color": 0x5865F2,
        "fields": [
            {"name": "Async", "value": "✅ Full async support", "inline": True},
            {"name": "Fingerprint", "value": "✅ Extremely realistic", "inline": True},
        ]
    }
)
2. Event Listener
Python@client.event("message_create")
async def on_message(event: dict):
    content = event["d"]["content"]
    channel_id = event["d"]["channel_id"]
    
    if "dapi" in content.lower():
        await client.messages.send(channel_id, "Tôi đây! 🚀")
3. Proxy & Options
Pythonfrom dapi import Client, ClientOptions

options = ClientOptions(
    proxy="http://127.0.0.1:8080",
    timeout=30.0,
    debug=True,
    enable_gateway=True,
)

async with Client("token", options=options) as client:
    ...

📖 API Reference
Authentication & User

await client.login()
await client.get_current_user()

Messages

client.messages.send()
client.messages.edit()
client.messages.delete()
client.messages.bulk_delete()

Presence

client.presence.set_status("online" | "idle" | "dnd" | "invisible")
client.presence.set_custom_status("text")

Gateway

await client.connect_gateway()
@client.event("event_name")


🏗️ Kiến Trúc
textdapi/
├── client.py
├── http_client.py
├── gateway.py
├── rate_limiter.py
├── constants.py
├── exceptions.py
├── api/           # messages, users, guilds...
├── models/        # User, Message, Guild...
└── utils.py

⚙️ Cấu Hình Nâng Cao
Pythonoptions = ClientOptions(
    proxy=None,
    timeout=30.0,
    max_retries=5,
    debug=False,
    enable_gateway=True,
    gateway_intents=33281,
    auto_reconnect=True,
)

🔧 Khắc Phục Sự Cố

InvalidToken: Kiểm tra token sạch (không khoảng trắng)
Rate Limited: Thư viện đã tự xử lý
Gateway disconnect: Bật auto_reconnect=True
Proxy lỗi: Kiểm tra format http:// hoặc socks5://


🤝 Contribution
Mừng đón Pull Request!

Fork project
Tạo branch mới
Commit thay đổi
Push & mở PR


📝 License
MIT License — Xem file LICENSE


Made with ❤️ for the Python Discord Community
⭐ Star Repository •
🐛 Report Issue •
💬 Discussions