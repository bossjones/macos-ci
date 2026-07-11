"""`macos-ci` console-script entrypoint. Mounts every subcommand group as a sub-app."""

import typer

from macos_ci import doctor, gui, harness, utm, vm_debug

app: typer.Typer = typer.Typer(help="Local, disposable macOS CI harness on top of Tart.")

app.add_typer(harness.app, name="harness")
app.add_typer(gui.app, name="gui")
app.add_typer(vm_debug.app, name="vm-debug")
app.add_typer(utm.app, name="utm")


@app.command("doctor")
def doctor_command(
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    """Preflight every requirement. Exit 2 if anything is missing."""
    raise typer.Exit(code=doctor.run(json_output=json_output))


if __name__ == "__main__":
    app()
