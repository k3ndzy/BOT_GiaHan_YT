
Telegram Reminder Bot - FULL (Copy Buttons)

Tính năng chính:
- Quản lý farm/khách hàng: thêm, sửa, xoá, tìm kiếm, xem chi tiết.
- Nhắc hạn thanh toán: trước 3 ngày, 2 ngày, 1 ngày và đúng ngày.
- Thống kê, báo cáo ngày, báo cáo 7 ngày tới, lịch sử nhắc.
- Sao lưu JSON, export CSV.
- Bật/tắt nhắc cho từng farm.
- Lưu login cho từng email trong farm: password, 2FA, ghi chú, ngày tham gia, số ngày sử dụng, Facebook.
- Mã hoá password/2FA/note bằng AES-256 (Fernet) với MASTER_SECRET.
- Nút inline để copy nhanh:
  + Trong /xem_farm: nút 📋 Copy Email cho chủ & từng member.
  + Trong /get_mail_login: nút 📋 Copy Email / 📋 Copy Password / 📋 Copy 2FA.

1. Biến môi trường cần có
   - TELEGRAM_BOT_TOKEN = token bot Telegram (từ BotFather)
   - MASTER_SECRET = chuỗi bí mật dùng mã hoá mật khẩu/2FA

2. Chạy local
   pip install -e .
   # hoặc
   pip install requests cryptography

   python bot.py

3. Deploy Railway
   - Tạo project mới
   - Upload 3 file:
     + bot.py
     + pyproject.toml
     + farms_data.json
   - Vào Variables, thêm:
     + TELEGRAM_BOT_TOKEN = ...
     + MASTER_SECRET = ...
   - Vào Settings -> Start Command:
     python bot.py

4. Lệnh chính
   /start, /help
   /them_farm, /danh_sach, /xem_farm, /sua_farm, /xoa_farm, /tim_farm
   /thong_ke, /bao_cao_ngay, /bao_cao_tuan, /lich_su
   /sao_luu, /xuat_csv, /bat_tat_nhac
   /set_mail_login, /get_mail_login
   /huy
