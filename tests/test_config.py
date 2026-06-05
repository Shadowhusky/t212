import os, stat, pytest
from t212.config import resolve_settings, save_key, MissingKeyError

def test_flag_beats_env(monkeypatch, tmp_path):
    monkeypatch.setenv("TRADING212_API_KEY", "from_env")
    s = resolve_settings(environment="live", api_key="from_flag", config_path=tmp_path / "c.toml")
    assert s.api_key == "from_flag" and s.environment == "live"
    assert s.base_url.startswith("https://live.")

def test_env_beats_file(monkeypatch, tmp_path):
    monkeypatch.setenv("TRADING212_API_KEY", "from_env")
    s = resolve_settings(environment="demo", config_path=tmp_path / "c.toml")
    assert s.api_key == "from_env" and s.base_url.startswith("https://demo.")

def test_file_used_when_no_flag_or_env(monkeypatch, tmp_path):
    monkeypatch.delenv("TRADING212_API_KEY", raising=False)
    path = tmp_path / "c.toml"
    save_key(path, "live", "from_file")
    s = resolve_settings(environment="live", config_path=path)
    assert s.api_key == "from_file"

def test_missing_raises(monkeypatch, tmp_path):
    monkeypatch.delenv("TRADING212_API_KEY", raising=False)
    with pytest.raises(MissingKeyError):
        resolve_settings(environment="live", config_path=tmp_path / "nope.toml")

def test_saved_file_is_chmod_600(monkeypatch, tmp_path):
    path = tmp_path / "c.toml"
    save_key(path, "demo", "secret")
    mode = stat.S_IMODE(path.stat().st_mode)
    assert mode == 0o600
