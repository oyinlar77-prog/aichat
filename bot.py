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
 
TEMPLATE_PATH = "certificate_template.jpg"  # yoki .png — rasmingiz qaysi formatda bo'lsa
DATA_FILE = "certificates.json"
 
user_states = {}
 
admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛠 Sertifikat yaratish")],
        [KeyboardButton(text="✅ Sertifikatni tekshirish")],
    ],
    resize_keyboard=True,
)
 
main_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="✅ Sertifikatni tekshirish")]],
    resize_keyboard=True,
)
 
 
def generate_code():
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=4)) + "-" + "".join(random.choices(chars, k=4))
 
 
def get_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    """Font yuklaydi. Topilmasa fallback ishlatadi."""
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()
 
 
def create_certificate(name: str, volume: str, date: str, code: str) -> str | None:
    """
    Sertifikat rasmini yaratadi va fayl nomini qaytaradi.
    Shablonning o'lchami: 1248 x 816 px
    """
    try:
        img = Image.open(TEMPLATE_PATH).convert("RGB")
        draw = ImageDraw.Draw(img)
        W = img.width  # 1248
 
        # ── Fontlar ──────────────────────────────────────────────────────────
        # Railwayda DejaVu / FreeSans paketlari odatda o'rnatilgan bo'ladi.
        # Agar o'rnatilmagan bo'lsa: apt-get install -y fonts-dejavu fonts-freefont-ttf
        ITALIC_FONT  = "/usr/share/fonts/truetype/freefont/FreeSansOblique.ttf"
        REGULAR_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        BOLD_FONT    = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
 
        font_name = get_font(ITALIC_FONT,  38)   # muallif ismi — kursiv, yirik
        font_info = get_font(REGULAR_FONT, 26)   # Jild / Sana
        font_code = get_font(BOLD_FONT,    28)   # Verification code — qalin, qizil
 
        # ── Muallif ismi — markazlashtirilgan ────────────────────────────────
        bbox   = draw.textbbox((0, 0), name, font=font_name)
        text_w = bbox[2] - bbox[0]
        name_x = (W - text_w) // 2
        name_y = 488
        draw.text((name_x, name_y), name, fill=(20, 20, 20), font=font_name)
 
        # ── Jild / Son ───────────────────────────────────────────────────────
        # "Jild / Son:" matni ~x=330-475 gacha, qiymat undan keyin
        draw.text((478, 572), volume, fill=(20, 20, 20), font=font_info)
 
        # ── Sana ─────────────────────────────────────────────────────────────
        # "Sana:" matni ~x=330-420 gacha
        draw.text((422, 616), date, fill=(20, 20, 20), font=font_info)
 
        # ── Verification Code ─────────────────────────────────────────────────
        # "Verification Code:" matni ~x=165-390 gacha
        draw.text((393, 713), code, fill=(150, 0, 0), font=font_code)
 
        filename = f"cert_{code}.png"
        img.save(filename, format="PNG")
        return filename
 
    except Exception as e:
        print("Sertifikat yaratishda xatolik:", e)
        return None
 
 
# ── Handlers ──────────────────────────────────────────────────────────────────
 
@dp.message(Command("start"))
async def start(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("👋 Salom Admin!", reply_markup=admin_kb)
    else:
        await message.answer("👋 Xush kelibsiz!", reply_markup=main_kb)
 
 
@dp.message(lambda m: m.text == "🛠 Sertifikat yaratish" and m.from_user.id == ADMIN_ID)
async def create_start(message: types.Message):
    user_states[message.from_user.id] = "name"
    await message.answer("👤 Muallifning to'liq ism va familiyasini yozing:")
 
 
@dp.message()
async def process(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip() if message.text else ""
 
    # ── Admin: sertifikat yaratish oqimi ─────────────────────────────────────
    if user_id in user_states:
        state = user_states[user_id]
 
        if state == "name":
            user_states[user_id] = {"step": "volume", "name": text}
            await message.answer("📚 Jild / Son kiriting (masalan: 1(3)):")
            return
 
        if isinstance(state, dict) and state.get("step") == "volume":
            volume = text
            name   = state["name"]
            code   = generate_code()
            date   = datetime.now().strftime("%d.%m.%Y")
 
            filename = create_certificate(name, volume, date, code)
 
            # JSON saqlash
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    all_data = json.load(f)
            else:
                all_data = {}
 
            all_data[code] = {"name": name, "volume": volume, "date": date, "code": code}
 
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2)
 
            if filename:
                await message.answer_photo(
                    types.FSInputFile(filename),
                    caption=f"✅ Sertifikat tayyor!\nKod: `{code}`",
                    parse_mode="Markdown",
                )
                os.remove(filename)
            else:
                await message.answer("❌ Rasm yaratishda xatolik bo'ldi.")
 
            del user_states[user_id]
            return
 
    # ── Sertifikatni tekshirish ───────────────────────────────────────────────
    if len(text) == 9 and text[4] == "-":
        if not os.path.exists(DATA_FILE):
            await message.answer("❌ Hech qanday sertifikat topilmadi.")
            return
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if text.upper() in data:
                d = data[text.upper()]
                await message.answer(
                    f"✅ Sertifikat haqiqiy!\n\n"
                    f"👤 {d['name']}\n"
                    f"📚 Jild / Son: {d['volume']}\n"
                    f"📅 Sana: {d['date']}"
                )
            else:
                await message.answer("❌ Bu kod topilmadi.")
        except Exception as e:
            print("Tekshirishda xatolik:", e)
            await message.answer("❌ Xatolik yuz berdi.")
 
 
# ── Main ──────────────────────────────────────────────────────────────────────
 
async def main():
    print("✅ Bot ishga tushdi!")
    await dp.start_polling(bot)
 
 
if __name__ == "__main__":
    asyncio.run(main())
 
