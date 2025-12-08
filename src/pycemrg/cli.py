# src/pycemrg/cli.py

import click
from pathlib import Path
from pycemrg.files import ConfigScaffolder  

@click.group()
def main():
    """A CLI for the pycemrg utility library."""
    pass

@main.command('init-models', help="Create a template models.yaml file.")
@click.option(
    '--output', '-o',
    default=Path('./models.yaml'),
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    help="Path to save the file."
)
@click.option('--force', is_flag=True, help="Overwrite the file if it exists.")
def init_models(output: Path, force: bool):
    """Generates a starter models.yaml file."""
    scaffolder = ConfigScaffolder()
    try:
        scaffolder.create_models_manifest(output_path=output, overwrite=force)
        click.secho(f"Successfully created template at: {output.resolve()}", fg="green")
    except FileExistsError as e:
        click.secho(str(e), fg="yellow")
        click.echo("Use the --force flag to overwrite.")
    except Exception as e:
        click.secho(f"An error occurred: {e}", fg="red")

@main.command('init-labels', help="Create a template labels.yaml file.")
@click.option(
    '--output', '-o',
    default=Path('./labels.yaml'),
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    help="Path to save the file."
)
@click.option('--force', is_flag=True, help="Overwrite the file if it exists.")
def init_labels(output: Path, force: bool):
    """Generates a starter labels.yaml file."""
    scaffolder = ConfigScaffolder()
    try:
        scaffolder.create_labels_manifest(output_path=output, overwrite=force)
        click.secho(f"Successfully created template at: {output.resolve()}", fg="green")
    except FileExistsError as e:
        click.secho(str(e), fg="yellow")
        click.echo("Use the --force flag to overwrite.")
    except Exception as e:
        click.secho(f"An error occurred: {e}", fg="red")


if __name__ == '__main__':
    main()