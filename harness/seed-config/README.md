# seed-config

Pre-seeded `chezmoi.yaml` fixtures for the toggle-matrix lever (spec
[08-dotfiles-test-harness.md §(b), Option A](../../specs/macos-ci/08-dotfiles-test-harness.md#the-one-real-limitation-the-boolean-toggles-are-unreachable-non-tty)).

## Why this exists

`ruby`/`pyenv`/`nodejs`/`k8s`/`cuda`/`fnm`/`opencv` all sit inside `.chezmoi.yaml.tmpl`'s
`{{- if $interactive -}}` guard, and `$interactive` is `stdinIsATTY` — which the harness's non-TTY
`ssh` apply (G11) always makes `false`. There is no `--promptBool` lever for a non-TTY run: the
`promptBool` calls that would read it never execute. The **only** way to reach those seven fields in a
harness run is to pre-seed a chezmoi config file whose `data:` block already sets them, written into the
guest at `~/.config/chezmoi/chezmoi.yaml` **before** `chezmoi init` runs. Every prompt in the template
checks `hasKey . "<field>"` first and short-circuits straight to the pre-seeded value — this path is
identical whether the session is interactive or not, because it never reaches the `promptBool` call at
all.

`version_manager` is **not** one of these fields — it sits outside the `$interactive` guard on purpose
and is reachable directly via `chezmoi init --promptString version_manager=mise|asdf` (see
`harness.py`'s `chezmoi_argv()`, parameterized by `--version-manager`/`MACOS_CI_VERSION_MANAGER`). Do not
duplicate it in a seed-config fixture; it does not need one.

## Field reference (spec 09 §"Non-TTY default state")

| Field | Non-seeded (lean baseline) default |
|---|---|
| `ruby` | `false` |
| `pyenv` | `false` |
| `nodejs` | `false` |
| `k8s` | `false` |
| `cuda` | `false` |
| `fnm` | `false` |
| `opencv` | `false` |

## Fixtures

- `lean-baseline.yaml` — all seven fields explicit `false`. Behaviourally identical to *no* seed file at
  all (that's what a non-TTY run already defaults to per spec 09) — this fixture exists so a
  toggle-matrix test can assert against an explicit, named baseline rather than "absence of a file",
  and so the matrix has one row that pins the default rather than leaving it implicit.
- `all-features.yaml` — all seven fields explicit `true`. The opposite corner of the matrix: exercises
  every optional install path (Ruby via asdf, pyenv-managed Python, Node.js, Kubernetes CLIs, CUDA,
  fnm, OpenCV) in one run. Slow — pulls the asdf-managed devops CLI tail from
  `.chezmoi.yaml.tmpl`'s `data:` block (spec 09 §"Template data block").

## How the harness consumes these

`harness.py` (impure shell, 🛠 harness-builder) reads the chosen fixture, mounts or copies it into the
guest at `~/.config/chezmoi/chezmoi.yaml` over the same `tart --dir` share used for the dotfiles source
(or via a one-shot `ssh admin@<ip> 'cat > ~/.config/chezmoi/chezmoi.yaml'` piping the fixture's bytes),
**before** invoking `chezmoi init`. This is a harness-side-only mechanism — no edit to `zsh-dotfiles`
required, per spec 08(b)'s Option A decision.
