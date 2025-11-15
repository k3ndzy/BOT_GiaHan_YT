# Telegram Bot Quản Lý Farm YouTube

## Tổng quan
Bot Telegram toàn diện để quản lý farm YouTube Family với đầy đủ tính năng: thêm/sửa/xóa farm, tìm kiếm, thống kê, sao lưu và nhắc nhở tự động 2 lần.

## Ngày tạo
15 tháng 11, 2025

## Cấu trúc dự án
- `bot.py`: File chính chứa toàn bộ logic bot
- `farms_data.json`: File lưu trữ dữ liệu farm (tự động tạo khi chạy)
- `pyproject.toml`: Cấu hình dependencies

## Tính năng đầy đủ

### 📋 Quản lý Farm
1. **Thêm farm mới** (`/them_farm`): Bot hỏi từng bước
   - Tên farm
   - Email chủ farm
   - 5 email thành viên (hỏi lần lượt)
   - Ngày bắt đầu farm (DD/MM/YYYY)
   - Ngày gia hạn hàng tháng (1-31)
   - Giá tiền

2. **Xem danh sách** (`/danh_sach`): Liệt kê tất cả farm với trạng thái nhắc nhở

3. **Xem chi tiết farm** (`/xem_farm`): Hiển thị đầy đủ thông tin 1 farm
   - Tất cả 5 email thành viên
   - Ngày bắt đầu, ngày gia hạn
   - Trạng thái nhắc nhở

4. **Sửa thông tin** (`/sua_farm`): Sửa đổi farm đã tồn tại
   - Email chủ farm
   - Ngày gia hạn
   - Giá tiền

5. **Xóa farm** (`/xoa_farm`): Xóa farm không còn sử dụng

6. **Tìm kiếm farm** (`/tim_farm`): Tìm farm theo tên hoặc email

### 📊 Thống kê & Công cụ

7. **Thống kê tổng quan** (`/thong_ke`):
   - Tổng số farm đang quản lý
   - Tổng chi phí hàng tháng
   - Số farm đang bật nhắc nhở
   - Farm sắp hết hạn trong 7 ngày tới

8. **Sao lưu dữ liệu** (`/sao_luu`):
   - Gửi file JSON chứa tất cả farm
   - Bao gồm thời gian backup
   - Để backup an toàn

9. **Bật/Tắt nhắc nhở** (`/bat_tat_nhac`):
   - Tắt tạm thời nhắc nhở cho farm cụ thể
   - Không cần xóa farm

### ⏰ Nhắc nhở tự động (nâng cấp)
- Bot kiểm tra **mỗi giờ**
- Nhắc **2 lần**:
  - Lần 1: **2 ngày trước** ngày gia hạn
  - Lần 2: **1 ngày trước** ngày gia hạn
- Chỉ nhắc farm có bật nhắc nhở
- Thông báo gồm: tên farm, ngày gia hạn, giá tiền, email chủ farm

### 🛠 Lệnh khác
- `/start` - Menu chính với tất cả lệnh
- `/help` - Hướng dẫn sử dụng chi tiết
- `/huy` - Hủy thao tác hiện tại

## Cấu trúc dữ liệu (JSON)

Mỗi farm có các trường:
- `name`: Tên farm
- `owner_email`: Email chủ farm
- `members`: Danh sách 5 email thành viên (array)
- `start_date`: Ngày bắt đầu farm (YYYY-MM-DD)
- `renewal_day`: Ngày gia hạn hàng tháng (1-31)
- `price`: Giá tiền (VNĐ)
- `chat_id`: ID chat Telegram để gửi nhắc nhở
- `reminder_enabled`: Bật/tắt nhắc nhở (boolean, mặc định true)
- `last_reminded_2days`: Ngày gửi nhắc lần 1 (YYYY-MM-DD)
- `last_reminded_1day`: Ngày gửi nhắc lần 2 (YYYY-MM-DD)

## Cách sử dụng
1. Tạo bot mới trên Telegram qua @BotFather
2. Lấy token của bot
3. Thêm token vào Secrets với tên `TELEGRAM_BOT_TOKEN`
4. Chạy bot
5. Gửi `/start` trên Telegram để bắt đầu
6. Sử dụng `/them_farm` để thêm farm đầu tiên
7. Bot sẽ tự động nhắc đúng giờ!

## Thư viện sử dụng
- `requests`: Gọi Telegram Bot API
- `json`: Lưu trữ dữ liệu
- `datetime`: Tính toán ngày tháng
- `calendar`: Xử lý tháng có số ngày khác nhau

## Ghi chú kỹ thuật
- **State management**: Dùng JSON để theo dõi trạng thái hội thoại từng user
- **Data persistence**: Lưu vào file `farms_data.json`
- **Reminder system**: 
  - Kiểm tra mỗi giờ (3600 giây)
  - Tính toán chính xác với `datetime` và `calendar`
  - Xử lý đúng tháng 28/29/30/31 ngày
  - Nhắc 2 lần: trước 2 ngày và trước 1 ngày
  - Lưu riêng ngày nhắc cho từng farm
- **Backup**: Gửi file JSON qua Telegram API
- **Search**: Tìm kiếm trong tên farm và tất cả email

## Ví dụ sử dụng

### Thêm farm mới:
```
User: /them_farm
Bot: Nhập tên farm:
User: Farm 1
Bot: Nhập email chủ farm:
User: chu@gmail.com
Bot: Nhập email thành viên 1:
...
Bot: Nhập ngày bắt đầu farm (DD/MM/YYYY):
User: 15/11/2025
Bot: Nhập ngày gia hạn (1-31):
User: 15
Bot: Nhập giá tiền:
User: 50000
Bot: ✅ Đã thêm farm thành công!
```

### Sửa farm:
```
User: /sua_farm
Bot: Nhập tên farm cần sửa:
User: Farm 1
Bot: Chọn: 1-Email, 2-Ngày gia hạn, 3-Giá
User: 3
Bot: Nhập giá tiền mới:
User: 60000
Bot: ✅ Đã cập nhật giá!
```

### Xem thống kê:
```
User: /thong_ke
Bot: 
📊 Thống kê Farm YouTube
📦 Tổng số farm: 5
💰 Tổng chi phí/tháng: 250,000 VNĐ
🔔 Farm đang bật nhắc: 5/5
⏰ Farm sắp hết hạn (7 ngày tới): 2 farm
   • Farm 1 - còn 2 ngày
   • Farm 2 - HÔM NAY
```

## Lịch sử cập nhật
- **15/11/2025**: Phiên bản 1.0 - Bot cơ bản với thêm/xóa/xem farm, nhắc 1 lần
- **15/11/2025**: Phiên bản 2.0 - Thêm đầy đủ tính năng:
  - Sửa farm, xem chi tiết, tìm kiếm
  - Thống kê, sao lưu, bật/tắt nhắc
  - Nhắc 2 lần (2 ngày + 1 ngày trước)
  - Lưu ngày bắt đầu farm
