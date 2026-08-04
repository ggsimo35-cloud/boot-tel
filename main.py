import asyncio
import sqlite3

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery


BOT_TOKEN = "8882282653:AAGieiKuEadfsfE88baF4dYZrfBUSyjqiCQ"

CHANNEL_ID = -1004424805545

PRICE = 50


bot = Bot(BOT_TOKEN)
dp = Dispatcher()


# إنشاء قاعدة البيانات
db = sqlite3.connect("users.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY
)
""")

db.commit()


@dp.message(Command("start"))
async def start(message: types.Message):

    user_id = message.from_user.id

    cursor.execute(
        "SELECT user_id FROM users WHERE user_id=?",
        (user_id,)
    )

    if cursor.fetchone():
        await message.answer(
            "✅ أنت مشترك بالفعل."
        )
        return


    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="⭐ دفع 50 Stars",
                    callback_data="pay"
                )
            ]
        ]
    )

    await message.answer(
        "اشترك للوصول إلى القناة الخاصة:",
        reply_markup=keyboard
    )



@dp.callback_query(lambda c: c.data == "pay")
async def pay(callback: types.CallbackQuery):

    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title="اشتراك القناة",
        description="دخول دائم إلى القناة الخاصة",
        payload="one_time_channel_access",
        provider_token="",
        currency="XTR",
        prices=[
            LabeledPrice(
                label="اشتراك",
                amount=50
            )
        ]
    )



@dp.pre_checkout_query()
async def checkout(query: PreCheckoutQuery):

    await bot.answer_pre_checkout_query(
        query.id,
        ok=True
    )



@dp.message(lambda m: m.successful_payment)
async def success(message: types.Message):

    user_id = message.from_user.id

    # حفظ المشترك
    cursor.execute(
        "INSERT OR IGNORE INTO users VALUES (?)",
        (user_id,)
    )

    db.commit()


    # إنشاء رابط خاص للاستخدام مرة واحدة
    link = await bot.create_chat_invite_link(
        chat_id=CHANNEL_ID,
        member_limit=1
    )


    await message.answer(
        "✅ تم الدفع بنجاح\n\n"
        "رابط دخول القناة:\n"
        f"{link.invite_link}"
    )



async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
