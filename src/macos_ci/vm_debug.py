"""Impure shell: sweeps guest log sources over SSH and matches `_triage_core` signatures (owned by 🛠 harness-builder after handoff)."""

import typer

app = typer.Typer(help="Triage a Tart VM's log sources for known failure signatures.")


@app.command()
def sweep() -> None:
    raise NotImplementedError("vm_debug.sweep: implemented by harness-builder post-handoff")
