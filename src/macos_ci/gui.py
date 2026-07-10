"""Impure shell: VNC connect / screenshot / keystrokes via `_gui_core.parse_vnc_url` + asyncvnc (stays with 🐍 core-builder)."""

import typer

app = typer.Typer(help="Drive a Tart VM's VNC framebuffer for screenshots and keystrokes.")


@app.command()
def shot(label: str) -> None:
    raise NotImplementedError("gui.shot: not yet implemented")
