# Architecture

Reference documentation for how `macos-ci` is actually built — what each part of the repo is, how the
golden-image build and per-test harness lifecycle work, what this repo depends on, and the full command
surface (`macos-ci` CLI and `just` recipes). These pages describe the checked-in code as it exists today;
for *why* the design looks this way, see [../../specs/](../../specs/) — the specs are authoritative on
rationale, these pages are authoritative on current shape.

| Doc | What it covers |
|---|---|
| [repo-structure.md](repo-structure.md) | The top-level directory map, the `macos_ci` package's pure/impure module split, and the pytest marker-based test layout. Includes a diagram of how the major directories relate. |
| [build-pipeline.md](build-pipeline.md) | The full pipeline: the one-time golden-image Packer build, the `verify-no-secrets` leak-canary, and the repeatable per-test harness lifecycle (`doctor` → `up` → `apply` → `verify` → `destroy`). Includes a diagram and flags the not-yet-implemented `images-cache` recipe. |
| [dependencies.md](dependencies.md) | Python dependencies (via `uv`/`pyproject.toml`) and external tooling this repo assumes (Tart, Packer, lychee, `gh`, `zsh-dotfiles`, Cirrus CI). |
| [cli-reference.md](cli-reference.md) | Every `macos-ci` CLI command (`doctor`, and the `harness`/`gui`/`vm-debug` sub-apps), generated from `src/macos_ci/cli.py` and its sub-app modules. |
| [justfile-reference.md](justfile-reference.md) | Every `just` recipe (~48), grouped by purpose, plus the Justfile's override variables and env vars. |

Both `cli-reference.md` and `justfile-reference.md` flag a handful of real discrepancies found between
the Justfile and the current CLI implementation (e.g. `just vnc`/`just shot` calling unimplemented or
stubbed commands) — read the "Justfile Integration Notes" / cross-reference sections in each rather than
assuming every recipe listed in the Justfile currently works end to end.

See also: [../tutorials/](../tutorials/) for task-oriented walkthroughs, and [../contributor/](../contributor/) for how this repo's own build was orchestrated.
