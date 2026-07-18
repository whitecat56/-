import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from melody_ai.bot.handlers import music, start
from melody_ai.config.settings import get_settings
from melody_ai.core.logging import configure_logging


async def main() -> None:
    configure_logging()
    settings = get_settings()
    bot = Bot(
        settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(start.router)
    dp.include_router(music.router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
