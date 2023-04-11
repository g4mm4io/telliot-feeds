import click

from telliot_feeds.integrations.diva_protocol.cli import diva


@click.group()
def integrations() -> None:
    """Commands for Fetch Protocol integrations."""
    pass


integrations.add_command(diva)
