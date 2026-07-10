# Dependencies

## Python

`requires-python = ">=3.13"` ([pyproject.toml](../../pyproject.toml)). `uv` manages the project's
virtualenv and lockfile (`uv.lock`) — there is no `Brewfile`, no `package.json`, no `mise`/`asdf` config
for the repo's *own* tooling. Don't confuse this with the version managers (`mise`, `asdf`) the harness
installs and exercises **inside the guest VM** as part of testing `zsh-dotfiles` — those are dependencies
of the system under test, not of this repo's own build or test tooling.

`[project.scripts]` registers the console entrypoint: `macos-ci = "macos_ci.cli:app"`.

### Runtime dependencies

From `pyproject.toml`'s `dependencies`, pinned in `uv.lock`:

| Package | Constraint | Locked version |
|---|---|---|
| [typer](https://pypi.org/project/typer/) | `>=0.15.0` | 0.26.8 |
| [rich](https://pypi.org/project/rich/) | `>=13.0.0` | 15.0.0 |

### Dev dependencies

From `pyproject.toml`'s `[dependency-groups].dev`, pinned in `uv.lock`:

| Package | Constraint | Locked version | Role |
|---|---|---|---|
| pytest | `>=8.0.0` | 9.1.1 | Test runner |
| pytest-cov | `>=6.0.0` | 7.1.0 | Coverage |
| pytest-sugar | `>=1.1.1` | 1.1.1 | Test-run output formatting |
| pytest-mock | `>=3.15.1` | 3.15.1 | Mocking fixtures |
| pytest-timeout | `>=2.4.0` | 2.4.0 | Per-test timeouts |
| pytest-retry | `>=1.7.0` | 1.7.0 | Retry flaky tests |
| pytest-subprocess | `>=1.5.3` | 1.6.0 | Fakes `tart`/`ssh` subprocess calls in `tests/unit/` |
| pytest-skip-slow | `>=0.0.5` | 1.1.0 | Marker-based slow-test skipping |
| pytest-testinfra | `>=10.2.1` | 10.2.2 | SSH-based host assertions for `tests/integration/` (`-m vm`) |
| asyncvnc | `>=1.3.0` | 1.3.0 | VNC client, used by `gui.py`/`_gui_core.py` and `tests/gui/` |
| pexpect | `>=4.9.0` | 4.9.0 | PTY automation over `ssh -tt`, used by `tests/pty/` |
| pytest-json-report | `>=1.5.0` | 1.5.0 | Machine-readable pytest output |
| ruff | `>=0.8.0` | 0.15.21 | Lint (`just lint`) and format (`just fmt`) |
| basedpyright | `>=1.29.1` | 1.39.9 | Static type checking (`just typecheck`) |

`uv.lock` records exact resolved versions for the full transitive dependency graph; the table above
gives only the direct dependencies this repo declares.

## External tools this repo assumes are on `PATH`

These are not Python packages and are not managed by `uv`. `macos-ci doctor`
([src/macos_ci/_doctor_core.py](../../src/macos_ci/_doctor_core.py)) checks for a subset of them
(`tart`, `packer`, `just`, `uv`, `cirrus`, `sshpass`) and gates the harness on their presence and, for
`tart`/`packer`, a minimum version (`tart>=2.0.0`, `packer>=1.10.0`).

| Tool | Why it's needed | Notes |
|---|---|---|
| **Tart** | Clones/runs/deletes the macOS guest VMs (`tart clone`/`run`/`ip`/`delete`/`stop`). | `brew install cirruslabs/cli/tart`. Fair Source licensed (`FSL-1.1-ALv2`), not open source, and actively enforced. This repo's accepted-risk posture (≤3 hosts, ≤100 combined CPU cores) is recorded in [specs/macos-ci/04-tart-licensing-risk.md](../../specs/macos-ci/04-tart-licensing-risk.md) and reported (never silently approved) by `macos-ci doctor`'s fleet-ceiling notice. |
| **Packer** | Builds the golden image from `packer/tart-golden-image.pkr.hcl`. | Requires the `cirruslabs/tart` Packer plugin (`packer { required_plugins { tart = { version = ">= 1.11.1", source = "github.com/cirruslabs/tart" } } }` in the template itself). See [docs/architecture/build-pipeline.md](build-pipeline.md). |
| **lychee** | Link-checks every `*.md` in the repo. | Invoked via `just link-check` / `just link-check-verbose` / `just link-check-fresh`, configured by `lychee.toml`. Not required for the build or test pipeline — a docs-quality gate only. |
| **gh** (GitHub CLI) | Optional. Supplies a `GITHUB_TOKEN` to lychee (avoids unauthenticated rate limiting) and can supply `HOMEBREW_GITHUB_API_TOKEN` to the Packer build via `gh auth token`. | Never required — every recipe that uses it falls back to an empty/unauthenticated value if `gh` is absent or unauthenticated. |
| **sshpass** | One-time password-authenticated SSH connection to seed the harness's SSH key into a freshly cloned VM (`harness.py`'s `_bootstrap_key_trust`), since the golden image only configures password auth. | Checked by `macos-ci doctor`, version read via `sshpass -V` (its `--version` flag doesn't exist). |
| **Cirrus CLI** (`cirrus`) | Runs `.cirrus.yml` locally for local/CI parity. | Invoked via `just ci` → `cirrus run`. Checked by `macos-ci doctor`. |
| **just** | The primary command runner for this repo — see [docs/architecture/justfile-reference.md](justfile-reference.md). | Checked by `macos-ci doctor`. |
| **zsh-dotfiles** | The external repo under test. Not vendored — the harness mounts its working tree read-only into the guest via `tart --dir`. | Path resolved from the `ZSH_DOTFILES` environment variable, or `--dotfiles`/`--dir` CLI flags, defaulting to a `../zsh-dotfiles` sibling directory. `macos-ci doctor` checks the resolved path exists. |

## CI

`.cirrus.yml` configures Cirrus CI to reproduce the apply-level pass/fail half of `just run`'s main loop
(clone `zsh-dotfiles` fresh, `chezmoi init --apply` under `retry`) inside Cirrus's own tart-backed
`macos_instance`, against the `dotfiles-golden` image built by `packer/tart-golden-image.pkr.hcl`. It
does **not** reproduce the full `pytest -m vm` testinfra pass, which SSHes from the host into the guest
and has no natural point to run mid-task inside Cirrus's tart backend — see the scope note at the top of
[.cirrus.yml](../../.cirrus.yml). `just ci` wraps `cirrus run` for local/CI parity.

## What is *not* a dependency of this repo

- **No Brewfile.** Homebrew packages are installed by the Packer provisioner *inside the guest*, not by
  anything the host runs to set up this repo.
- **No package.json, mise config, or asdf config for the repo's own tooling.** `mise` and `asdf` appear
  only as version managers the harness installs and exercises against `zsh-dotfiles`
  *inside the guest* (`macos-ci harness matrix`'s `mise`/`asdf` legs) — they are not used to manage this
  repo's own Python environment, which `uv` and `uv.lock` do exclusively.
- **No Terraform provider.** Neither Tart nor UTM has one; see
  [specs/macos-ci/10-tart-vs-utm-adr.md](../../specs/macos-ci/10-tart-vs-utm-adr.md).
