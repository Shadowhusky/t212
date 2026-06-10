import pathlib
from textual.widgets import Input
from t212.api.base import AuthError
from t212.api.mock import MockT212Client
from t212.app import T212App
from t212.models import AccountSummary
from t212.screens.setup import SetupScreen
import t212.config as config
import t212.store

FIX = pathlib.Path(__file__).parent / "fixtures"


def make_unconfigured_app():
    return T212App(client=None, environment="live", currency="")


async def test_no_client_opens_setup_screen():
    app = make_unconfigured_app()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert isinstance(app.screen, SetupScreen)
        tips = app.screen.query_one("#setup-tips").visual.plain
        assert "Settings → API" in tips
        assert "read-only" in tips


async def test_validate_saves_key_and_starts_app(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DEFAULT_CONFIG_PATH", tmp_path / "config.toml")
    monkeypatch.setattr(t212.store, "default_db_path",
                        lambda env, acc: tmp_path / f"{env}-{acc}.sqlite")
    summary = AccountSummary(id=77, currency="EUR")

    class EuroMock(MockT212Client):
        async def summary(self):
            return summary

    async def fake_validator(api_key, environment):
        assert api_key == "MYID:MYSECRET"
        assert environment == "live"
        app._pending_client = EuroMock(FIX)
        return summary

    app = make_unconfigured_app()
    async with app.run_test() as pilot:
        await pilot.pause()
        screen = app.screen
        screen._validator = fake_validator
        screen.query_one("#setup-key-id", Input).value = "MYID"
        screen.query_one("#setup-secret", Input).value = "MYSECRET"
        await screen._submit()
        await pilot.pause()
        assert not isinstance(app.screen, SetupScreen)
        assert "MYID:MYSECRET" in (tmp_path / "config.toml").read_text()
        assert app.currency == "EUR"
        assert app.environment == "live"
        assert app.scheduler is not None
        db_file = app.store.db.execute("PRAGMA database_list").fetchone()[2]
        assert "live-77" in db_file
        await app.workers.wait_for_complete()
        assert app._summary is not None


async def test_rejected_key_keeps_screen_open():
    async def fake_validator(api_key, environment):
        raise AuthError("unauthorized")

    app = make_unconfigured_app()
    async with app.run_test() as pilot:
        await pilot.pause()
        screen = app.screen
        screen._validator = fake_validator
        screen.query_one("#setup-key-id", Input).value = "BADID"
        screen.query_one("#setup-secret", Input).value = "BADSECRET"
        await screen._submit()
        await pilot.pause()
        assert isinstance(app.screen, SetupScreen)
        assert "rejected" in screen.query_one("#setup-status").visual.plain


async def test_blank_fields_show_error():
    app = make_unconfigured_app()
    async with app.run_test() as pilot:
        await pilot.pause()
        screen = app.screen
        await screen._submit()
        assert "enter both" in screen.query_one("#setup-status").visual.plain
        assert isinstance(app.screen, SetupScreen)


async def test_browse_sample_data_runs_on_mock():
    app = make_unconfigured_app()
    async with app.run_test(size=(100, 40)) as pilot:
        await pilot.pause()
        await pilot.click("#setup-mock")
        await pilot.pause()
        assert not isinstance(app.screen, SetupScreen)
        assert app.scheduler is not None
        await app.workers.wait_for_complete()
        assert app._summary is not None


async def test_persist_swaps_default_store_to_disk(tmp_path, monkeypatch):
    monkeypatch.setattr(t212.store, "default_db_path",
                        lambda env, acc: tmp_path / f"{env}-{acc}.sqlite")
    app = T212App(client=MockT212Client(FIX), environment="live", currency="GBP",
                  persist=True)
    async with app.run_test():
        await app.workers.wait_for_complete()
        db_file = app.store.db.execute("PRAGMA database_list").fetchone()[2]
        assert "live-1234567" in db_file
        assert app.store.equity_series()


async def test_escape_does_not_dismiss_required_setup():
    app = make_unconfigured_app()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.screen.query_one("#setup-validate").focus()
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, SetupScreen)
        assert "q quits" in app.screen.query_one("#setup-status").visual.plain
