from pharmalink.presentation.bot.main import main_menu


def test_main_menu_contains_search():
    markup = main_menu()
    assert markup.inline_keyboard[0][0].text.startswith("💊")
