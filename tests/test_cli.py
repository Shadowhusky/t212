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
