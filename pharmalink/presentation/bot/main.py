from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from redis.asyncio import Redis

from pharmalink.config.settings import get_settings

router = Router()


def main_menu():
    rows = [
        [
            InlineKeyboardButton(text="💊 Search Medicine", callback_data="search"),
            InlineKeyboardButton(text="📂 Categories", callback_data="categories"),
        ],
        [
            InlineKeyboardButton(text="❤️ Favorites", callback_data="favorites"),
            InlineKeyboardButton(text="🛒 Cart", callback_data="cart"),
        ],
        [
            InlineKeyboardButton(text="📦 Orders", callback_data="orders"),
            InlineKeyboardButton(text="📍 Pharmacies", callback_data="pharmacies"),
        ],
        [
            InlineKeyboardButton(text="👤 Profile", callback_data="profile"),
            InlineKeyboardButton(text="☎ Support", callback_data="support"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "Welcome to PharmaLink — find, reserve, and order medicines.", reply_markup=main_menu()
    )


@router.callback_query(F.data == "search")
async def search_prompt(call: CallbackQuery):
    await call.message.answer("Send a medicine name, barcode, manufacturer, or active ingredient.")
    await call.answer()


@router.message(F.text)
async def text_search(message: Message):
    await message.answer(
        f"🔎 Searching for: {message.text}\nUse the API-backed repository in production deployment."
    )


async def run_bot():
    s = get_settings()
    bot = Bot(s.bot_token)
    dp = Dispatcher(storage=RedisStorage(Redis.from_url(s.redis_url)))
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(run_bot())
