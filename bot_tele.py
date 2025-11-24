import telebot
import requests
import threading
import time
from flask import Flask
from threading import Thread

# --- PHẦN 1: TẠO WEB GIẢ ĐỂ LỪA RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "I'm alive! Bot đang chạy ngon lành."

def run_http():
    # Mở cổng 8080 (để Render nhìn thấy)
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_http)
    t.start()

# --- PHẦN 2: LOGIC CỦA BOT ---
API_TOKEN = '8525540577:AAFXfGdYgpcoJPC80zjYVlATLeJkqk1iHdE' # Token của bạn
bot = telebot.TeleBot(API_TOKEN)

# Danh sách các lệnh cảnh báo
watch_list = []

def lay_gia_coin(symbol):
    # Tạo cặp tiền, ví dụ: BTC -> BTCUSDT
    pair = symbol.upper() + "USDT"
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={pair}"
    
    try:
        # Thêm timeout để không bị treo nếu mạng lag
        resp = requests.get(url, timeout=5)
        
        # In ra để kiểm tra xem Binance trả về cái gì
        # print(f"Binance trả về: {resp.text}") 
        
        data = resp.json()
        
        if "price" in data:
            return float(data['price'])
        else:
            # Nếu Binance báo lỗi (Ví dụ: Invalid symbol)
            print(f"❌ Lỗi Binance: {data}")
            return None
            
    except Exception as e:
        print(f"❌ Lỗi kết nối API: {e}")
        return None
# Luồng chạy ngầm (Canh giá)
def luong_canh_gia():
    print("👀 Đang kích hoạt chế độ canh giá...")
    while True:
        try:
            for order in watch_list.copy():
                chat_id = order['chat_id']
                coin = order['coin']
                target = order['target']
                
                gia_hien_tai = lay_gia_coin(coin)
                
                # Nếu giá tụt xuống dưới mức target -> Báo động
                if gia_hien_tai and gia_hien_tai <= target:
                    msg = (
                        f"🚨 <b>BÁO ĐỘNG SẾP ƠI!</b> 🚨\n\n"
                        f"📉 <b>{coin}</b> đã tụt xuống mức <b>${gia_hien_tai:,.2f}</b>\n"
                        f"(Mục tiêu: ${target:,.2f})\n\n"
                        f"👉 Vào hốt ngay kẻo lỡ!"
                    )
                    try:
                        bot.send_message(chat_id, msg, parse_mode="HTML")
                        watch_list.remove(order) # Xóa lệnh để đỡ báo lại
                    except Exception as e:
                        print(f"Lỗi gửi tin: {e}")
        except Exception as e:
            print(f"Lỗi luồng canh giá: {e}")
            
        time.sleep(10) # Nghỉ 10s

# Xử lý lệnh /canh
@bot.message_handler(commands=['canh'])
def dat_lenh_canh(message):
    try:
        text = message.text.split()
        if len(text) < 3:
            bot.reply_to(message, "⚠️ Sai cú pháp! Ví dụ: /canh btc 90000")
            return
        
        coin = text[1].upper()
        target = float(text[2])
        
        # 1. Kiểm tra giá trước
        gia_now = lay_gia_coin(coin)
        
        if gia_now is None:
            bot.reply_to(message, f"❌ Không tìm thấy coin <b>{coin}</b> hoặc API bị chặn!", parse_mode="HTML")
            return # Dừng lại, không lưu lệnh canh nữa

        # 2. Nếu có giá thì mới lưu
        new_order = {
            "chat_id": message.chat.id,
            "coin": coin,
            "target": target
        }
        watch_list.append(new_order)
        
        bot.reply_to(message, f"✅ Đã cài báo thức!\nKhi nào <b>{coin}</b> tụt xuống <b>${target}</b> em sẽ gọi.\n(Giá hiện tại: ${gia_now})", parse_mode="HTML")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Lỗi xử lý: {e}")
@bot.message_handler(commands=['list'])
def xem_danh_sach(message):
    if not watch_list:
        bot.reply_to(message, "📭 Chưa có lệnh canh nào cả.")
        return
    
    msg = "📋 <b>DANH SÁCH ĐANG CANH:</b>\n"
    for order in watch_list:
        msg += f"- {order['coin']}: Chờ dưới ${order['target']}\n"
    bot.reply_to(message, msg, parse_mode="HTML")

# --- PHẦN 3: CHẠY CHƯƠNG TRÌNH ---
if __name__ == "__main__":
    # 1. Kích hoạt Web giả (để Render không tắt)
    keep_alive()
    
    # 2. Kích hoạt luồng canh giá ngầm
    t = threading.Thread(target=luong_canh_gia)
    t.start()

    # 3. Kích hoạt Bot chính
    print("✅ Bot Pro đang chạy...")
    bot.infinity_polling()