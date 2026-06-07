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

        # Oddiy shriftdan foydalanamiz (Railwayda boshqa shrift yo'q)
        font_name = ImageFont.load_default()   # Hozircha default
        font_info = ImageFont.load_default()

        # Ism (katta qilishga harakat)
        draw.text((340, 460), name, fill=(0, 0, 0), font=font_name)

        # Jild / Son
        draw.text((370, 780), volume, fill=(0, 0, 0), font=font_info)

        # Sana
        draw.text((370, 850), date, fill=(0, 0, 0), font=font_info)

        # Verification Code
        draw.text((290, 1040), code, fill=(180, 0, 0), font=font_info)

        filename = f"cert_{code}.png"
        img.save(filename)
        return filename
    except Exception as e:
        print("Xatolik:", e)
        return None

# Qolgan kodlar...
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
    # ... (oldingi kodni saqlab qoldim, joy tejash uchun qisqartirdim)
    # To'liq kod kerak bo'lsa ayting, qolgan qismini ham beraman.

    # Hozircha faqat asosiy qismni sinab ko'ramiz
    pass  # To'liq kodni oldingi xabarlardan oling

async def main():
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
