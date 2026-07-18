from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from melody_ai.bot.keyboards.main import main_menu, persistent_menu

router = Router()
WELCOME = """🎵 <b>Melody AI</b>\n\n<i>The smart music assistant.</i>\n\n✨ Discover songs.\n🎙 Find artists.\n❤️ Save favorites.\n🎧 Receive recommendations.\n\n<b>MAIN MENU</b>"""


@router.message(CommandStart())
async def start(message: Message):
    await message.answer(WELCOME, reply_markup=main_menu())
    await message.answer("Choose an action below 👇", reply_markup=persistent_menu())


@router.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer(
        "Send a song title, artist, album, or lyrics snippet. Voice/audio recognition works when AUDD_API_TOKEN is configured.",
        reply_markup=main_menu(),
    )


@router.callback_query(lambda c: c.data == "back:menu")
async def back(callback: CallbackQuery):
    await callback.message.edit_text(WELCOME, reply_markup=main_menu())
    await callback.answer()
