from melody_ai.api.app import create_app


def test_app_metadata():
    app = create_app()
    assert app.title == "MELODY AI API"
