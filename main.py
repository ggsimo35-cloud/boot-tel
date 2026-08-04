import asyncio
import logging
import os
import sqlite3
from contextlib import closing

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery


BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
CHANNEL_ID_RAW = os.getenv("CHANNEL_ID", "-1004424805545").strip()
PRICE = 50
PAYLOAD = "one_time_channel_access"

if not BOT_TOKEN:
    raise RuntimeError("8882282653:AAGieiKuEadfsfE88baF4dYZrfBUSyjqiCQ")

try:
    CHANNEL_ID = int(CHANNEL_ID_RAW)
except ValueError as exc:
    raise RuntimeError("-1004424805545") from exc


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


TEXTS = {
    "ar": {
        "subscribe": "اشترك للوصول إلى القناة الخاصة:",
        "pay": "⭐ دفع 50 Stars",
        "already_paid": "✅ أنت مشترك بالفعل.",
        "payment_title": "اشتراك القناة",
        "payment_description": "دخول دائم إلى القناة الخاصة",
        "payment_label": "اشتراك",
        "payment_success": (
            "✅ تم الدفع بنجاح\n\n"
            "هذا رابط دخول القناة الخاص بك:\n{link}\n\n"
            "⚠️ الرابط مخصص للاستخدام مرة واحدة."
        ),
        "payment_error": (
            "تم الدفع، لكن تعذر إنشاء رابط القناة.\n"
            "تواصل مع إدارة البوت."
        ),
        "language_saved": "✅ تم اختيار العربية.",
    },
    "en": {
        "subscribe": "Subscribe to access the private channel:",
        "pay": "⭐ Pay 50 Stars",
        "already_paid": "✅ You are already subscribed.",
        "payment_title": "Channel subscription",
        "payment_description": "Permanent access to the private channel",
        "payment_label": "Subscription",
        "payment_success": (
            "✅ Payment successful\n\n"
            "Here is your private channel invite link:\n{link}\n\n"
            "⚠️ This link can be used only once."
        ),
        "payment_error": (
            "Payment was completed, but the channel link could not be created.\n"
            "Please contact the bot administrator."
        ),
        "language_saved": "✅ English selected.",
    },
    "ru": {
        "subscribe": "Оформите подписку для доступа к приватному каналу:",
        "pay": "⭐ Оплатить 50 Stars",
        "already_paid": "✅ Вы уже подписаны.",
        "payment_title": "Подписка на канал",
        "payment_description": "Постоянный доступ к приватному каналу",
        "payment_label": "Подписка",
        "payment_success": (
            "✅ Оплата прошла успешно\n\n"
            "Ваша приватная ссылка для входа в канал:\n{link}\n\n"
            "⚠️ Ссылка предназначена только для одного использования."
        ),
        "payment_error": (
            "Оплата прошла, но создать ссылку на канал не удалось.\n"
            "Свяжитесь с администратором бота."
        ),
        "language_saved": "✅ Выбран русский язык.",
    },
}


DB_PATH = "users.db"


def initialize_database() -> None:
    with closing(sqlite3.connect(DB_PATH)) as db:
        cursor = db.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                lang TEXT NOT NULL DEFAULT 'ar',
                paid INTEGER NOT NULL DEFAULT 0
            )
            """
        )

        cursor.execute("PRAGMA table_info(users)")
        columns = {row[1] for row in cursor.fetchall()}

        if "lang" not in columns:
            cursor.execute(
                "ALTER TABLE users ADD COLUMN lang TEXT NOT NULL DEFAULT 'ar'"
            )

        if "paid" not in columns:
            cursor.execute(
                "ALTER TABLE users ADD COLUMN paid INTEGER NOT NULL DEFAULT 0"
            )

        db.commit()


def get_user(user_id: int):
    with closing(sqlite3.connect(DB_PATH)) as db:
        cursor = db.cursor()
        cursor.execute(
            "SELECT lang, paid FROM users WHERE user_id = ?",
            (user_id,),
        )
        return cursor.fetchone()


def save_language(user_id: int, lang: str) -> None:
    with closing(sqlite3.connect(DB_PATH)) as db:
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO users (user_id, lang, paid)
            VALUES (?, ?, 0)
            ON CONFLICT(user_id) DO UPDATE SET lang = excluded.lang
            """,
            (user_id, lang),
        )
        db.commit()


def mark_as_paid(user_id: int, lang: str) -> None:
    with closing(sqlite3.connect(DB_PATH)) as db:
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO users (user_id, lang, paid)
            VALUES (?, ?, 1)
            ON CONFLICT(user_id) DO UPDATE SET
                lang = excluded.lang,
                paid = 1
            """,
            (user_id, lang),
        )
        db.commit()


initialize_database()


def language_keyboard() -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="🇩🇿 العربية",
                    callback_data="lang_ar",
                )
            ],
            [
                types.InlineKeyboardButton(
                    text="🇬🇧 English",
                    callback_data="lang_en",
                )
            ],
            [
                types.InlineKeyboardButton(
                    text="🇷🇺 Русский",
                    callback_data="lang_ru",
                )
            ],
        ]
    )


def payment_keyboard(lang: str) -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=TEXTS[lang]["pay"],
                    callback_data="pay",
                )
            ]
        ]
    )


@dp.message(Command("start"))
async def start(message: types.Message) -> None:
    user_id = message.from_user.id
    user = get_user(user_id)

    if user and user[1] == 1:
        lang = user[0] if user[0] in TEXTS else "ar"
        await message.answer(TEXTS[lang]["already_paid"])
        return

    await message.answer(
        "اختر لغتك\nChoose your language\nВыберите язык",
        reply_markup=language_keyboard(),
    )


@dp.callback_query(F.data.startswith("lang_"))
async def choose_language(callback: types.CallbackQuery) -> None:
    lang = callback.data.replace("lang_", "", 1)

    if lang not in TEXTS:
        await callback.answer("Unsupported language", show_alert=True)
        return

    save_language(callback.from_user.id, lang)
    await callback.answer(TEXTS[lang]["language_saved"])

    await callback.message.edit_text(
        TEXTS[lang]["subscribe"],
        reply_markup=payment_keyboard(lang),
    )


@dp.callback_query(F.data == "pay")
async def pay(callback: types.CallbackQuery) -> None:
    user_id = callback.from_user.id
    user = get_user(user_id)

    lang = user[0] if user and user[0] in TEXTS else "ar"
    paid = user[1] if user else 0

    if paid == 1:
        await callback.answer(
            TEXTS[lang]["already_paid"],
            show_alert=True,
        )
        return

    await callback.answer()

    await bot.send_invoice(
        chat_id=user_id,
        title=TEXTS[lang]["payment_title"],
        description=TEXTS[lang]["payment_description"],
        payload=PAYLOAD,
        provider_token="",
        currency="XTR",
        prices=[
            LabeledPrice(
                label=TEXTS[lang]["payment_label"],
                amount=PRICE,
            )
        ],
    )


@dp.pre_checkout_query()
async def checkout(query: PreCheckoutQuery) -> None:
    if query.invoice_payload != PAYLOAD:
        await bot.answer_pre_checkout_query(
            query.id,
            ok=False,
            error_message="Invalid payment payload.",
        )
        return

    await bot.answer_pre_checkout_query(query.id, ok=True)


@dp.message(F.successful_payment)
async def successful_payment(message: types.Message) -> None:
    payment = message.successful_payment

    if (
        payment.invoice_payload != PAYLOAD
        or payment.currency != "XTR"
        or payment.total_amount != PRICE
    ):
        logging.warning(
            "Unexpected payment: user=%s payload=%s currency=%s amount=%s",
            message.from_user.id,
            payment.invoice_payload,
            payment.currency,
            payment.total_amount,
        )
        return

    user_id = message.from_user.id
    user = get_user(user_id)
    lang = user[0] if user and user[0] in TEXTS else "ar"

    mark_as_paid(user_id, lang)

    try:
        invite = await bot.create_chat_invite_link(
            chat_id=CHANNEL_ID,
            member_limit=1,
            name=f"Paid user {user_id}",
        )

        await message.answer(
            TEXTS[lang]["payment_success"].format(
                link=invite.invite_link
            )
        )

    except Exception:
        logging.exception(
            "Failed to create invite link for user %s",
            user_id,
        )
        await message.answer(TEXTS[lang]["payment_error"])


async def main() -> None:
    logging.info("Bot is starting...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
