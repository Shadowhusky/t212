from __future__ import annotations
import asyncio
import click
from t212.api.limits import RATE_LIMITS
from t212.api.mock import MockT212Client
from t212.summary import build_summary, render_summary_text


def _make_client(mock: bool, fixtures: str | None, environment: str, api_key: str | None):
    if mock:
        return MockT212Client(fixtures)
    from t212.api.http import HttpT212Client
    from t212.api.ratelimit import RateLimitGovernor
    from t212.config import resolve_settings
    settings = resolve_settings(environment=environment, api_key=api_key)
    gov = RateLimitGovernor(RATE_LIMITS)
    return HttpT212Client(api_key=settings.api_key, base_url=settings.base_url, governor=gov)


async def _run_once(client):
    summary = await build_summary(client)
    text = render_summary_text(summary)
    await client.aclose()
    return text


@click.group(invoke_without_command=True)
@click.option("--demo", "environment", flag_value="demo", help="Use the demo/practice account.")
@click.option("--live", "environment", flag_value="live", default=True, help="Use the live account (default).")
@click.option("--mock", is_flag=True, help="Use bundled fixtures (offline).")
@click.option("--fixtures", default=None, help="Fixtures dir for --mock.")
@click.option("--once", "once", is_flag=True, help="Print a text summary and exit.")
@click.option("--refresh", default=None, type=int, help="Portfolio poll seconds (TUI).")
@click.option("--api-key", default=None, help="Override API key.")
@click.pass_context
def main(ctx, environment, mock, fixtures, once, refresh, api_key):
    """Read-only Trading 212 portfolio terminal."""
    if ctx.invoked_subcommand is not None:
        return
    if once:
        from t212.config import MissingKeyError
        try:
            client = _make_client(mock, fixtures, environment, api_key)
        except MissingKeyError:
            click.echo("No Trading 212 API key configured.")
            click.echo("Get one in the Trading 212 app: Settings → API (Beta) → Generate key.")
            click.echo("Then run `t212 config set-key`, or just `t212` for guided setup.")
            raise SystemExit(1)
        click.echo(asyncio.run(_run_once(client)))
        return
    from t212.app import run_app
    run_app(environment=environment, mock=mock, fixtures=fixtures,
            refresh=refresh, api_key=api_key)


@main.command("config")
@click.argument("action", type=click.Choice(["set-key"]))
@click.option("--demo", "environment", flag_value="demo", help="Save the demo-account key.")
@click.option("--live", "environment", flag_value="live", default=True, help="Save the live-account key (default).")
def config_cmd(action, environment):
    """Manage saved credentials. Currently: set-key."""
    key_id = click.prompt(f"Trading 212 API key ID ({environment})", hide_input=True)
    secret = click.prompt("Trading 212 API key secret", hide_input=True)
    from t212.config import save_key, DEFAULT_CONFIG_PATH
    save_key(DEFAULT_CONFIG_PATH, environment, f"{key_id}:{secret}")
    click.echo(f"Saved {environment} key to {DEFAULT_CONFIG_PATH} (chmod 600).")
