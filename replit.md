# Telegram Reminder Bot

## Tổng quan
Bot Telegram nhắc hạn thanh toán với tính năng mã hóa AES-256 để lưu trữ mật khẩu và 2FA cho từng farm/khách hàng. 

**Version hiện tại: 1.2.0**

Hỗ trợ lưu trữ đầy đủ thông tin:
- Mật khẩu email (mã hóa)
- Mã 2FA (mã hóa)  
- Ghi chú (mã hóa)
- Ngày tham gia
- Thời gian sử dụng (số ngày)
- Facebook khách hàng

**Tính năng nút copy nhanh:**
- Copy email, password, 2FA chỉ bằng 1 nút bấm
- Inline keyboard buttons hiện trực tiếp trên tin nhắn

## Ngày tạo
15/11/2025

## Thay đổi gần đây
### 15/11/2025 - Cập nhật version 1.2.0 - Nút Copy nhanh
- **Tính năng mới**: Thêm inline keyboard buttons để copy nhanh:
  - Trong `/xem_farm`: Nút 📋 Copy Email cho chủ và từng thành viên
  - Trong `/get_mail_login`: 3 nút copy riêng biệt:
    - 📋 Copy Email
    - 📋 Copy Password  
    - 📋 Copy 2FA
- Callback handler xử lý các nút bấm
- Gửi dữ liệu dưới dạng `<code>` để dễ copy trong Telegram

### 15/11/2025 - Cập nhật version 1.1.0 với tính năng mới
- **Tính năng mới**: Thêm thông tin chi tiết cho mỗi email login:
  - 📅 Ngày tham gia (join_date)
  - 🕒 Số ngày sử dụng (usage_days)
  - 👤 Facebook khách hàng (facebook)
- Cập nhật flows `/set_mail_login` và `/get_mail_login`
- Tất cả thông tin nhạy cảm (password, 2FA, note) vẫn được mã hóa AES-256
- Thông tin mới (ngày tham gia, thời gian dùng, Facebook) được lưu không mã hóa

### 15/11/2025 - Sửa lỗi state management (đã fix)
- Sửa lỗi trong flows `/set_mail_login`, `/get_mail_login`, và `/sua_farm`
- Vấn đề: Khi thay đổi step trong state, code không lưu data ngay
- Giải pháp: Thêm `save_data(data)` sau mỗi lần thay đổi `state["step"]`

## Cấu trúc dự án
- `bot.py`: File chính chứa toàn bộ logic của bot
- `farms_data.json`: File lưu trữ dữ liệu farms, user states, và credentials (được mã hóa)
- `pyproject.toml`: Cấu hình dependencies
- `README.txt`: Hướng dẫn sử dụng và deploy

## Dependencies
- `requests>=2.32.0`: Gọi Telegram API
- `cryptography>=43.0.0`: Mã hóa AES-256 cho passwords/2FA

## Environment Variables
- `TELEGRAM_BOT_TOKEN`: Token từ @BotFather
- `MASTER_SECRET`: Chuỗi bí mật để mã hóa dữ liệu nhạy cảm

## Tính năng chính

### Quản lý Farm
- `/them_farm`: Thêm farm/khách hàng mới
- `/danh_sach`: Xem danh sách tất cả farms
- `/xem_farm`: Xem chi tiết farm
- `/sua_farm`: Sửa thông tin farm
- `/xoa_farm`: Xóa farm
- `/tim_farm`: Tìm kiếm farm theo tên/email

### Báo cáo & Thống kê
- `/thong_ke`: Thống kê tổng quan
- `/bao_cao_ngay`: Báo cáo farms đến hạn hôm nay
- `/bao_cao_tuan`: Báo cáo farms đến hạn trong 7 ngày tới
- `/lich_su`: Xem lịch sử nhắc nhở

### Quản lý Dữ liệu
- `/sao_luu`: Backup file JSON
- `/xuat_csv`: Export dữ liệu ra CSV
- `/bat_tat_nhac`: Bật/tắt nhắc nhở cho từng farm

### Quản lý Login Email
- `/set_mail_login`: Lưu thông tin đầy đủ cho email:
  - Mật khẩu (mã hóa AES-256)
  - 2FA (mã hóa AES-256)
  - Ghi chú (mã hóa AES-256)
  - Ngày tham gia
  - Số ngày sử dụng
  - Facebook khách hàng
- `/get_mail_login`: Xem tất cả thông tin login đã lưu
  - **Mới**: Có nút copy nhanh email, password, 2FA

### Xem chi tiết Farm
- `/xem_farm`: Xem thông tin chi tiết farm
  - **Mới**: Có nút copy nhanh email chủ và các thành viên

## Workflow
- **Telegram Bot**: Chạy `python bot.py` để khởi động bot

## Bảo mật
- Tất cả mật khẩu và 2FA được mã hóa bằng AES-256 (Fernet)
- MASTER_SECRET được sử dụng để tạo khóa mã hóa
- Không lưu trữ thông tin nhạy cảm dưới dạng plain text

## Cách sử dụng
1. Tìm bot trên Telegram bằng username đã tạo
2. Gửi `/start` để bắt đầu
3. Sử dụng menu hoặc các lệnh để quản lý farms
4. Bot sẽ tự động nhắc nhở khi đến hạn thanh toán

## Lưu ý
- Bot chạy 24/7 trên Replit
- Dữ liệu được lưu trong `farms_data.json`
- Backup thường xuyên bằng lệnh `/sao_luu`
