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

user_states = {}

# ====================== TUGMALAR ======================
admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛠 Sertifikat yaratish")],
        [KeyboardButton(text="✅ Sertifikatni tekshirish")]
    ], 
    resize_keyboard=True
)

main_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="✅ Sertifikatni tekshirish")]], resize_keyboard=True)

def generate_code():
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=4)) + "-" + ''.join(random.choices(chars, k=4))

# ====================== SERTIFIKAT YARATISH ======================
def create_certificate(name, volume, date, code):
    try:
        img = Image.open(TEMPLATE_PATH)
        draw = ImageDraw.Draw(img)
        
        # Shrift (agar yo'q bo'lsa oddiy shriftdan foydalanadi)
        try:
            font = ImageFont.truetype("arial.ttf", 60)
            small_font = ImageFont.truetype("arial.ttf", 45)
        except:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        # Ism-familya
        draw.text((450, 620), name, fill=(0, 0, 0), font=font)
        
        # Jild/Son
        draw.text((450, 780), volume, fill=(0, 0, 0), font=small_font)
        
        # Sana
        draw.text((450, 850), date, fill=(0, 0, 0), font=small_font)
        
        # Verification Code
        draw.text((280, 1050), code, fill=(200, 0, 0), font=small_font)

        filename = f"cert_{code}.png"
        img.save(filename)
        return filename
    except Exception as e:
        print("Rasm yaratishda xatolik:", e)
        return None

# ====================== HANDLERLAR ======================
@dp.message(Command("start"))
async def start(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("👋 Salom Admin!", reply_markup=admin_kb)
    else:
        await message.answer("👋 Xush kelibsiz!", reply_markup=main_kb)

@dp.message(lambda m: m.text == "🛠 Sertifikat yaratish" and m.from_user.id == ADMIN_ID)
async def create_start(message: types.Message):
    user_states[message.from_user.id] = {"step": "name"}
    await message.answer("👤 Muallifning to‘liq ism va familiyasini yozing:")

@dp.message()
async def process(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()

    if user_id in user_states:
        state = user_states[user_id]
        
        if state["step"] == "name":
            state["name"] = text
            state["step"] = "volume"
            await message.answer("📚 Jild / Son kiriting (masalan: 1(3)):")
            
        elif state["step"] == "volume":
            state["volume"] = text
            code = generate_code()
            date = datetime.now().strftime("%d.%m.%Y")
            
            # Rasm yaratish
            filename = create_certificate(state["name"], text, date, code)
            
            # Ma'lumotni saqlash
            cert = {"name": state["name"], "volume": text, "date": date, "code": code}
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    all_data = json.load(f)
            else:
                all_data = {}
            all_data[code] = cert
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2)
            
            if filename and os.path.exists(filename):
                await message.answer_photo(photo=types.FSInputFile(filename), 
                                         caption=f"✅ Sertifikat tayyor!\nKod: `{code}`", parse_mode="Markdown")
                os.remove(filename)  # faylni tozalash
            else:
                await message.answer("❌ Rasm yaratishda xatolik bo'ldi.")
            
            del user_states[user_id]

    # Tekshirish qismi
    elif len(text) == 9 and text[4] == "-":
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if text in data:
                d = data[text]
                await message.answer(f"✅ Sertifikat haqiqiy!\n\n👤 {d['name']}\n📚 {d['volume']}\n📅 {d['date']}")
            else:
                await message.answer("❌ Bu kod topilmadi.")
        except:
            await message.answer("❌ Xatolik yuz berdi.")

# ====================== ISHGA TUSHIRISH ======================
async def main():
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
