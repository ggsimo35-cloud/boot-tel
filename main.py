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


# Create database
db = sqlite3.connect("users.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY
)
""")

db.commit()


# ---------------------------------------------------------------------------
# Translations
# ---------------------------------------------------------------------------

TRANSLATIONS = {
    "en": {
        "already_subscribed": "✅ You are already subscribed.",
        "subscribe_prompt": "Subscribe to access the private channel:",
        "pay_button": "⭐ Pay 50 Stars",
        "invoice_title": "Channel Subscription",
        "invoice_description": "Permanent access to the private channel",
        "payment_success": "✅ Payment successful!\n\nYour private channel invite link:\n{link}",
        "label": "Subscription",
    },
    "ru": {
        "already_subscribed": "✅ Вы уже подписаны.",
        "subscribe_prompt": "Оформите подписку, чтобы получить доступ к закрытому каналу:",
        "pay_button": "⭐ Оплатить 50 Stars",
        "invoice_title": "Подписка на канал",
        "invoice_description": "Постоянный доступ к закрытому каналу",
        "payment_success": "✅ Оплата прошла успешно!\n\nВаша ссылка-приглашение в закрытый канал:\n{link}",
        "label": "Подписка",
    },
    "ar": {
        "already_subscribed": "✅ أنت مشترك بالفعل.",
        "subscribe_prompt": "اشترك للوصول إلى القناة الخاصة:",
        "pay_button": "⭐ ادفع 50 نجمة",
        "invoice_title": "اشتراك القناة",
        "invoice_description": "وصول دائم إلى القناة الخاصة",
        "payment_success": "✅ تم الدفع بنجاح!\n\nرابط الدعوة الخاص بك للقناة:\n{link}",
        "label": "اشتراك",
    },
}

DEFAULT_LANG = "en"


def get_lang(user: types.User) -> str:
    """Return a supported language code based on the Telegram user's client language."""
    code = (user.language_code or "").split("-")[0].lower()
    if code in TRANSLATIONS:
        return code
    return DEFAULT_LANG


def t(lang: str, key: str, **kwargs) -> str:
    text = TRANSLATIONS.get(lang, TRANSLATIONS[DEFAULT_LANG])[key]
    return text.format(**kwargs) if kwargs else text


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

@dp.message(Command("start"))
async def start(message: types.Message):

    user_id = message.from_user.id
    lang = get_lang(message.from_user)

    cursor.execute(
        "SELECT user_id FROM users WHERE user_id=?",
        (user_id,)
    )

    if cursor.fetchone():
        await message.answer(t(lang, "already_subscribed"))
        return

    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=t(lang, "pay_button"),
                    callback_data="pay"
                )
            ]
        ]
    )

    await message.answer(
        t(lang, "subscribe_prompt"),
        reply_markup=keyboard
    )


@dp.callback_query(lambda c: c.data == "pay")
async def pay(callback: types.CallbackQuery):

    lang = get_lang(callback.from_user)

    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title=t(lang, "invoice_title"),
        description=t(lang, "invoice_description"),
        payload="one_time_channel_access",
        provider_token="",
        currency="XTR",
        prices=[
            LabeledPrice(
                label=t(lang, "label"),
                amount=PRICE
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
    lang = get_lang(message.from_user)

    # Save subscriber
    cursor.execute(
        "INSERT OR IGNORE INTO users VALUES (?)",
        (user_id,)
    )

    db.commit()

    # Create one-time invite link
    link = await bot.create_chat_invite_link(
        chat_id=CHANNEL_ID,
        member_limit=1
    )

    await message.answer(
        t(lang, "payment_success", link=link.invite_link)
    )


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
