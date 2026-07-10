"""Impure shell: `tart clone` -> headless `tart run` -> SSH apply -> `tart delete` (owned by 🛠 harness-builder after handoff)."""

import typer

app = typer.Typer(help="Run the dotfiles-test harness against a Tart VM.")


@app.command()
def up() -> None:
    raise NotImplementedError("harness.up: implemented by harness-builder post-handoff")


@app.command()
def run() -> None:
    raise NotImplementedError("harness.run: implemented by harness-builder post-handoff")


@app.command()
def destroy() -> None:
    raise NotImplementedError("harness.destroy: implemented by harness-builder post-handoff")
