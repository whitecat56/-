from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.chat_action import ChatActionSender

from melody_ai.application.services.music_service import MusicService
from melody_ai.bot.keyboards.main import main_menu, song_actions
from melody_ai.bot.states.music import SearchStates
from melody_ai.config.settings import get_settings
from melody_ai.infrastructure.music.providers import AuddRecognitionProvider, DeezerProvider

router = Router()
settings = get_settings()
service = MusicService(
    DeezerProvider(settings.deezer_base_url),
    AuddRecognitionProvider(
        settings.audd_api_token.get_secret_value() if settings.audd_api_token else None
    ),
)


def render_song(song) -> str:
    return f"🎶 <b>{song.title}</b>\n👤 <b>Artist:</b> {song.artist}\n💿 <b>Album:</b> {song.album or '—'}\n🏷 <b>Genre:</b> {song.genre or '—'}\n📅 <b>Release:</b> {song.release_date or '—'}\n⏱ <b>Duration:</b> {song.duration_seconds or '—'} sec\n🔥 <b>Popularity:</b> {song.popularity or '—'}\n\n{('▶ Official preview available' if song.preview_url else 'ℹ️ Preview is unavailable from the official provider')}"


@router.callback_query(F.data == "search")
async def ask_search(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SearchStates.waiting_query)
    await callback.message.answer(
        "🔎 What should I search? Send song, artist, album, or lyrics snippet."
    )
    await callback.answer()


@router.message(F.text == "🎵 Search")
async def ask_search_text(message: Message, state: FSMContext):
    await state.set_state(SearchStates.waiting_query)
    await message.answer("🔎 Send your search query.")


@router.message(SearchStates.waiting_query)
async def do_search(message: Message, state: FSMContext):
    async with ChatActionSender.typing(bot=message.bot, chat_id=message.chat.id):
        songs = await service.search(message.text or "", 5)
    await state.clear()
    if not songs:
        await message.answer(
            "No official metadata results found. Try another query.", reply_markup=main_menu()
        )
        return
    for song in songs[:3]:
        if song.cover_url:
            await message.answer_photo(
                str(song.cover_url),
                caption=render_song(song),
                reply_markup=song_actions(song.provider_id, song.service_url),
            )
        else:
            await message.answer(
                render_song(song), reply_markup=song_actions(song.provider_id, song.service_url)
            )


@router.callback_query(F.data == "trending")
async def trending(callback: CallbackQuery):
    await callback.answer("Loading charts…")
    songs = await service.trending(limit=5)
    await callback.message.answer("🔥 <b>Global Top</b>")
    for i, s in enumerate(songs, 1):
        await callback.message.answer(
            f"{i}. {s.title} — {s.artist}", reply_markup=song_actions(s.provider_id, s.service_url)
        )


@router.callback_query(
    F.data.in_(
        {
            "favorites",
            "playlists",
            "recommendations",
            "history",
            "premium",
            "settings",
            "help",
            "recognize",
        }
    )
)
async def feature(callback: CallbackQuery):
    texts = {
        "favorites": "❤️ Favorites support add/remove/sort/search with pagination via API and repository layer.",
        "playlists": "📂 Create, rename, delete and share playlists. Use /api/v1/playlists for automation.",
        "recommendations": "🎧 Recommendations use favorites, history, genres and artists as seeds.",
        "history": "🕓 Search and opened-item history are stored securely.",
        "premium": "⭐ Premium: Telegram Stars monthly/yearly, unlimited playlists, priority search, advanced recommendations.",
        "settings": "⚙ Settings: language, notifications, theme and privacy.",
        "help": "❓ Search metadata and legal previews only. No unauthorized downloads.",
        "recognize": "🎤 Send a voice or audio sample. Recognition requires AUDD_API_TOKEN.",
    }
    await callback.message.answer(texts[callback.data], reply_markup=main_menu())
    await callback.answer()


@router.message(F.voice | F.audio)
async def recognize(message: Message):
    file = await message.bot.get_file((message.voice or message.audio).file_id)
    data = await message.bot.download_file(file.file_path)
    song = await service.recognize(data.read())
    await message.answer(
        render_song(song)
        if song
        else "I could not identify this sample with the configured provider."
    )
