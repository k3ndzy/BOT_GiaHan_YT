import requests
import time
import os
import json
import calendar
from datetime import datetime, timedelta

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    print("❌ Lỗi: Không tìm thấy TELEGRAM_BOT_TOKEN trong environment variables!")
    print("Vui lòng thêm token vào Secrets.")
    exit(1)

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
DATA_FILE = "farms_data.json"

def load_data():
    """Đọc dữ liệu từ file JSON"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"farms": [], "user_states": {}}

def save_data(data):
    """Lưu dữ liệu vào file JSON"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_updates(offset=None):
    url = BASE_URL + "/getUpdates"
    params = {
        "timeout": 100,
        "offset": offset
    }
    response = requests.get(url, params=params)
    return response.json()

def send_message(chat_id, text):
    url = BASE_URL + "/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    requests.post(url, data=data)

def send_document(chat_id, file_path, caption=""):
    """Gửi file tài liệu"""
    url = BASE_URL + "/sendDocument"
    with open(file_path, 'rb') as f:
        files = {'document': f}
        data = {'chat_id': chat_id, 'caption': caption}
        requests.post(url, data=data, files=files)

def get_menu_text():
    """Text menu chính"""
    return """🤖 <b>Bot Quản Lý Farm YouTube</b>

📋 <b>Quản lý Farm:</b>
/them_farm - Thêm farm mới
/danh_sach - Xem tất cả farm
/xem_farm - Xem chi tiết farm
/sua_farm - Sửa thông tin farm
/xoa_farm - Xóa farm
/tim_farm - Tìm kiếm farm

📊 <b>Thống kê & Công cụ:</b>
/thong_ke - Thống kê tổng quan
/sao_luu - Sao lưu dữ liệu
/bat_tat_nhac - Bật/tắt nhắc nhở

ℹ️ <b>Khác:</b>
/huy - Hủy thao tác hiện tại
/help - Xem hướng dẫn chi tiết

💡 Bot sẽ tự động nhắc <b>2 ngày</b> và <b>1 ngày</b> trước ngày gia hạn!"""

def handle_start(chat_id):
    """Xử lý lệnh /start"""
    send_message(chat_id, get_menu_text())

def handle_help(chat_id):
    """Xử lý lệnh /help"""
    help_text = """📖 <b>Hướng dẫn sử dụng Bot Farm YouTube</b>

<b>1️⃣ Thêm farm mới</b> - /them_farm
   • Bot sẽ hỏi từng bước
   • Thông tin: tên, email, thành viên, ngày bắt đầu, ngày gia hạn, giá

<b>2️⃣ Xem danh sách</b> - /danh_sach
   • Liệt kê tất cả farm đang quản lý
   
<b>3️⃣ Xem chi tiết farm</b> - /xem_farm
   • Xem đầy đủ thông tin 1 farm cụ thể
   • Bao gồm cả 5 email thành viên

<b>4️⃣ Sửa thông tin</b> - /sua_farm
   • Sửa email chủ, giá, ngày gia hạn
   
<b>5️⃣ Xóa farm</b> - /xoa_farm
   • Xóa farm không còn sử dụng

<b>6️⃣ Tìm kiếm</b> - /tim_farm
   • Tìm farm theo tên hoặc email

<b>7️⃣ Thống kê</b> - /thong_ke
   • Tổng số farm, tổng chi phí
   • Farm sắp hết hạn trong 7 ngày

<b>8️⃣ Sao lưu</b> - /sao_luu
   • Tải file JSON chứa tất cả dữ liệu

<b>9️⃣ Bật/Tắt nhắc nhở</b> - /bat_tat_nhac
   • Tạm tắt nhắc nhở cho farm cụ thể

<b>🔟 Hủy thao tác</b> - /huy
   • Hủy bất cứ lúc nào

⏰ <b>Nhắc nhở tự động:</b>
   • Bot nhắc <b>2 lần</b>: trước 2 ngày và trước 1 ngày
   • Kiểm tra mỗi giờ"""
    send_message(chat_id, help_text)

def start_add_farm(chat_id, data):
    """Bắt đầu quy trình thêm farm"""
    data["user_states"][str(chat_id)] = {
        "action": "add_farm",
        "step": "name",
        "farm_data": {}
    }
    save_data(data)
    send_message(chat_id, "📝 <b>Thêm farm mới</b>\n\nNhập <b>tên farm</b>:")

def handle_add_farm_flow(chat_id, text, data):
    """Xử lý quy trình thêm farm từng bước"""
    state = data["user_states"][str(chat_id)]
    step = state["step"]
    farm_data = state["farm_data"]
    
    if step == "name":
        farm_data["name"] = text
        state["step"] = "owner_email"
        send_message(chat_id, f"✅ Tên farm: <b>{text}</b>\n\nNhập <b>email chủ farm</b>:")
    
    elif step == "owner_email":
        farm_data["owner_email"] = text
        state["step"] = "member1"
        send_message(chat_id, f"✅ Email chủ farm: <b>{text}</b>\n\nNhập <b>email thành viên 1</b>:")
    
    elif step == "member1":
        farm_data["members"] = [text]
        state["step"] = "member2"
        send_message(chat_id, f"✅ Thành viên 1: <b>{text}</b>\n\nNhập <b>email thành viên 2</b>:")
    
    elif step == "member2":
        farm_data["members"].append(text)
        state["step"] = "member3"
        send_message(chat_id, f"✅ Thành viên 2: <b>{text}</b>\n\nNhập <b>email thành viên 3</b>:")
    
    elif step == "member3":
        farm_data["members"].append(text)
        state["step"] = "member4"
        send_message(chat_id, f"✅ Thành viên 3: <b>{text}</b>\n\nNhập <b>email thành viên 4</b>:")
    
    elif step == "member4":
        farm_data["members"].append(text)
        state["step"] = "member5"
        send_message(chat_id, f"✅ Thành viên 4: <b>{text}</b>\n\nNhập <b>email thành viên 5</b>:")
    
    elif step == "member5":
        farm_data["members"].append(text)
        state["step"] = "start_date"
        send_message(chat_id, f"✅ Thành viên 5: <b>{text}</b>\n\nNhập <b>ngày bắt đầu farm</b> (DD/MM/YYYY, VD: 15/11/2025):")
    
    elif step == "start_date":
        try:
            start_date = datetime.strptime(text.strip(), "%d/%m/%Y")
            farm_data["start_date"] = start_date.strftime("%Y-%m-%d")
            state["step"] = "renewal_day"
            send_message(chat_id, f"✅ Ngày bắt đầu: <b>{text}</b>\n\nNhập <b>ngày gia hạn hàng tháng</b> (1-31):")
        except ValueError:
            send_message(chat_id, "❌ Sai định dạng! Nhập theo dạng DD/MM/YYYY (VD: 15/11/2025):")
    
    elif step == "renewal_day":
        try:
            day = int(text)
            if 1 <= day <= 31:
                farm_data["renewal_day"] = day
                state["step"] = "price"
                send_message(chat_id, f"✅ Ngày gia hạn: <b>Ngày {day} hàng tháng</b>\n\nNhập <b>giá tiền</b> (VD: 50000):")
            else:
                send_message(chat_id, "❌ Vui lòng nhập số từ 1-31:")
        except ValueError:
            send_message(chat_id, "❌ Vui lòng nhập số từ 1-31:")
    
    elif step == "price":
        try:
            price = int(text.replace(",", "").replace(".", ""))
            farm_data["price"] = price
            farm_data["chat_id"] = chat_id
            farm_data["reminder_enabled"] = True
            
            data["farms"].append(farm_data)
            del data["user_states"][str(chat_id)]
            save_data(data)
            
            summary = f"""✅ <b>Đã thêm farm thành công!</b>

📦 <b>Tên farm:</b> {farm_data['name']}
👤 <b>Chủ farm:</b> {farm_data['owner_email']}
👥 <b>Thành viên:</b>
   • {farm_data['members'][0]}
   • {farm_data['members'][1]}
   • {farm_data['members'][2]}
   • {farm_data['members'][3]}
   • {farm_data['members'][4]}
📅 <b>Ngày bắt đầu:</b> {datetime.strptime(farm_data['start_date'], '%Y-%m-%d').strftime('%d/%m/%Y')}
📅 <b>Ngày gia hạn:</b> Ngày {farm_data['renewal_day']} hàng tháng
💰 <b>Giá:</b> {farm_data['price']:,} VNĐ

⏰ Bot sẽ nhắc bạn <b>2 ngày</b> và <b>1 ngày</b> trước ngày gia hạn!"""
            send_message(chat_id, summary)
        except ValueError:
            send_message(chat_id, "❌ Vui lòng nhập số tiền hợp lệ (VD: 50000):")
    
    save_data(data)

def handle_list_farms(chat_id, data):
    """Hiển thị danh sách farm"""
    farms = data["farms"]
    
    if not farms:
        send_message(chat_id, "📭 Chưa có farm nào. Dùng /them_farm để thêm mới!")
        return
    
    message = f"📋 <b>Danh sách Farm ({len(farms)} farm)</b>\n\n"
    
    for i, farm in enumerate(farms, 1):
        status = "🔔 Bật" if farm.get("reminder_enabled", True) else "🔕 Tắt"
        message += f"<b>{i}. {farm['name']}</b>\n"
        message += f"   👤 Chủ: {farm['owner_email']}\n"
        message += f"   👥 Thành viên: {len(farm['members'])} người\n"
        message += f"   📅 Gia hạn: Ngày {farm['renewal_day']}\n"
        message += f"   💰 Giá: {farm['price']:,} VNĐ\n"
        message += f"   {status}\n\n"
    
    send_message(chat_id, message)

def start_view_farm(chat_id, data):
    """Bắt đầu xem chi tiết farm"""
    farms = data["farms"]
    
    if not farms:
        send_message(chat_id, "📭 Chưa có farm nào!")
        return
    
    data["user_states"][str(chat_id)] = {
        "action": "view_farm",
        "step": "select"
    }
    save_data(data)
    
    message = "👁 <b>Xem chi tiết farm</b>\n\nNhập <b>tên farm</b>:\n\n"
    for farm in farms:
        message += f"• {farm['name']}\n"
    
    send_message(chat_id, message)

def handle_view_farm_flow(chat_id, text, data):
    """Xử lý xem chi tiết farm"""
    farm_name = text.strip()
    farms = data["farms"]
    
    found_farm = None
    for farm in farms:
        if farm["name"].lower() == farm_name.lower():
            found_farm = farm
            break
    
    if found_farm:
        start_date_str = "Không có"
        if "start_date" in found_farm:
            start_date_str = datetime.strptime(found_farm['start_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
        
        status = "🔔 Đang bật" if found_farm.get("reminder_enabled", True) else "🔕 Đã tắt"
        
        detail = f"""📦 <b>Chi tiết Farm: {found_farm['name']}</b>

👤 <b>Chủ farm:</b> {found_farm['owner_email']}

👥 <b>5 Thành viên:</b>
   1. {found_farm['members'][0]}
   2. {found_farm['members'][1]}
   3. {found_farm['members'][2]}
   4. {found_farm['members'][3]}
   5. {found_farm['members'][4]}

📅 <b>Ngày bắt đầu:</b> {start_date_str}
📅 <b>Ngày gia hạn:</b> Ngày {found_farm['renewal_day']} hàng tháng
💰 <b>Giá:</b> {found_farm['price']:,} VNĐ

⏰ <b>Nhắc nhở:</b> {status}"""
        
        del data["user_states"][str(chat_id)]
        save_data(data)
        send_message(chat_id, detail)
    else:
        send_message(chat_id, f"❌ Không tìm thấy farm <b>{farm_name}</b>. Vui lòng kiểm tra lại tên!")

def start_edit_farm(chat_id, data):
    """Bắt đầu sửa farm"""
    farms = data["farms"]
    
    if not farms:
        send_message(chat_id, "📭 Chưa có farm nào để sửa!")
        return
    
    data["user_states"][str(chat_id)] = {
        "action": "edit_farm",
        "step": "select_farm"
    }
    save_data(data)
    
    message = "✏️ <b>Sửa thông tin farm</b>\n\nNhập <b>tên farm</b> cần sửa:\n\n"
    for farm in farms:
        message += f"• {farm['name']}\n"
    
    send_message(chat_id, message)

def handle_edit_farm_flow(chat_id, text, data):
    """Xử lý sửa farm"""
    state = data["user_states"][str(chat_id)]
    step = state["step"]
    
    if step == "select_farm":
        farm_name = text.strip()
        found_farm = None
        farm_index = -1
        
        for i, farm in enumerate(data["farms"]):
            if farm["name"].lower() == farm_name.lower():
                found_farm = farm
                farm_index = i
                break
        
        if found_farm:
            state["farm_index"] = farm_index
            state["step"] = "select_field"
            message = f"""✏️ <b>Sửa farm: {found_farm['name']}</b>

Chọn thông tin muốn sửa:

1️⃣ - Email chủ farm
2️⃣ - Ngày gia hạn
3️⃣ - Giá tiền

Nhập số <b>1, 2</b> hoặc <b>3</b>:"""
            send_message(chat_id, message)
        else:
            send_message(chat_id, f"❌ Không tìm thấy farm <b>{farm_name}</b>!")
    
    elif step == "select_field":
        if text == "1":
            state["step"] = "edit_email"
            send_message(chat_id, "Nhập <b>email chủ farm mới</b>:")
        elif text == "2":
            state["step"] = "edit_renewal"
            send_message(chat_id, "Nhập <b>ngày gia hạn mới</b> (1-31):")
        elif text == "3":
            state["step"] = "edit_price"
            send_message(chat_id, "Nhập <b>giá tiền mới</b>:")
        else:
            send_message(chat_id, "❌ Vui lòng nhập số 1, 2 hoặc 3!")
    
    elif step == "edit_email":
        farm_index = state["farm_index"]
        data["farms"][farm_index]["owner_email"] = text
        farm_name = data["farms"][farm_index]["name"]
        
        del data["user_states"][str(chat_id)]
        save_data(data)
        send_message(chat_id, f"✅ Đã cập nhật email chủ farm <b>{farm_name}</b> thành: <b>{text}</b>")
    
    elif step == "edit_renewal":
        try:
            day = int(text)
            if 1 <= day <= 31:
                farm_index = state["farm_index"]
                data["farms"][farm_index]["renewal_day"] = day
                farm_name = data["farms"][farm_index]["name"]
                
                del data["user_states"][str(chat_id)]
                save_data(data)
                send_message(chat_id, f"✅ Đã cập nhật ngày gia hạn farm <b>{farm_name}</b> thành: <b>Ngày {day}</b>")
            else:
                send_message(chat_id, "❌ Vui lòng nhập số từ 1-31!")
        except ValueError:
            send_message(chat_id, "❌ Vui lòng nhập số từ 1-31!")
    
    elif step == "edit_price":
        try:
            price = int(text.replace(",", "").replace(".", ""))
            farm_index = state["farm_index"]
            data["farms"][farm_index]["price"] = price
            farm_name = data["farms"][farm_index]["name"]
            
            del data["user_states"][str(chat_id)]
            save_data(data)
            send_message(chat_id, f"✅ Đã cập nhật giá farm <b>{farm_name}</b> thành: <b>{price:,} VNĐ</b>")
        except ValueError:
            send_message(chat_id, "❌ Vui lòng nhập số tiền hợp lệ!")
    
    save_data(data)

def start_delete_farm(chat_id, data):
    """Bắt đầu quy trình xóa farm"""
    farms = data["farms"]
    
    if not farms:
        send_message(chat_id, "📭 Chưa có farm nào để xóa!")
        return
    
    data["user_states"][str(chat_id)] = {
        "action": "delete_farm",
        "step": "select"
    }
    save_data(data)
    
    message = "🗑 <b>Xóa farm</b>\n\nNhập <b>tên farm</b> cần xóa:\n\n"
    for farm in farms:
        message += f"• {farm['name']}\n"
    
    send_message(chat_id, message)

def handle_delete_farm_flow(chat_id, text, data):
    """Xử lý xóa farm"""
    farm_name = text.strip()
    farms = data["farms"]
    
    deleted_farm_name = None
    for i, farm in enumerate(farms):
        if farm["name"].lower() == farm_name.lower():
            deleted_farm_name = farm["name"]
            farms.pop(i)
            break
    
    if deleted_farm_name:
        del data["user_states"][str(chat_id)]
        save_data(data)
        send_message(chat_id, f"✅ Đã xóa farm <b>{deleted_farm_name}</b>!")
    else:
        send_message(chat_id, f"❌ Không tìm thấy farm <b>{farm_name}</b>. Vui lòng kiểm tra lại tên!")

def start_search_farm(chat_id, data):
    """Bắt đầu tìm kiếm farm"""
    if not data["farms"]:
        send_message(chat_id, "📭 Chưa có farm nào để tìm!")
        return
    
    data["user_states"][str(chat_id)] = {
        "action": "search_farm",
        "step": "input"
    }
    save_data(data)
    send_message(chat_id, "🔍 <b>Tìm kiếm farm</b>\n\nNhập <b>tên farm</b> hoặc <b>email</b> cần tìm:")

def handle_search_farm_flow(chat_id, text, data):
    """Xử lý tìm kiếm farm"""
    keyword = text.strip().lower()
    results = []
    
    for farm in data["farms"]:
        if (keyword in farm["name"].lower() or 
            keyword in farm["owner_email"].lower() or 
            any(keyword in member.lower() for member in farm["members"])):
            results.append(farm)
    
    del data["user_states"][str(chat_id)]
    save_data(data)
    
    if results:
        message = f"🔍 <b>Kết quả tìm kiếm</b> ({len(results)} farm)\n\n"
        for i, farm in enumerate(results, 1):
            message += f"<b>{i}. {farm['name']}</b>\n"
            message += f"   👤 Chủ: {farm['owner_email']}\n"
            message += f"   📅 Gia hạn: Ngày {farm['renewal_day']}\n"
            message += f"   💰 Giá: {farm['price']:,} VNĐ\n\n"
        send_message(chat_id, message)
    else:
        send_message(chat_id, f"❌ Không tìm thấy farm nào với từ khóa <b>{text}</b>!")

def handle_statistics(chat_id, data):
    """Xử lý thống kê"""
    farms = data["farms"]
    
    if not farms:
        send_message(chat_id, "📭 Chưa có farm nào để thống kê!")
        return
    
    total_farms = len(farms)
    total_cost = sum(farm["price"] for farm in farms)
    active_reminders = sum(1 for farm in farms if farm.get("reminder_enabled", True))
    
    today = datetime.now()
    upcoming_farms = []
    
    for farm in farms:
        renewal_day = farm["renewal_day"]
        current_year = today.year
        current_month = today.month
        
        try:
            renewal_date = datetime(current_year, current_month, renewal_day)
        except ValueError:
            last_day = calendar.monthrange(current_year, current_month)[1]
            renewal_date = datetime(current_year, current_month, min(renewal_day, last_day))
        
        if renewal_date < today:
            if current_month == 12:
                next_month = 1
                next_year = current_year + 1
            else:
                next_month = current_month + 1
                next_year = current_year
            
            try:
                renewal_date = datetime(next_year, next_month, renewal_day)
            except ValueError:
                last_day = calendar.monthrange(next_year, next_month)[1]
                renewal_date = datetime(next_year, next_month, min(renewal_day, last_day))
        
        days_until = (renewal_date - today).days
        if 0 <= days_until <= 7:
            upcoming_farms.append((farm, days_until))
    
    message = f"""📊 <b>Thống kê Farm YouTube</b>

📦 <b>Tổng số farm:</b> {total_farms}
💰 <b>Tổng chi phí/tháng:</b> {total_cost:,} VNĐ
🔔 <b>Farm đang bật nhắc:</b> {active_reminders}/{total_farms}

⏰ <b>Farm sắp hết hạn (7 ngày tới):</b>"""
    
    if upcoming_farms:
        message += f" {len(upcoming_farms)} farm\n\n"
        for farm, days in sorted(upcoming_farms, key=lambda x: x[1]):
            if days == 0:
                day_text = "HÔM NAY"
            elif days == 1:
                day_text = "NGÀY MAI"
            else:
                day_text = f"còn {days} ngày"
            message += f"   • {farm['name']} - {day_text}\n"
    else:
        message += " Không có\n"
    
    send_message(chat_id, message)

def handle_backup(chat_id, data):
    """Xử lý sao lưu dữ liệu"""
    if not data["farms"]:
        send_message(chat_id, "📭 Chưa có dữ liệu để sao lưu!")
        return
    
    backup_data = {
        "backup_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_farms": len(data["farms"]),
        "farms": data["farms"]
    }
    
    backup_file = f"backup_farms_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)
    
    caption = f"💾 Sao lưu dữ liệu\n📅 Thời gian: {backup_data['backup_date']}\n📦 Tổng: {backup_data['total_farms']} farm"
    send_document(chat_id, backup_file, caption)
    
    os.remove(backup_file)

def start_toggle_reminder(chat_id, data):
    """Bắt đầu bật/tắt nhắc nhở"""
    farms = data["farms"]
    
    if not farms:
        send_message(chat_id, "📭 Chưa có farm nào!")
        return
    
    data["user_states"][str(chat_id)] = {
        "action": "toggle_reminder",
        "step": "select"
    }
    save_data(data)
    
    message = "🔔 <b>Bật/Tắt nhắc nhở</b>\n\nNhập <b>tên farm</b>:\n\n"
    for farm in farms:
        status = "🔔 Đang bật" if farm.get("reminder_enabled", True) else "🔕 Đã tắt"
        message += f"• {farm['name']} - {status}\n"
    
    send_message(chat_id, message)

def handle_toggle_reminder_flow(chat_id, text, data):
    """Xử lý bật/tắt nhắc nhở"""
    farm_name = text.strip()
    
    found = False
    for farm in data["farms"]:
        if farm["name"].lower() == farm_name.lower():
            current_status = farm.get("reminder_enabled", True)
            farm["reminder_enabled"] = not current_status
            new_status = "🔔 Đã bật" if farm["reminder_enabled"] else "🔕 Đã tắt"
            
            del data["user_states"][str(chat_id)]
            save_data(data)
            send_message(chat_id, f"✅ {new_status} nhắc nhở cho farm <b>{farm['name']}</b>!")
            found = True
            break
    
    if not found:
        send_message(chat_id, f"❌ Không tìm thấy farm <b>{farm_name}</b>!")

def cancel_action(chat_id, data):
    """Hủy thao tác hiện tại"""
    if str(chat_id) in data["user_states"]:
        del data["user_states"][str(chat_id)]
        save_data(data)
        send_message(chat_id, "✅ Đã hủy thao tác!")
    else:
        send_message(chat_id, "ℹ️ Không có thao tác nào đang thực hiện.")

def check_and_send_reminders(data):
    """Kiểm tra và gửi nhắc nhở"""
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    
    data_changed = False
    
    for farm in data["farms"]:
        if not farm.get("reminder_enabled", True):
            continue
        
        renewal_day = farm["renewal_day"]
        
        if renewal_day > 31 or renewal_day < 1:
            continue
        
        current_year = today.year
        current_month = today.month
        
        try:
            renewal_date = datetime(current_year, current_month, renewal_day)
        except ValueError:
            last_day = calendar.monthrange(current_year, current_month)[1]
            renewal_date = datetime(current_year, current_month, min(renewal_day, last_day))
        
        if renewal_date < today:
            if current_month == 12:
                next_month = 1
                next_year = current_year + 1
            else:
                next_month = current_month + 1
                next_year = current_year
            
            try:
                renewal_date = datetime(next_year, next_month, renewal_day)
            except ValueError:
                last_day = calendar.monthrange(next_year, next_month)[1]
                renewal_date = datetime(next_year, next_month, min(renewal_day, last_day))
        
        reminder_2days = renewal_date - timedelta(days=2)
        reminder_1day = renewal_date - timedelta(days=1)
        
        last_reminded_2days = farm.get("last_reminded_2days")
        last_reminded_1day = farm.get("last_reminded_1day")
        
        chat_id = farm["chat_id"]
        
        if today.date() == reminder_2days.date():
            if last_reminded_2days != today_str:
                message = f"""⏰ <b>NHẮC NHỞ GIA HẠN</b>

📦 <b>Farm:</b> {farm['name']}
📅 <b>Ngày gia hạn:</b> Ngày {renewal_day}
💰 <b>Giá:</b> {farm['price']:,} VNĐ

👤 <b>Chủ farm:</b> {farm['owner_email']}

⚠️ Còn <b>2 ngày</b> nữa đến hạn thanh toán!"""
                
                send_message(chat_id, message)
                farm["last_reminded_2days"] = today_str
                data_changed = True
        
        if today.date() == reminder_1day.date():
            if last_reminded_1day != today_str:
                message = f"""🔔 <b>NHẮC NHỞ GIA HẠN LẦN 2</b>

📦 <b>Farm:</b> {farm['name']}
📅 <b>Ngày gia hạn:</b> Ngày {renewal_day}
💰 <b>Giá:</b> {farm['price']:,} VNĐ

👤 <b>Chủ farm:</b> {farm['owner_email']}

🚨 Còn <b>1 ngày</b> nữa đến hạn thanh toán!"""
                
                send_message(chat_id, message)
                farm["last_reminded_1day"] = today_str
                data_changed = True
    
    if data_changed:
        save_data(data)

def main():
    print("🤖 Bot đang chạy...")
    offset = None
    last_reminder_check = datetime.now()
    
    data = load_data()
    
    while True:
        current_time = datetime.now()
        if (current_time - last_reminder_check).seconds >= 3600:
            check_and_send_reminders(data)
            last_reminder_check = current_time
        
        updates = get_updates(offset)
        
        if updates.get("ok"):
            for update in updates["result"]:
                offset = update["update_id"] + 1
                
                message = update.get("message") or update.get("edited_message")
                if not message:
                    continue
                
                chat_id = message["chat"]["id"]
                text = message.get("text", "")
                
                data = load_data()
                
                if text == "/start":
                    handle_start(chat_id)
                
                elif text == "/help":
                    handle_help(chat_id)
                
                elif text == "/them_farm":
                    start_add_farm(chat_id, data)
                
                elif text == "/danh_sach":
                    handle_list_farms(chat_id, data)
                
                elif text == "/xem_farm":
                    start_view_farm(chat_id, data)
                
                elif text == "/sua_farm":
                    start_edit_farm(chat_id, data)
                
                elif text == "/xoa_farm":
                    start_delete_farm(chat_id, data)
                
                elif text == "/tim_farm":
                    start_search_farm(chat_id, data)
                
                elif text == "/thong_ke":
                    handle_statistics(chat_id, data)
                
                elif text == "/sao_luu":
                    handle_backup(chat_id, data)
                
                elif text == "/bat_tat_nhac":
                    start_toggle_reminder(chat_id, data)
                
                elif text == "/huy":
                    cancel_action(chat_id, data)
                
                elif str(chat_id) in data["user_states"]:
                    state = data["user_states"][str(chat_id)]
                    action = state["action"]
                    
                    if action == "add_farm":
                        handle_add_farm_flow(chat_id, text, data)
                    elif action == "view_farm":
                        handle_view_farm_flow(chat_id, text, data)
                    elif action == "edit_farm":
                        handle_edit_farm_flow(chat_id, text, data)
                    elif action == "delete_farm":
                        handle_delete_farm_flow(chat_id, text, data)
                    elif action == "search_farm":
                        handle_search_farm_flow(chat_id, text, data)
                    elif action == "toggle_reminder":
                        handle_toggle_reminder_flow(chat_id, text, data)
                
                else:
                    send_message(chat_id, f"ℹ️ Lệnh không hợp lệ. Gửi /help để xem hướng dẫn!")
        
        time.sleep(1)

if __name__ == "__main__":
    main()
