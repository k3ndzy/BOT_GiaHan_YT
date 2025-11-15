import os
import time
import json
import csv
import calendar
import base64
import hashlib
from datetime import datetime, timedelta

import requests
from cryptography.fernet import Fernet

# ================== CONFIG ==================

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    print("❌ Lỗi: Thiếu TELEGRAM_BOT_TOKEN trong environment variables")
    raise SystemExit(1)

MASTER_SECRET = os.environ.get("MASTER_SECRET")
if not MASTER_SECRET:
    print("❌ Lỗi: Thiếu MASTER_SECRET trong environment variables")
    raise SystemExit(1)

BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
DATA_FILE = "farms_data.json"


# ================== ENCRYPTION (AES-256 / FERNET) ==================


def _build_fernet():
    key = hashlib.sha256(MASTER_SECRET.encode("utf-8")).digest()
    fkey = base64.urlsafe_b64encode(key)
    return Fernet(fkey)


FERNET = _build_fernet()


def encrypt_text(plain: str) -> str:
    if plain is None:
        plain = ""
    token = FERNET.encrypt(plain.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_text(token: str) -> str:
    if not token:
        return ""
    plain = FERNET.decrypt(token.encode("utf-8"))
    return plain.decode("utf-8")


# ================== DATA LOAD / SAVE ==================


def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = {"farms": [], "user_states": {}, "credentials": {}}
    else:
        data = {"farms": [], "user_states": {}, "credentials": {}}

    data.setdefault("farms", [])
    data.setdefault("user_states", {})
    data.setdefault("credentials", {})

    # bảo đảm mỗi farm có email_logins & reminder_history
    for farm in data["farms"]:
        farm.setdefault("reminder_history", [])
        farm.setdefault("email_logins", {})

    return data


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ================== TELEGRAM API ==================


def get_updates(offset=None):
    url = BASE_URL + "/getUpdates"
    params = {"timeout": 100, "offset": offset}
    resp = requests.get(url, params=params, timeout=120)
    return resp.json()


def send_message(chat_id, text, reply_markup=None):
    url = BASE_URL + "/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
    }
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup, ensure_ascii=False)
    try:
        requests.post(url, data=data, timeout=20)
    except Exception as e:
        print("Lỗi send_message:", e)


def send_document(chat_id, file_path, caption=""):
    url = BASE_URL + "/sendDocument"
    with open(file_path, "rb") as f:
        files = {"document": f}
        data = {"chat_id": chat_id, "caption": caption}
        try:
            requests.post(url, data=data, files=files, timeout=60)
        except Exception as e:
            print("Lỗi send_document:", e)


def answer_callback_query(callback_query_id, text=""):
    url = BASE_URL + "/answerCallbackQuery"
    data = {"callback_query_id": callback_query_id}
    if text:
        data["text"] = text
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print("Lỗi answerCallbackQuery:", e)


# ================== MENU & HELP ==================


def get_menu_text():
    return """🤖 <b>Bot Nhắc Hạn Thanh Toán</b>

📋 <b>Quản lý:</b>
/them_farm - Thêm farm/khách hàng
/danh_sach - Danh sách
/xem_farm - Xem chi tiết
/sua_farm - Sửa
/xoa_farm - Xóa
/tim_farm - Tìm kiếm

📊 <b>Báo cáo:</b>
/thong_ke - Thống kê
/bao_cao_ngay - Hôm nay
/bao_cao_tuan - 7 ngày tới
/lich_su - Lịch sử nhắc

💾 <b>Dữ liệu:</b>
/sao_luu - Backup JSON
/xuat_csv - Export CSV
/bat_tat_nhac - Bật/Tắt nhắc

🔐 <b>Login email (theo farm):</b>
/set_mail_login - Lưu password / 2FA + ngày tham gia + thời gian dùng + Facebook
/get_mail_login - Xem & copy thông tin login email

ℹ️ <b>Khác:</b>
/huy - Hủy thao tác hiện tại
/help - Hướng dẫn chi tiết
"""


def handle_start(chat_id):
    keyboard = {
        "keyboard": [
            [{"text": "➕ Thêm"}, {"text": "📋 Danh sách"}],
            [{"text": "📊 Thống kê"}, {"text": "📆 Báo cáo tuần"}],
            [{"text": "📅 Báo cáo hôm nay"}, {"text": "💾 Sao lưu"}],
            [{"text": "📤 Xuất CSV"}, {"text": "🔔 Bật/Tắt nhắc"}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
    }
    send_message(chat_id, get_menu_text(), reply_markup=keyboard)


def handle_help(chat_id):
    help_text = """📖 <b>Hướng dẫn</b>

• /them_farm: Thêm farm/khách hàng, bot hỏi từng bước.
• /danh_sach, /xem_farm, /sua_farm, /xoa_farm, /tim_farm: Quản lý farm.
• /thong_ke, /bao_cao_ngay, /bao_cao_tuan, /lich_su: Thống kê & lịch sử.
• /sao_luu, /xuat_csv: Sao lưu & export dữ liệu.
• /bat_tat_nhac: Bật/tắt nhắc hạn từng farm.
• /set_mail_login: Lưu mật khẩu / 2FA + ngày tham gia + thời gian sử dụng + Facebook cho email trong farm.
• /get_mail_login: Xem lại & copy email / password / 2FA của email trong farm.
• /huy: Huỷ thao tác đang làm.
"""
    send_message(chat_id, help_text)


# ================== DATE UTIL ==================


def get_next_renewal_date(renewal_day, from_date=None):
    if from_date is None:
        from_date = datetime.now()
    today = from_date
    year = today.year
    month = today.month
    try:
        renewal_date = datetime(year, month, renewal_day)
    except ValueError:
        last_day = calendar.monthrange(year, month)[1]
        renewal_date = datetime(year, month, min(renewal_day, last_day))
    if renewal_date.date() < today.date():
        if month == 12:
            month = 1
            year += 1
        else:
            month += 1
        try:
            renewal_date = datetime(year, month, renewal_day)
        except ValueError:
            last_day = calendar.monthrange(year, month)[1]
            renewal_date = datetime(year, month, min(renewal_day, last_day))
    return renewal_date


# ================== ADD FARM ==================


def start_add_farm(chat_id, data):
    data["user_states"][str(chat_id)] = {
        "action": "add_farm",
        "step": "name",
        "farm": {},
    }
    save_data(data)
    send_message(chat_id, "📝 <b>Thêm farm/khách hàng mới</b>\n\nNhập <b>tên</b>:")


def handle_add_farm_flow(chat_id, text, data):
    state = data["user_states"][str(chat_id)]
    step = state["step"]
    farm = state["farm"]

    if step == "name":
        farm["name"] = text.strip()
        state["step"] = "owner"
        save_data(data)
        send_message(chat_id, f"✅ Tên: <b>{farm['name']}</b>\n\nNhập <b>email chủ</b>:")

    elif step == "owner":
        farm["owner_email"] = text.strip()
        farm["members"] = []
        state["step"] = "member"
        state["idx"] = 1
        save_data(data)
        send_message(
            chat_id,
            "Nhập <b>email thành viên 1</b> (hoặc gõ <code>skip</code> nếu không có):",
        )

    elif step == "member":
        if text.strip().lower() != "skip":
            farm["members"].append(text.strip())
        if state["idx"] < 5:
            state["idx"] += 1
            save_data(data)
            send_message(
                chat_id,
                f"Nhập <b>email thành viên {state['idx']}</b> (hoặc <code>skip</code>):",
            )
        else:
            state["step"] = "start"
            save_data(data)
            send_message(chat_id, "Nhập <b>ngày bắt đầu</b> (DD/MM/YYYY):")

    elif step == "start":
        try:
            d = datetime.strptime(text.strip(), "%d/%m/%Y")
            farm["start_date"] = d.strftime("%Y-%m-%d")
            state["step"] = "renewal"
            save_data(data)
            send_message(
                chat_id,
                f"✅ Ngày bắt đầu: <b>{text.strip()}</b>\n\nNhập <b>ngày gia hạn hàng tháng</b> (1-31):",
            )
        except ValueError:
            send_message(chat_id, "❌ Sai định dạng, hãy nhập dạng DD/MM/YYYY.")

    elif step == "renewal":
        try:
            day = int(text.strip())
            if 1 <= day <= 31:
                farm["renewal_day"] = day
                state["step"] = "price"
                save_data(data)
                send_message(
                    chat_id,
                    f"✅ Ngày gia hạn: <b>Ngày {day}</b>\n\nNhập <b>giá tiền</b> (VD: 50000):",
                )
            else:
                send_message(chat_id, "❌ Vui lòng nhập số 1-31.")
        except ValueError:
            send_message(chat_id, "❌ Vui lòng nhập số 1-31.")

    elif step == "price":
        try:
            price = int(text.replace(",", "").replace(".", "").strip())
            farm["price"] = price
            farm["chat_id"] = chat_id
            farm["reminder_enabled"] = True
            farm.setdefault("reminder_history", [])
            farm.setdefault("email_logins", {})

            data["farms"].append(farm)
            if str(chat_id) in data["user_states"]:
                del data["user_states"][str(chat_id)]
            save_data(data)

            members = farm.get("members", [])
            mem_str = ""
            if members:
                for i, m in enumerate(members, 1):
                    mem_str += f"   {i}. {m}\n"
            else:
                mem_str = "   (Không có)\n"

            start_str = datetime.strptime(farm["start_date"], "%Y-%m-%d").strftime(
                "%d/%m/%Y"
            )

            summary = f"""✅ <b>Đã thêm thành công!</b>

📦 <b>Tên:</b> {farm['name']}
👤 <b>Chủ:</b> {farm['owner_email']}
👥 <b>Thành viên:</b>
{mem_str}📅 <b>Bắt đầu:</b> {start_str}
📅 <b>Gia hạn:</b> Ngày {farm['renewal_day']} hàng tháng
💰 <b>Giá:</b> {farm['price']:,} VNĐ
"""
            send_message(chat_id, summary)
        except ValueError:
            send_message(chat_id, "❌ Vui lòng nhập số tiền hợp lệ.")

    save_data(data)


# ================== LIST / VIEW FARM ==================


def handle_list_farms(chat_id, data):
    farms = data.get("farms", [])
    if not farms:
        send_message(chat_id, "📭 Chưa có dữ liệu. Dùng /them_farm để thêm mới.")
        return
    msg = f"📋 <b>Danh sách ({len(farms)})</b>\n\n"
    for i, f in enumerate(farms, 1):
        st = "🔔" if f.get("reminder_enabled", True) else "🔕"
        msg += (
            f"<b>{i}. {f['name']}</b> {st}\n"
            f"   👤 {f['owner_email']}\n"
            f"   📅 Ngày {f['renewal_day']}\n"
            f"   💰 {f['price']:,} VNĐ\n\n"
        )
    send_message(chat_id, msg)


def start_view_farm(chat_id, data):
    farms = data.get("farms", [])
    if not farms:
        send_message(chat_id, "📭 Chưa có dữ liệu!")
        return
    data["user_states"][str(chat_id)] = {
        "action": "view_farm",
        "step": "select",
    }
    save_data(data)
    msg = "👁 <b>Xem chi tiết</b>\n\nNhập <b>tên</b>:\n\n"
    for f in farms:
        msg += f"• {f['name']}\n"
    send_message(chat_id, msg)


def handle_view_farm_flow(chat_id, text, data):
    name = text.strip().lower()
    farms = data.get("farms", [])
    target = None
    for f in farms:
        if f["name"].lower() == name:
            target = f
            break
    if not target:
        send_message(chat_id, f"❌ Không tìm thấy <b>{text}</b>.")
        return

    start_str = target.get("start_date", "")
    if start_str:
        try:
            start_str = datetime.strptime(start_str, "%Y-%m-%d").strftime("%d/%m/%Y")
        except Exception:
            pass
    else:
        start_str = "Không có"

    members = target.get("members", [])
    if members:
        mem_str = ""
        for i, m in enumerate(members, 1):
            mem_str += f"   {i}. {m}\n"
    else:
        mem_str = "   (Không có)\n"

    st = "🔔 Đang bật" if target.get("reminder_enabled", True) else "🔕 Đang tắt"

    detail = f"""📦 <b>Chi tiết: {target['name']}</b>

👤 <b>Chủ:</b> {target['owner_email']}
👥 <b>Thành viên:</b>
{mem_str}📅 <b>Bắt đầu:</b> {start_str}
📅 <b>Gia hạn:</b> Ngày {target['renewal_day']} hàng tháng
💰 <b>Giá:</b> {target['price']:,} VNĐ
🔔 <b>Nhắc:</b> {st}

🔐 Mật khẩu / 2FA KHÔNG hiển thị ở đây.
Dùng lệnh /get_mail_login để xem login từng email.
"""

    # Inline keyboard copy email cho chủ + từng member
    inline_keyboard = []
    owner_email = target.get("owner_email")
    if owner_email:
        inline_keyboard.append(
            [
                {
                    "text": "📋 Copy Email (chủ)",
                    "callback_data": f"ce|{owner_email}",
                }
            ]
        )
    for em in members:
        inline_keyboard.append(
            [
                {
                    "text": f"📋 Copy {em}",
                    "callback_data": f"ce|{em}",
                }
            ]
        )

    reply_markup = {"inline_keyboard": inline_keyboard} if inline_keyboard else None

    if str(chat_id) in data["user_states"]:
        del data["user_states"][str(chat_id)]
        save_data(data)
    send_message(chat_id, detail, reply_markup=reply_markup)


# ================== EDIT / DELETE ==================


def start_edit_farm(chat_id, data):
    farms = data.get("farms", [])
    if not farms:
        send_message(chat_id, "📭 Chưa có dữ liệu để sửa!")
        return
    data["user_states"][str(chat_id)] = {
        "action": "edit_farm",
        "step": "select",
    }
    save_data(data)
    msg = "✏️ <b>Sửa farm</b>\n\nNhập <b>tên</b>:\n\n"
    for f in farms:
        msg += f"• {f['name']}\n"
    send_message(chat_id, msg)


def handle_edit_farm_flow(chat_id, text, data):
    state = data["user_states"][str(chat_id)]
    step = state["step"]

    if step == "select":
        farms = data.get("farms", [])
        name = text.strip().lower()
        idx = -1
        for i, f in enumerate(farms):
            if f["name"].lower() == name:
                idx = i
                break
        if idx == -1:
            send_message(chat_id, f"❌ Không tìm thấy <b>{text}</b>.")
            return
        state["farm_index"] = idx
        state["step"] = "field"
        save_data(data)
        send_message(
            chat_id,
            "Chọn mục sửa:\n1 - Email chủ\n2 - Ngày gia hạn\n3 - Giá tiền\nNhập 1 / 2 / 3:",
        )

    elif step == "field":
        if text.strip() == "1":
            state["step"] = "edit_owner"
            save_data(data)
            send_message(chat_id, "Nhập email chủ mới:")
        elif text.strip() == "2":
            state["step"] = "edit_renewal"
            save_data(data)
            send_message(chat_id, "Nhập ngày gia hạn mới (1-31):")
        elif text.strip() == "3":
            state["step"] = "edit_price"
            save_data(data)
            send_message(chat_id, "Nhập giá tiền mới:")
        else:
            send_message(chat_id, "❌ Vui lòng nhập 1 / 2 / 3.")

    elif step == "edit_owner":
        idx = state["farm_index"]
        data["farms"][idx]["owner_email"] = text.strip()
        name = data["farms"][idx]["name"]
        del data["user_states"][str(chat_id)]
        save_data(data)
        send_message(chat_id, f"✅ Đã cập nhật email chủ của <b>{name}</b>.")

    elif step == "edit_renewal":
        try:
            day = int(text.strip())
            if 1 <= day <= 31:
                idx = state["farm_index"]
                data["farms"][idx]["renewal_day"] = day
                name = data["farms"][idx]["name"]
                del data["user_states"][str(chat_id)]
                save_data(data)
                send_message(chat_id, f"✅ Đã cập nhật ngày gia hạn của <b>{name}</b>.")
            else:
                send_message(chat_id, "❌ Vui lòng nhập số 1-31.")
        except ValueError:
            send_message(chat_id, "❌ Vui lòng nhập số 1-31.")

    elif step == "edit_price":
        try:
            price = int(text.replace(",", "").replace(".", "").strip())
            idx = state["farm_index"]
            data["farms"][idx]["price"] = price
            name = data["farms"][idx]["name"]
            del data["user_states"][str(chat_id)]
            save_data(data)
            send_message(chat_id, f"✅ Đã cập nhật giá của <b>{name}</b>.")
        except ValueError:
            send_message(chat_id, "❌ Vui lòng nhập số tiền hợp lệ.")


def start_delete_farm(chat_id, data):
    farms = data.get("farms", [])
    if not farms:
        send_message(chat_id, "📭 Chưa có dữ liệu để xoá!")
        return
    data["user_states"][str(chat_id)] = {
        "action": "delete_farm",
        "step": "select",
    }
    save_data(data)
    msg = "🗑 <b>Xoá farm</b>\n\nNhập <b>tên</b>:\n\n"
    for f in farms:
        msg += f"• {f['name']}\n"
    send_message(chat_id, msg)


def handle_delete_farm_flow(chat_id, text, data):
    farms = data.get("farms", [])
    name = text.strip().lower()
    idx = -1
    for i, f in enumerate(farms):
        if f["name"].lower() == name:
            idx = i
            break
    if idx == -1:
        send_message(chat_id, f"❌ Không tìm thấy <b>{text}</b>.")
        return
    deleted = farms[idx]["name"]
    farms.pop(idx)
    if str(chat_id) in data["user_states"]:
        del data["user_states"][str(chat_id)]
    save_data(data)
    send_message(chat_id, f"✅ Đã xoá <b>{deleted}</b>.")


# ================== SEARCH ==================


def start_search_farm(chat_id, data):
    if not data.get("farms"):
        send_message(chat_id, "📭 Chưa có dữ liệu để tìm!")
        return
    data["user_states"][str(chat_id)] = {
        "action": "search_farm",
        "step": "input",
    }
    save_data(data)
    send_message(chat_id, "🔍 Nhập <b>tên</b> hoặc <b>email</b> cần tìm:")


def handle_search_farm_flow(chat_id, text, data):
    kw = text.strip().lower()
    res = []
    for f in data.get("farms", []):
        if kw in f["name"].lower() or kw in f["owner_email"].lower():
            res.append(f)
            continue
        for m in f.get("members", []):
            if kw in m.lower():
                res.append(f)
                break
    if str(chat_id) in data["user_states"]:
        del data["user_states"][str(chat_id)]
        save_data(data)
    if not res:
        send_message(chat_id, f"❌ Không tìm thấy với từ khoá <b>{text}</b>.")
        return
    msg = f"🔍 <b>Kết quả ({len(res)})</b>\n\n"
    for i, f in enumerate(res, 1):
        msg += (
            f"<b>{i}. {f['name']}</b>\n"
            f"   👤 {f['owner_email']}\n"
            f"   📅 Ngày {f['renewal_day']}\n"
            f"   💰 {f['price']:,} VNĐ\n\n"
        )
    send_message(chat_id, msg)


# ================== STATS & REPORT ==================


def handle_statistics(chat_id, data):
    farms = data.get("farms", [])
    if not farms:
        send_message(chat_id, "📭 Chưa có dữ liệu để thống kê!")
        return
    total = len(farms)
    total_cost = sum(f.get("price", 0) for f in farms)
    active = sum(1 for f in farms if f.get("reminder_enabled", True))
    today = datetime.now()
    upcoming = []
    for f in farms:
        rd = get_next_renewal_date(f.get("renewal_day", 1), from_date=today)
        diff = (rd.date() - today.date()).days
        if 0 <= diff <= 7:
            upcoming.append((f, diff))

    msg = f"""📊 <b>Thống kê</b>

📦 Tổng farm: <b>{total}</b>
💰 Tổng tiền/tháng: <b>{total_cost:,} VNĐ</b>
🔔 Đang bật nhắc: <b>{active}/{total}</b>

⏰ Đến hạn trong 7 ngày tới:"""

    if not upcoming:
        msg += " Không có."
    else:
        msg += "\n\n"
        for f, d in sorted(upcoming, key=lambda x: x[1]):
            if d == 0:
                day_text = "Hôm nay"
            elif d == 1:
                day_text = "Ngày mai"
            else:
                day_text = f"Còn {d} ngày"
            msg += f"• {f['name']} - {day_text} - {f['price']:,} VNĐ\n"
    send_message(chat_id, msg)


def handle_daily_report(chat_id, data):
    farms = data.get("farms", [])
    if not farms:
        send_message(chat_id, "📭 Chưa có dữ liệu!")
        return
    today = datetime.now()
    today_str = today.strftime("%d/%m/%Y")
    res = []
    for f in farms:
        rd = get_next_renewal_date(
            f.get("renewal_day", 1),
            from_date=today.replace(hour=0, minute=0, second=0, microsecond=0),
        )
        if rd.date() == today.date():
            res.append(f)
    if not res:
        send_message(chat_id, f"📅 Hôm nay ({today_str}) không có farm nào đến hạn.")
        return
    msg = f"📅 <b>Báo cáo hôm nay ({today_str})</b>\n\n"
    for f in res:
        msg += f"• {f['name']} - {f['price']:,} VNĐ - {f['owner_email']}\n"
    send_message(chat_id, msg)


def handle_weekly_report(chat_id, data):
    farms = data.get("farms", [])
    if not farms:
        send_message(chat_id, "📭 Chưa có dữ liệu!")
        return
    today = datetime.now()
    res = []
    for f in farms:
        rd = get_next_renewal_date(f.get("renewal_day", 1), from_date=today)
        diff = (rd.date() - today.date()).days
        if 0 <= diff <= 7:
            res.append((f, rd, diff))
    if not res:
        send_message(chat_id, "📆 7 ngày tới không có farm nào đến hạn.")
        return
    msg = "📆 <b>Báo cáo 7 ngày tới</b>\n\n"
    for f, rd, d in sorted(res, key=lambda x: x[2]):
        if d == 0:
            day_text = "Hôm nay"
        elif d == 1:
            day_text = "Ngày mai"
        else:
            day_text = f"Còn {d} ngày"
        msg += f"• {f['name']} - {f['price']:,} VNĐ - {day_text} (ngày {rd.day})\n"
    send_message(chat_id, msg)


def start_history(chat_id, data):
    if not data.get("farms"):
        send_message(chat_id, "📭 Chưa có farm nào!")
        return
    data["user_states"][str(chat_id)] = {
        "action": "history",
        "step": "farm",
    }
    save_data(data)
    msg = "🕒 <b>Lịch sử nhắc</b>\n\nNhập tên farm:\n\n"
    for f in data["farms"]:
        msg += f"• {f['name']}\n"
    send_message(chat_id, msg)


def handle_history_flow(chat_id, text, data):
    name = text.strip().lower()
    target = None
    for f in data.get("farms", []):
        if f["name"].lower() == name:
            target = f
            break
    if not target:
        send_message(chat_id, f"❌ Không tìm thấy <b>{text}</b>.")
        return

    history = target.get("reminder_history", [])
    if not history:
        msg = f"🕒 <b>Lịch sử nhắc - {target['name']}</b>\n\nChưa có lần nhắc nào."
    else:
        msg = f"🕒 <b>Lịch sử nhắc - {target['name']}</b>\n\n"
        for h in sorted(history, key=lambda x: x.get("date", ""), reverse=True)[:20]:
            t = h.get("type", "")
            label = {
                "3days": "Trước 3 ngày",
                "2days": "Trước 2 ngày",
                "1day": "Trước 1 ngày",
                "0day": "Đúng ngày",
            }.get(t, t)
            msg += f"• {h.get('date', '')}: {label}\n"

    if str(chat_id) in data["user_states"]:
        del data["user_states"][str(chat_id)]
        save_data(data)
    send_message(chat_id, msg)


# ================== BACKUP / CSV ==================


def handle_backup(chat_id, data):
    farms = data.get("farms", [])
    if not farms:
        send_message(chat_id, "📭 Chưa có dữ liệu để backup!")
        return
    backup = {
        "backup_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "farms": farms,
    }
    fn = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(fn, "w", encoding="utf-8") as f:
        json.dump(backup, f, ensure_ascii=False, indent=2)
    send_document(chat_id, fn, "💾 Backup dữ liệu farm")
    os.remove(fn)


def handle_export_csv(chat_id, data):
    farms = data.get("farms", [])
    if not farms:
        send_message(chat_id, "📭 Chưa có dữ liệu để export!")
        return
    fn = f"farms_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(fn, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "name",
                "owner_email",
                "members",
                "start_date",
                "renewal_day",
                "price",
                "chat_id",
            ]
        )
        for x in farms:
            w.writerow(
                [
                    x.get("name", ""),
                    x.get("owner_email", ""),
                    ",".join(x.get("members", [])),
                    x.get("start_date", ""),
                    x.get("renewal_day", ""),
                    x.get("price", ""),
                    x.get("chat_id", ""),
                ]
            )
    send_document(chat_id, fn, "📤 CSV farms")
    os.remove(fn)


# ================== TOGGLE REMINDER ==================


def start_toggle_reminder(chat_id, data):
    farms = data.get("farms", [])
    if not farms:
        send_message(chat_id, "📭 Chưa có farm nào!")
        return
    data["user_states"][str(chat_id)] = {
        "action": "toggle_reminder",
        "step": "select",
    }
    save_data(data)
    msg = "🔔 <b>Bật/Tắt nhắc</b>\n\nNhập tên farm:\n\n"
    for f in farms:
        st = "ON" if f.get("reminder_enabled", True) else "OFF"
        msg += f"• {f['name']} - {st}\n"
    send_message(chat_id, msg)


def handle_toggle_reminder_flow(chat_id, text, data):
    name = text.strip().lower()
    farms = data.get("farms", [])
    target = None
    for f in farms:
        if f["name"].lower() == name:
            target = f
            break
    if not target:
        send_message(chat_id, f"❌ Không tìm thấy <b>{text}</b>.")
        return
    cur = target.get("reminder_enabled", True)
    target["reminder_enabled"] = not cur
    save_data(data)
    st = "🔔 ĐÃ BẬT" if target["reminder_enabled"] else "🔕 ĐÃ TẮT"
    if str(chat_id) in data["user_states"]:
        del data["user_states"][str(chat_id)]
        save_data(data)
    send_message(chat_id, f"✅ {st} nhắc cho <b>{target['name']}</b>.")


# ================== LOGIN CHO TỪNG EMAIL TRONG FARM ==================


def start_set_mail_login(chat_id, data):
    farms = data.get("farms", [])
    if not farms:
        send_message(chat_id, "📭 Chưa có farm nào!")
        return
    data["user_states"][str(chat_id)] = {
        "action": "set_mail_login",
        "step": "choose_farm",
    }
    save_data(data)
    msg = "🔐 <b>Lưu thông tin login cho email</b>\n\nNhập <b>tên farm</b>:\n\n"
    for f in farms:
        msg += f"• {f['name']}\n"
    send_message(chat_id, msg)


def handle_set_mail_login_flow(chat_id, text, data):
    state = data["user_states"][str(chat_id)]
    step = state["step"]

    if step == "choose_farm":
        farms = data.get("farms", [])
        name = text.strip().lower()
        idx = -1
        for i, f in enumerate(farms):
            if f["name"].lower() == name:
                idx = i
                break
        if idx == -1:
            send_message(chat_id, f"❌ Không tìm thấy farm <b>{text}</b>. Nhập lại tên farm:")
            return
        state["farm_index"] = idx
        farm = farms[idx]
        emails = [farm["owner_email"]] + farm.get("members", [])
        state["emails"] = emails
        state["step"] = "choose_email"
        save_data(data)

        lst = ""
        for i, em in enumerate(emails, 1):
            lst += f"{i}. {em}\n"

        send_message(
            chat_id,
            f"✅ Đã chọn farm <b>{farm['name']}</b>\n\nDanh sách email:\n{lst}\nNhập <b>số thứ tự</b> email cần lưu thông tin login:",
        )

    elif step == "choose_email":
        try:
            idx = int(text.strip())
        except ValueError:
            send_message(chat_id, "❌ Vui lòng nhập số thứ tự hợp lệ.")
            return
        emails = state.get("emails", [])
        if not (1 <= idx <= len(emails)):
            send_message(chat_id, "❌ Số thứ tự không hợp lệ, nhập lại:")
            return
        email = emails[idx - 1]
        state["selected_email"] = email
        state["step"] = "password"
        save_data(data)
        send_message(
            chat_id,
            f"📧 Email: <b>{email}</b>\n\nNhập <b>mật khẩu</b> (password):",
        )

    elif step == "password":
        state["password"] = text.strip()
        state["step"] = "twofa"
        save_data(data)
        send_message(chat_id, "Nhập <b>mã 2FA</b> (hoặc gõ <code>skip</code> nếu không có):")

    elif step == "twofa":
        if text.strip().lower() == "skip":
            state["twofa"] = ""
        else:
            state["twofa"] = text.strip()
        state["step"] = "note"
        save_data(data)
        send_message(chat_id, "Nhập <b>ghi chú</b> (hoặc gõ <code>skip</code>):")

    elif step == "note":
        note = "" if text.strip().lower() == "skip" else text.strip()
        state["note"] = note
        state["step"] = "join_date"
        save_data(data)
        send_message(
            chat_id,
            "Nhập <b>ngày tham gia</b> (DD/MM/YYYY) (hoặc gõ <code>skip</code>):",
        )

    elif step == "join_date":
        txt = text.strip()
        if txt.lower() == "skip":
            state["join_date"] = ""
        else:
            try:
                d = datetime.strptime(txt, "%d/%m/%Y")
                state["join_date"] = d.strftime("%Y-%m-%d")
            except ValueError:
                send_message(chat_id, "❌ Sai định dạng. Nhập lại dạng DD/MM/YYYY hoặc gõ skip:")
                return
        state["step"] = "usage_days"
        save_data(data)
        send_message(
            chat_id,
            "Nhập <b>số ngày sử dụng</b> (vd: 30) (hoặc gõ <code>skip</code>):",
        )

    elif step == "usage_days":
        txt = text.strip()
        if txt.lower() == "skip":
            state["usage_days"] = 0
        else:
            try:
                days = int(txt)
                if days < 0:
                    days = 0
                state["usage_days"] = days
            except ValueError:
                send_message(chat_id, "❌ Vui lòng nhập số ngày hợp lệ hoặc gõ skip:")
                return
        state["step"] = "facebook"
        save_data(data)
        send_message(
            chat_id,
            "Nhập <b>Facebook khách</b> (link hoặc username) (hoặc gõ <code>skip</code>):",
        )

    elif step == "facebook":
        txt = text.strip()
        if txt.lower() == "skip":
            state["facebook"] = ""
        else:
            state["facebook"] = txt

        email = state["selected_email"]
        password = state.get("password", "")
        twofa = state.get("twofa", "")
        note = state.get("note", "")
        join_date = state.get("join_date", "")
        usage_days = state.get("usage_days", 0)
        facebook = state.get("facebook", "")

        farms = data.get("farms", [])
        farm = farms[state["farm_index"]]

        bundle = {
            "password": password,
            "twofa": twofa,
            "note": note,
        }
        enc = encrypt_text(json.dumps(bundle, ensure_ascii=False))

        farm.setdefault("email_logins", {})
        farm["email_logins"][email] = {
            "enc": enc,
            "join_date": join_date,
            "usage_days": usage_days,
            "facebook": facebook,
        }
        save_data(data)

        if str(chat_id) in data["user_states"]:
            del data["user_states"][str(chat_id)]
            save_data(data)

        send_message(
            chat_id,
            f"""✅ Đã lưu thông tin login cho:
📧 <b>{email}</b>
🧱 Farm: <b>{farm['name']}</b>

Bao gồm:
- Mật khẩu
- 2FA
- Ghi chú
- Ngày tham gia
- Thời gian sử dụng
- Facebook khách

Dùng /get_mail_login để xem lại khi cần.""",
        )


def start_get_mail_login(chat_id, data):
    farms = data.get("farms", [])
    if not farms:
        send_message(chat_id, "📭 Chưa có farm nào!")
        return
    data["user_states"][str(chat_id)] = {
        "action": "get_mail_login",
        "step": "choose_farm",
    }
    save_data(data)
    msg = "🔎 <b>Xem thông tin login email</b>\n\nNhập <b>tên farm</b>:\n\n"
    for f in farms:
        msg += f"• {f['name']}\n"
    send_message(chat_id, msg)


def handle_get_mail_login_flow(chat_id, text, data):
    state = data["user_states"][str(chat_id)]
    step = state["step"]

    if step == "choose_farm":
        farms = data.get("farms", [])
        name = text.strip().lower()
        idx = -1
        for i, f in enumerate(farms):
            if f["name"].lower() == name:
                idx = i
                break
        if idx == -1:
            send_message(chat_id, f"❌ Không tìm thấy farm <b>{text}</b>. Nhập lại tên farm:")
            return
        state["farm_index"] = idx
        farm = farms[idx]
        emails = [farm["owner_email"]] + farm.get("members", [])
        state["emails"] = emails
        state["step"] = "choose_email"
        save_data(data)

        lst = ""
        for i, em in enumerate(emails, 1):
            lst += f"{i}. {em}\n"
        send_message(
            chat_id,
            f"✅ Đã chọn farm <b>{farm['name']}</b>\n\nDanh sách email:\n{lst}\nNhập <b>số thứ tự</b> email cần xem login:",
        )

    elif step == "choose_email":
        try:
            idx = int(text.strip())
        except ValueError:
            send_message(chat_id, "❌ Vui lòng nhập số thứ tự hợp lệ.")
            return
        emails = state.get("emails", [])
        if not (1 <= idx <= len(emails)):
            send_message(chat_id, "❌ Số thứ tự không hợp lệ, nhập lại:")
            return
        email = emails[idx - 1]
        farms = data.get("farms", [])
        farm_index = state["farm_index"]
        farm = farms[farm_index]
        email_logins = farm.get("email_logins", {})
        entry = email_logins.get(email)

        if str(chat_id) in data.get("user_states", {}):
            del data["user_states"][str(chat_id)]
            save_data(data)

        if not entry:
            send_message(chat_id, f"❌ Chưa lưu login cho <b>{email}</b>.")
            return

        try:
            decoded = decrypt_text(entry.get("enc", ""))
            bundle = json.loads(decoded)
        except Exception as e:
            print("Lỗi giải mã email_login:", e)
            send_message(chat_id, "❌ Lỗi giải mã dữ liệu. Kiểm tra MASTER_SECRET.")
            return

        password = bundle.get("password", "")
        twofa = bundle.get("twofa", "")
        note = bundle.get("note", "")

        join_iso = entry.get("join_date", "")
        if join_iso:
            try:
                join_str = datetime.strptime(join_iso, "%Y-%m-%d").strftime(
                    "%d/%m/%Y"
                )
            except Exception:
                join_str = join_iso
        else:
            join_str = "(Không có)"

        usage_days = entry.get("usage_days", 0)
        if usage_days:
            usage_str = f"{usage_days} ngày"
        else:
            usage_str = "(Không có)"

        facebook = entry.get("facebook", "")
        if not facebook:
            facebook = "(Không có)"

        msg = f"""🔐 <b>Thông tin login cho email</b>

📧 Email: <b>{email}</b>

📅 Tham gia: {join_str}
🕒 Thời gian sử dụng: {usage_str}
👤 Facebook: {facebook}
📝 Ghi chú: {note if note else "(Không có)"}

🔑 Mật khẩu: <code>{password}</code>
🛡 2FA: <code>{twofa}</code>

👉 Bạn có thể copy trực tiếp trong Telegram hoặc dùng các nút bên dưới.
"""

        inline_keyboard = [
            [
                {
                    "text": "📋 Copy Email",
                    "callback_data": f"ce|{email}",
                }
            ],
            [
                {
                    "text": "📋 Copy Password",
                    "callback_data": f"cpw|{farm_index}|{email}",
                },
                {
                    "text": "📋 Copy 2FA",
                    "callback_data": f"c2f|{farm_index}|{email}",
                },
            ],
        ]

        send_message(chat_id, msg, reply_markup={"inline_keyboard": inline_keyboard})


# ================== CANCEL ==================


def cancel_action(chat_id, data):
    if str(chat_id) in data.get("user_states", {}):
        del data["user_states"][str(chat_id)]
        save_data(data)
        send_message(chat_id, "✅ Đã huỷ thao tác hiện tại.")
    else:
        send_message(chat_id, "ℹ️ Không có thao tác nào cần hủy.")


# ================== CALLBACK HANDLER (COPY) ==================


def handle_callback(callback):
    data_all = load_data()
    cb_id = callback.get("id")
    msg = callback.get("message") or {}
    chat = msg.get("chat") or {}
    chat_id = chat.get("id")
    data_str = callback.get("data") or ""

    if not chat_id or not data_str:
        if cb_id:
            answer_callback_query(cb_id)
        return

    try:
        if data_str.startswith("ce|"):
            # Copy Email
            email = data_str[3:]
            send_message(chat_id, f"<code>{email}</code>")
            if cb_id:
                answer_callback_query(cb_id, "Đã gửi email để copy.")
        elif data_str.startswith("cpw|"):
            # Copy Password
            parts = data_str.split("|", 2)
            if len(parts) == 3:
                _, idx_str, email = parts
                idx = int(idx_str)
                farms = data_all.get("farms", [])
                if 0 <= idx < len(farms):
                    farm = farms[idx]
                    entry = farm.get("email_logins", {}).get(email)
                    if entry:
                        decoded = decrypt_text(entry.get("enc", ""))
                        bundle = json.loads(decoded)
                        password = bundle.get("password", "")
                        send_message(chat_id, f"🔑 Password:\n<code>{password}</code>")
                        if cb_id:
                            answer_callback_query(cb_id, "Đã gửi password.")
                        return
            if cb_id:
                answer_callback_query(cb_id, "Không tìm thấy password.")
        elif data_str.startswith("c2f|"):
            # Copy 2FA
            parts = data_str.split("|", 2)
            if len(parts) == 3:
                _, idx_str, email = parts
                idx = int(idx_str)
                farms = data_all.get("farms", [])
                if 0 <= idx < len(farms):
                    farm = farms[idx]
                    entry = farm.get("email_logins", {}).get(email)
                    if entry:
                        decoded = decrypt_text(entry.get("enc", ""))
                        bundle = json.loads(decoded)
                        twofa = bundle.get("twofa", "")
                        send_message(chat_id, f"🛡 2FA:\n<code>{twofa}</code>")
                        if cb_id:
                            answer_callback_query(cb_id, "Đã gửi mã 2FA.")
                        return
            if cb_id:
                answer_callback_query(cb_id, "Không tìm thấy 2FA.")
        else:
            if cb_id:
                answer_callback_query(cb_id)
    except Exception as e:
        print("Lỗi handle_callback:", e)
        if cb_id:
            answer_callback_query(cb_id, "Có lỗi xảy ra.")


# ================== REMINDER LOOP ==================


def check_and_send_reminders(data):
    today = datetime.now().date()
    today_str = datetime.now().strftime("%Y-%m-%d")
    changed = False

    for f in data.get("farms", []):
        if not f.get("reminder_enabled", True):
            continue
        rd = get_next_renewal_date(f.get("renewal_day", 1)).date()
        diff = (rd - today).days

        chat_id = f.get("chat_id")
        if not chat_id:
            continue

        def add_hist(kind):
            hist = f.get("reminder_history", [])
            hist.append(
                {
                    "type": kind,
                    "date": today_str,
                    "renewal_date": rd.strftime("%Y-%m-%d"),
                }
            )
            f["reminder_history"] = hist

        if diff == 3 and f.get("last3") != today_str:
            send_message(chat_id, f"⏰ <b>{f['name']}</b> còn <b>3 ngày</b> đến hạn.")
            f["last3"] = today_str
            add_hist("3days")
            changed = True

        if diff == 2 and f.get("last2") != today_str:
            send_message(chat_id, f"⏰ <b>{f['name']}</b> còn <b>2 ngày</b> đến hạn.")
            f["last2"] = today_str
            add_hist("2days")
            changed = True

        if diff == 1 and f.get("last1") != today_str:
            send_message(chat_id, f"🔔 <b>{f['name']}</b> còn <b>1 ngày</b> đến hạn.")
            f["last1"] = today_str
            add_hist("1day")
            changed = True

        if diff == 0 and f.get("last0") != today_str:
            send_message(chat_id, f"🚨 <b>{f['name']}</b> HÔM NAY đến hạn thanh toán!")
            f["last0"] = today_str
            add_hist("0day")
            changed = True

    if changed:
        save_data(data)


# ================== MAIN LOOP ==================


def main():
    print("🤖 Bot nhắc hạn đang chạy...")
    offset = None
    last_check = datetime.now()
    data = load_data()

    while True:
        now = datetime.now()
        if (now - last_check).seconds >= 3600:
            data = load_data()
            check_and_send_reminders(data)
            last_check = now

        try:
            updates = get_updates(offset)
        except Exception as e:
            print("Lỗi get_updates:", e)
            time.sleep(5)
            continue

        if updates.get("ok"):
            for u in updates["result"]:
                offset = u["update_id"] + 1

                # Callback query (inline buttons)
                if "callback_query" in u:
                    handle_callback(u["callback_query"])
                    continue

                msg = u.get("message")
                if not msg:
                    continue
                chat_id = msg["chat"]["id"]
                text = msg.get("text", "")
                if not isinstance(text, str):
                    continue
                text = text.strip()

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
                elif text == "/bao_cao_ngay":
                    handle_daily_report(chat_id, data)
                elif text == "/bao_cao_tuan":
                    handle_weekly_report(chat_id, data)
                elif text == "/lich_su":
                    start_history(chat_id, data)
                elif text == "/sao_luu":
                    handle_backup(chat_id, data)
                elif text == "/xuat_csv":
                    handle_export_csv(chat_id, data)
                elif text == "/bat_tat_nhac":
                    start_toggle_reminder(chat_id, data)
                elif text == "/set_mail_login":
                    start_set_mail_login(chat_id, data)
                elif text == "/get_mail_login":
                    start_get_mail_login(chat_id, data)
                elif text == "/huy":
                    cancel_action(chat_id, data)

                elif text == "➕ Thêm":
                    start_add_farm(chat_id, data)
                elif text == "📋 Danh sách":
                    handle_list_farms(chat_id, data)
                elif text == "📊 Thống kê":
                    handle_statistics(chat_id, data)
                elif text == "📆 Báo cáo tuần":
                    handle_weekly_report(chat_id, data)
                elif text == "📅 Báo cáo hôm nay":
                    handle_daily_report(chat_id, data)
                elif text == "💾 Sao lưu":
                    handle_backup(chat_id, data)
                elif text == "📤 Xuất CSV":
                    handle_export_csv(chat_id, data)
                elif text == "🔔 Bật/Tắt nhắc":
                    start_toggle_reminder(chat_id, data)

                elif str(chat_id) in data.get("user_states", {}):
                    state = data["user_states"][str(chat_id)]
                    action = state.get("action")

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
                    elif action == "history":
                        handle_history_flow(chat_id, text, data)
                    elif action == "set_mail_login":
                        handle_set_mail_login_flow(chat_id, text, data)
                    elif action == "get_mail_login":
                        handle_get_mail_login_flow(chat_id, text, data)

                else:
                    send_message(chat_id, "❌ Lệnh không hợp lệ. Gửi /help để xem hướng dẫn.")

        time.sleep(1)


if __name__ == "__main__":
    main()
