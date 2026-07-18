from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def main_menu() -> InlineKeyboardMarkup:
    rows = [
        [("🎵 Search", "search"), ("❤️ Favorites", "favorites")],
        [("📂 Playlists", "playlists"), ("🔥 Trending", "trending")],
        [("🎧 Recommendations", "recommendations"), ("🎤 Recognize Song", "recognize")],
        [("🕓 History", "history"), ("⭐ Premium", "premium")],
        [("⚙ Settings", "settings"), ("❓ Help", "help")],
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t, callback_data=c) for t, c in r] for r in rows
        ]
    )


def persistent_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎵 Search"), KeyboardButton(text="❤️ Favorites")],
            [KeyboardButton(text="🔥 Trending"), KeyboardButton(text="⚙ Settings")],
        ],
        resize_keyboard=True,
    )


def song_actions(provider_id: str, service_url: str | None) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="▶ Preview", callback_data=f"preview:{provider_id}"),
            InlineKeyboardButton(text="❤️ Favorite", callback_data=f"fav:{provider_id}"),
        ],
        [
            InlineKeyboardButton(text="➕ Playlist", callback_data=f"pladd:{provider_id}"),
            InlineKeyboardButton(text="📤 Share", switch_inline_query=provider_id),
        ],
        [InlineKeyboardButton(text="⬅ Back", callback_data="back:menu")],
    ]
    if service_url:
        buttons.insert(2, [InlineKeyboardButton(text="🔗 Open in Music Service", url=service_url)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
