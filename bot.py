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
    keyboard=[[KeyboardButton(text="🛠 Sertifikat yaratish")], 
              [KeyboardButton(text="✅ Sertifikatni tekshirish")]],
    resize_keyboard=True
)

main_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="✅ Sertifikatni tekshirish")]], resize_keyboard=True)

def generate_code():
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=4)) + "-" + ''.join(random.choices(chars, k=4))

# ====================== SERTIFIKAT YARATISH (ENG ANIQ VERSIYA) ======================
def create_certificate(name, volume, date, code):
    try:
        img = Image.open(TEMPLATE_PATH)
        draw = ImageDraw.Draw(img)

        # Shriftlar
        try:
            font_name = ImageFont.truetype("arial.ttf", 78)   # Ism-familya uchun
            font_text = ImageFont.truetype("arial.ttf", 52)   # Asosiy matn
            font_small = ImageFont.truetype("arial.ttf", 46)  # Jild va Sana uchun
        except:
            font_name = ImageFont.load_default()
            font_text = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # =================== ANIQ JOYLASHUV ===================

        # 1. Ism va Familiya
        draw.text((385, 485), name, fill=(0, 0, 0), font=font_name)

        # 2. Asosiy o‘zbekcha matn (ikki qator)
        draw.text((235, 655), "ilmiy-fan rivojiga o‘zining dolzarb va sifatli ilmiy maqolasi bilan", 
                  fill=(0, 0, 0), font=font_text)
        
        draw.text((295, 715), "hissa qo‘shganligi uchun ushbu sertifikat bilan taqdirlanadi.", 
                  fill=(0, 0, 0), font=font_text)

        # 3. Jild / Son
        draw.text((380, 815), volume, fill=(0, 0, 0), font=font_small)

        # 4. Sana
        draw.text((380, 875), date, fill=(0, 0, 0), font=font_small)

        # 5. Verification Code
        draw.text((295, 1035), code, fill=(180, 0, 0), font=font_small)

        filename = f"cert_{code}.png"
        img.save(filename)
        return filename
    except Exception as e:
        print("Xatolik:", e)
        return None

# ====================== QOLGAN KOD ======================
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
        
        if state.get("step") == "name":
            state["name"] = text
            state["step"] = "volume"
            await message.answer("📚 Jild / Son kiriting (masalan: 1(3)):")
            return
            
        elif state.get("step") == "volume":
            state["volume"] = text
            code = generate_code()
            date = datetime.now().strftime("%d.%m.%Y")
            
            filename = create_certificate(state["name"], text, date, code)
            
            cert = {"name": state["name"], "volume": text, "date": date, "code": code}
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    all_data = json.load(f)
            else:
                all_data = {}
            all_data[code] = cert
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2)
            
            if filename:
                await message.answer_photo(types.FSInputFile(filename), 
                                         caption=f"✅ Sertifikat tayyor!\nKod: `{code}`", parse_mode="Markdown")
                os.remove(filename)
            else:
                await message.answer("❌ Rasm yaratishda xatolik.")
            
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
