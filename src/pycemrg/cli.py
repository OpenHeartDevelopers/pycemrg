# src/pycemrg/cli.py

import click
from pathlib import Path
from pycemrg.files import ConfigScaffolder, ProjectScaffolder
from pycemrg.files.project import InvalidProjectNameError

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
@click.option(
    '--num-labels',
    default=3,
    type=click.IntRange(min=0),
    help="Number of placeholder labels to generate.",
    show_default=True
)
@click.option(
    '--num-groups',
    default=1,
    type=click.IntRange(min=0),
    help="Number of placeholder groups to generate.",
    show_default=True
)
def init_labels(output: Path, force: bool, num_labels: int, num_groups: int):
    """Generates a starter labels.yaml file."""
    scaffolder = ConfigScaffolder()
    try:
        scaffolder.create_labels_manifest(
            output_path=output,
            overwrite=force,
            num_labels=num_labels,
            num_groups=num_groups
        )
        click.secho(f"Successfully created template at: {output.resolve()}", fg="green")
    except FileExistsError as e:
        click.secho(str(e), fg="yellow")
        click.echo("Use the --force flag to overwrite.")
    except Exception as e:
        click.secho(f"An error occurred: {e}", fg="red")

@main.command('init', help="Scaffold a new project that consumes the pycemrg suite.")
@click.argument('name')
@click.option(
    '--path', '-p',
    default=Path('.'),
    type=click.Path(file_okay=False, writable=True, path_type=Path),
    help="Parent directory in which to create the project folder."
)
@click.option(
    '--with-src',
    is_flag=True,
    help="Also create src/<name>/ for stateless library code."
)
@click.option(
    '--force',
    is_flag=True,
    help="Write into the project directory even if it already exists and is non-empty."
)
def init_project(name: str, path: Path, with_src: bool, force: bool):
    """Generate a starter project skeleton for the pycemrg suite."""
    scaffolder = ProjectScaffolder()
    try:
        project_root = scaffolder.create_project(
            name=name,
            parent_dir=path,
            with_src=with_src,
            force=force,
        )
    except InvalidProjectNameError as e:
        click.secho(str(e), fg="red")
        raise click.exceptions.Exit(code=2)
    except FileExistsError as e:
        click.secho(str(e), fg="yellow")
        click.echo("Use --force to write into it anyway.")
        raise click.exceptions.Exit(code=1)
    
    project_env_name = project_root.name.replace('-', '_')

    click.secho(f"Created project at: {project_root}", fg="green")
    click.echo("Next steps:")
    click.echo(f"  cd {project_root}")
    click.echo(f"  conda create --name {project_env_name} python=3.10 && conda activate {project_env_name}")
    click.echo("  pip install -e .\n")
    click.echo("Optional steps:")
    click.echo("  pycemrg init-labels -o config/labels.yaml")
    click.echo("  pycemrg init-models -o config/models.yaml")
    click.echo("  python scripts/example_run.py")


if __name__ == '__main__':
    main()