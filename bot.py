
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
 
TOKEN      = os.getenv("BOT_TOKEN")
ADMIN_ID   = int(os.getenv("ADMIN_ID"))
CHANNEL_ID = "@GJCDI_Certificate"   # kanal username
 
bot = Bot(token=TOKEN)
dp  = Dispatcher()
 
TEMPLATE_PATH = "certificate_template.png"
DATA_FILE     = "certificates.json"
 
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
 
FONT_ITALIC  = "/usr/share/fonts/truetype/freefont/FreeSansOblique.ttf"
FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD    = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
 
def load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()
 
def generate_code() -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=4)) + "-" + random.choice(chars)
 
def create_certificate(name: str, volume: str, date: str, code: str) -> str | None:
    try:
        img  = Image.open(TEMPLATE_PATH).convert("RGB")
        draw = ImageDraw.Draw(img)
        W    = img.width
 
        font_name = load_font(FONT_ITALIC,  44)
        font_info = load_font(FONT_REGULAR, 28)
        font_code = load_font(FONT_BOLD,    28)
 
        # Ism
        bbox   = draw.textbbox((0, 0), name, font=font_name)
        text_w = bbox[2] - bbox[0]
        if text_w > W - 280:
            font_name = load_font(FONT_ITALIC, 36)
            bbox   = draw.textbbox((0, 0), name, font=font_name)
            text_w = bbox[2] - bbox[0]
        name_x = (W - text_w) // 2
        draw.text((name_x, 458), name, fill=(20, 20, 20), font=font_name)
 
        # Jild / Son
        b      = draw.textbbox((0, 0), volume, font=font_info)
        h_info = b[3] - b[1]
        draw.text((482, 577 - h_info // 2), volume, fill=(20, 20, 20), font=font_info)
 
        # Sana
        draw.text((431, 622 - h_info // 2), date, fill=(20, 20, 20), font=font_info)
 
        # Verification Code
        bc     = draw.textbbox((0, 0), code, font=font_code)
        h_code = bc[3] - bc[1]
        draw.text((395, 724 - h_code // 2), code, fill=(150, 0, 0), font=font_code)
 
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
    text    = (message.text or "").strip()
 
    # ── Admin: sertifikat yaratish ─────────────────────────────────────────
    if user_id in user_states:
        state = user_states[user_id]
 
        if state == "name":
            user_states[user_id] = {"step": "volume", "name": text}
            await message.answer("📚 Jild / Son kiriting (masalan: 1(3)):")
            return
 
        if isinstance(state, dict) and state.get("step") == "volume":
            volume   = text
            name     = state["name"]
            code     = generate_code()
            date     = datetime.now().strftime("%d.%m.%Y")
            filename = create_certificate(name, volume, date, code)
 
            all_data = {}
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    all_data = json.load(f)
            all_data[code] = {"name": name, "volume": volume, "date": date, "code": code}
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2)
 
            if filename:
                caption = (
                    "<a href='https://t.me/GJCDI_Certificate_Bot'>Glob Journal</a> "
                    "orqali tekshirib olishingiz mumkin"
                )
 
                # Adminga yuborish
                await message.answer_photo(
                    types.FSInputFile(filename),
                    caption=caption,
                    parse_mode="HTML",
                )
 
                # Kanalga ham yuborish
                try:
                    await bot.send_photo(
                        chat_id=CHANNEL_ID,
                        photo=types.FSInputFile(filename),
                        caption=caption,
                        parse_mode="HTML",
                    )
                except Exception as e:
                    print("Kanalga yuborishda xatolik:", e)
                    await message.answer("⚠️ Kanalga yuborishda xatolik bo'ldi.")
 
                os.remove(filename)
            else:
                await message.answer("❌ Rasm yaratishda xatolik bo'ldi.")
 
            del user_states[user_id]
            return
 
    # ── Sertifikatni tekshirish (format: XXXX-X) ───────────────────────────
    if len(text) == 6 and text[4] == "-":
        if not os.path.exists(DATA_FILE):
            await message.answer("❌ Hech qanday sertifikat topilmadi.")
            return
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            key = text.upper()
            if key in data:
                d = data[key]
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
 
