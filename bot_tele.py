import telebot
import requests
import threading
import time

# --- CẤU HÌNH ---
API_TOKEN = '8525540577:AAFXfGdYgpcoJPC80zjYVlATLeJkqk1iHdE'
bot = telebot.TeleBot(API_TOKEN)

# Danh sách các lệnh cảnh báo
# Cấu trúc: {"chat_id": 123, "coin": "BTC", "target": 95000}
watch_list = []

def lay_gia_coin(symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol.upper()}USDT"
        resp = requests.get(url).json()
        return float(resp['price'])
    except:
        return None

# --- LUỒNG CHẠY NGẦM (BẢO VỆ) ---
def luong_canh_gia():
    print("👀 Đang kích hoạt chế độ canh giá...")
    while True:
        # Duyệt qua danh sách các lệnh đang chờ
        # Dùng copy() để tránh lỗi khi xóa phần tử trong lúc duyệt
        for order in watch_list.copy(): 
            chat_id = order['chat_id']
            coin = order['coin']
            target = order['target']
            
            gia_hien_tai = lay_gia_coin(coin)
            
            if gia_hien_tai and gia_hien_tai <= target:
                # --- GIÁ ĐÃ CHẠM MỐC! BÁO ĐỘNG! ---
                msg = (
                    f"🚨 <b>BÁO ĐỘNG SẾP ƠI!</b> 🚨\n\n"
                    f"📉 <b>{coin}</b> đã tụt xuống mức <b>${gia_hien_tai:,.2f}</b>\n"
                    f"(Mục tiêu: ${target:,.2f})\n\n"
                    f"👉 Vào hốt ngay kẻo lỡ!"
                )
                try:
                    bot.send_message(chat_id, msg, parse_mode="HTML")
                    # Báo xong thì xóa lệnh này đi để đỡ báo lại liên tục
                    watch_list.remove(order) 
                except Exception as e:
                    print(f"Lỗi gửi tin: {e}")
        
        # Nghỉ 10 giây rồi check tiếp (Đừng check nhanh quá Binance khóa IP)
        time.sleep(10)

# --- XỬ LÝ TIN NHẮN ---

@bot.message_handler(commands=['canh'])
def dat_lenh_canh(message):
    # Cú pháp: /canh btc 90000
    try:
        text = message.text.split()
        if len(text) < 3:
            bot.reply_to(message, "⚠️ Sai cú pháp! Ví dụ: /canh btc 90000")
            return
        
        coin = text[1].upper()
        target = float(text[2])
        
        # Lưu vào danh sách theo dõi
        new_order = {
            "chat_id": message.chat.id,
            "coin": coin,
            "target": target
        }
        watch_list.append(new_order)
        
        gia_now = lay_gia_coin(coin)
        bot.reply_to(message, f"✅ Đã cài báo thức!\nKhi nào <b>{coin}</b> tụt xuống <b>${target}</b> em sẽ gọi.\n(Giá hiện tại: ${gia_now})", parse_mode="HTML")
        
    except Exception:
        bot.reply_to(message, "❌ Lỗi rồi! Số tiền phải là số nhé.")

@bot.message_handler(commands=['list'])
def xem_danh_sach(message):
    if not watch_list:
        bot.reply_to(message, "📭 Chưa có lệnh canh nào cả.")
        return
    
    msg = "📋 <b>DANH SÁCH ĐANG CANH:</b>\n"
    for order in watch_list:
        msg += f"- {order['coin']}: Chờ dưới ${order['target']}\n"
    bot.reply_to(message, msg, parse_mode="HTML")

# --- MAIN ---
# Kích hoạt luồng chạy ngầm trước
t = threading.Thread(target=luong_canh_gia)
t.start()

# Kích hoạt Bot
print("✅ Bot Pro đang chạy...")
bot.infinity_polling()