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

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=TOKEN)
dp = Dispatcher()

TEMPLATE_PATH = "certificate_template.png"
DATA_FILE = "certificates.json"

user_states = {}

admin_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🛠 Sertifikat yaratish")], 
              [KeyboardButton(text="✅ Sertifikatni tekshirish")]],
    resize_keyboard=True
)

main_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="✅ Sertifikatni tekshirish")]], resize_keyboard=True)

def generate_code():
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=4)) + "-" + ''.join(random.choices(chars, k=4))

def create_certificate(name, volume, date, code):
    try:
        img = Image.open(TEMPLATE_PATH)
        draw = ImageDraw.Draw(img)

        try:
            font_name = ImageFont.truetype("arial.ttf", 85)
            font_info = ImageFont.truetype("arial.ttf", 50)
        except:
            font_name = ImageFont.load_default()
            font_info = ImageFont.load_default()

        draw.text((360, 460), name, fill=(0, 0, 0), font=font_name)
        draw.text((375, 780), volume, fill=(0, 0, 0), font=font_info)
        draw.text((375, 850), date, fill=(0, 0, 0), font=font_info)
        draw.text((295, 1040), code, fill=(180, 0, 0), font=font_info)

        filename = f"cert_{code}.png"
        img.save(filename)
        return filename
    except Exception as e:
        print("Xatolik:", e)
        return None

@dp.message(Command("start"))
async def start(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("👋 Salom Admin!", reply_markup=admin_kb)
    else:
        await message.answer("👋 Xush kelibsiz!", reply_markup=main_kb)

@dp.message(lambda m: m.text == "🛠 Sertifikat yaratish" and m.from_user.id == ADMIN_ID)
async def create_start(message: types.Message):
    user_states[message.from_user.id] = "name"
    await message.answer("👤 Muallifning to‘liq ism va familiyasini yozing:")

@dp.message()
async def process(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()

    if user_id in user_states:
        current_state = user_states[user_id]

        if current_state == "name":
            user_states[user_id] = {"step": "volume", "name": text}
            await message.answer("📚 Jild / Son kiriting (masalan: 1(3)):")
            return

        elif current_state.get("step") == "volume":
            volume = text
            name = current_state["name"]
            code = generate_code()
            date = datetime.now().strftime("%d.%m.%Y")

            filename = create_certificate(name, volume, date, code)

            cert = {"name": name, "volume": volume, "date": date, "code": code}
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    all_data = json.load(f)
            else:
                all_data = {}
            all_data[code] = cert
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2)

            if filename:
                await message.answer_photo(types.FSInputFile(filename), caption=f"✅ Sertifikat tayyor!\nKod: `{code}`", parse_mode="Markdown")
                os.remove(filename)
            else:
                await message.answer("❌ Rasm yaratishda xatolik bo'ldi.")

            del user_states[user_id]
            return

    # Tekshirish
    if len(text) == 9 and text[4] == "-":
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

async def main():
    print("✅ Bot ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
