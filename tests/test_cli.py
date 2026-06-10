import pathlib
from click.testing import CliRunner
from t212.cli import main

FIX = pathlib.Path(__file__).parent / "fixtures"

def test_once_mock_prints_summary():
    runner = CliRunner()
    result = runner.invoke(main, ["--once", "--mock", "--fixtures", str(FIX)])
    assert result.exit_code == 0, result.output
    assert "£24,813.07" in result.output
    assert "VUSA" in result.output

def test_help_lists_flags():
    result = CliRunner().invoke(main, ["--help"])
    assert "--demo" in result.output and "--once" in result.output and "--mock" in result.output


def test_config_set_key(tmp_path, monkeypatch):
    import t212.cli as cli
    import t212.config as config
    monkeypatch.setattr(config, "DEFAULT_CONFIG_PATH", tmp_path / "config.toml")
    result = CliRunner().invoke(cli.main, ["config", "set-key", "--demo"], input="MYID\nMYSECRET\n")
    assert result.exit_code == 0, result.output
    assert "Saved demo key" in result.output
    data = (tmp_path / "config.toml").read_text()
    assert "MYID:MYSECRET" in data
