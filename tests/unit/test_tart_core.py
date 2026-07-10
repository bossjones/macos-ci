from macos_ci import tart
from macos_ci._tart_core import DirMount, clone_argv, delete_argv, ip_argv, run_argv


def test_clone_argv():
    assert clone_argv("ghcr.io/cirruslabs/macos-sequoia-vanilla:latest", "dotfiles-test") == [
        "tart",
        "clone",
        "ghcr.io/cirruslabs/macos-sequoia-vanilla:latest",
        "dotfiles-test",
    ]


def test_run_argv_headless_default():
    assert run_argv("dotfiles-test") == ["tart", "run", "dotfiles-test", "--no-graphics"]


def test_run_argv_with_dir_mount():
    argv = run_argv(
        "dotfiles-test",
        dirs=[DirMount(name="dotfiles", path="/Users/bossjones/dev/bossjones/zsh-dotfiles")],
    )
    assert argv == [
        "tart",
        "run",
        "dotfiles-test",
        "--no-graphics",
        "--dir=dotfiles:/Users/bossjones/dev/bossjones/zsh-dotfiles",
    ]


def test_run_argv_with_readonly_dir_mount():
    argv = run_argv(
        "dotfiles-test",
        dirs=[DirMount(name="dotfiles", path="/tmp/x", read_only=True)],
    )
    assert argv[-1] == "--dir=dotfiles:/tmp/x:ro"


def test_run_argv_vnc_experimental():
    argv = run_argv("dotfiles-test", headless=False, vnc_experimental=True)
    assert "--vnc-experimental" in argv
    assert "--no-graphics" not in argv


def test_ip_argv_default_resolver():
    assert ip_argv("dotfiles-test") == ["tart", "ip", "dotfiles-test", "--resolver", "dhcp"]


def test_ip_argv_agent_resolver():
    assert ip_argv("dotfiles-test", resolver="agent") == [
        "tart",
        "ip",
        "dotfiles-test",
        "--resolver",
        "agent",
    ]


def test_delete_argv():
    assert delete_argv("dotfiles-test") == ["tart", "delete", "dotfiles-test"]


def test_tart_clone_invokes_no_real_tart_binary(fake_process):
    fake_process.register(["tart", "clone", "golden", "dotfiles-test"], returncode=0)

    tart.clone("golden", "dotfiles-test")

    assert list(fake_process.calls)[-1] == ["tart", "clone", "golden", "dotfiles-test"]
