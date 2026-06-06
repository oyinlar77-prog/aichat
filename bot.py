import asyncio
import json
import os
import random
import string
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from PIL import Image, ImageDraw, ImageFont

# ====================== SOZLAMALAR ======================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=TOKEN)
dp = Dispatcher()

TEMPLATE_PATH = "certificate_template.png"
DATA_FILE = "certificates.json"

# ====================== TUGMALAR ======================
main_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="✅ Sertifikatni tekshirish")]], resize_keyboard=True)

admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛠 Sertifikat yaratish")],
        [KeyboardButton(text="✅ Sertifikatni tekshirish")]
    ], 
    resize_keyboard=True
)

user_states = {}

def generate_code():
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=4)) + "-" + ''.join(random.choices(chars, k=4))

# ====================== START ======================
@dp.message(Command("start"))
async def start(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("👋 Salom Admin!", reply_markup=admin_kb)
    else:
        await message.answer("👋 Xush kelibsiz! Sertifikatni tekshirish uchun tugmani bosing.", reply_markup=main_kb)

# ====================== SERTIFIKAT YARATISH ======================
@dp.message(lambda m: m.text == "🛠 Sertifikat yaratish" and m.from_user.id == ADMIN_ID)
async def create_cert(message: types.Message):
    user_states[message.from_user.id] = {"step": "name"}
    await message.answer("👤 Muallifning to‘liq ism va familiyasini yozing:")

@dp.message()
async def process_message(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()

    if user_id not in user_states:
        # Tekshirish qismi
        if len(text) == 9 and text[4] == "-":
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if text in data:
                    d = data[text]
                    await message.answer(f"✅ Sertifikat topildi!\n\n👤 {d['name']}\n📚 {d['volume']}\n📅 {d['date']}")
                else:
                    await message.answer("❌ Bu kod noto‘g‘ri yoki topilmadi.")
            except:
                await message.answer("❌ Xatolik yuz berdi.")
        return

    state = user_states[user_id]

    if state["step"] == "name":
        state["name"] = text
        state["step"] = "volume"
        await message.answer("📚 Jild / Son (masalan: 1(3)):")
    
    elif state["step"] == "volume":
        state["volume"] = text
        code = generate_code()
        date = datetime.now().strftime("%d.%m.%Y")

        cert = {
            "name": state["name"],
            "volume": state["volume"],
            "date": date,
            "code": code
        }

        # Saqlash
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                all_certs = json.load(f)
        else:
            all_certs = {}

        all_certs[code] = cert

        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(all_certs, f, ensure_ascii=False, indent=2)

        await message.answer(f"✅ Sertifikat tayyor!\n\nKod: `{code}`\n\nRasm yaqin orada qo‘shiladi.", parse_mode="Markdown")
        del user_states[user_id]

# ====================== ISHGA TUSHIRISH ======================
async def main():
    print("✅ Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
