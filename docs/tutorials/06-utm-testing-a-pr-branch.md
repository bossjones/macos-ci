# 6. Testing a dotfiles PR branch in the UTM lane

## What you'll learn

How to use the UTM manual lane to *look at* a pushed `zsh-dotfiles` branch — boot a windowed macOS
guest, apply a PR branch straight from GitHub with every chezmoi prompt pre-answered, verify the
result visually in iTerm2, and capture a screenshot from the host. This is the exact session that
produced the README's hero screenshot (2026-07-12, PR
[bossjones/zsh-dotfiles#96](https://github.com/bossjones/zsh-dotfiles/pull/96)); every command below
was observed working then.

This flow differs from the lane's default bootstrap on one point, deliberately:
`just utm-bootstrap-dotfiles` mounts your **local working copy** over VirtioFS so you can test
uncommitted changes. For a branch that's already **pushed**, skip the mount entirely and let
`chezmoi init --branch` clone it from GitHub inside the guest — fewer moving parts, and the guest
needs nothing from your checkout.

## Prerequisites

- [Tutorial 1](01-getting-started.md) completed, UTM installed, `just utm-doctor` green.
- The one-time golden import done (`just utm-import-golden`; see
  [../../specs/macos-ci/06-utm-macos-guest.md](../../specs/macos-ci/06-utm-macos-guest.md) §11).
- The branch you want to test pushed to the dotfiles repo.

## 1. Pre-flight: one golden at a time

After the identity transplant, the Tart golden and the UTM golden are the same machine to
Virtualization.framework — never boot both at once. And the session clone shares the golden's MAC,
so the golden must be stopped before `utm-up` (otherwise `utm ip` cannot tell them apart):

```bash
tart list       # confirm dotfiles-golden is not running
utmctl list     # confirm dotfiles-golden-utm is stopped
```

If the UTM golden is running, stop it gracefully — note the explicit `--request` (asks the guest OS
to shut down); a bare `utmctl stop` is a **force power-off**:

```bash
utmctl stop dotfiles-golden-utm --request
```

## 2. Boot the session clone

```bash
just utm-up     # clone-if-missing → windowed start → IP discovery → SSH bootstrap
```

Prints `up: dotfiles-utm @ <ip> (run <run-id>, lane=utm)`. The clone is disposable; everything you
install or apply in it dies with `just utm-destroy`, and the golden stays untouched.

## 3. Apply the PR branch over SSH — interactively

```bash
just utm-ssh
```

Then, **inside that SSH session**, run chezmoi against the branch with every prompt pre-answered
(fill in your own values; `--branch` takes the PR's head branch name, from
`gh pr view <n> --json headRefName`):

```bash
chezmoi init -R --debug -v --apply \
  --branch claude/ruby-4-0-1-upgrade-5a05fa \
  --promptString "Name=Malcolm Jones" \
  --promptString "Email=bossjones@theblacktonystark.com" \
  --promptString "Computer name=dotfiles-utm" \
  --promptString "Host name=dotfiles-utm" \
  --promptString "version_manager=mise" \
  --promptBool "ruby=true" \
  --promptBool "pyenv=true" \
  --promptBool "nodejs=true" \
  --promptBool "k8s=false" \
  --promptBool "cuda=false" \
  --promptBool "fnm=true" \
  --promptBool "opencv=false" \
  https://github.com/bossjones/zsh-dotfiles.git
```

**Why the interactive session matters:** the dotfiles template gates its feature-bool prompts on
`stdinIsATTY`. `just utm-ssh` allocates a TTY, so the prompts fire and the `--promptBool` flags
answer them. Run the same command through a non-interactive channel (`just utm-exec`, a bare
`ssh host 'cmd'`) and those prompts never execute — every feature bool silently falls back to its
template default (`false`), and the apply quietly tests much less than you asked for. Only
`version_manager` sits outside the TTY gate (deliberate, upstream, so Docker smoke tests can set
it).

Feature bools that pull in toolchains (`ruby`, `pyenv`, `nodejs`) make the apply take minutes, not
seconds — it's building version managers inside a VM. It's running, not hung.

## 4. Verify visually in the guest window

The whole point of this lane. In the **UTM window** (not over SSH — the GUI render is the thing
being tested): open iTerm2, open a fresh tab so the newly applied zsh config loads, then:

```bash
cd ~/.local/share/chezmoi   # a git repo checked out on the PR branch → branch glyph in the prompt
ruby --version              # or whatever proves your branch's payload took effect
git status -sb
```

What the 2026-07-12 session verified this way: the pure prompt rendered the PR branch name next to
its git glyph, `ruby --version` reported the branch's new default (4.0.1 +PRISM, arm64), and
you-should-use colored the `git status` with alias tips — sheldon's plugin set demonstrably live.

**Expect this lane to surface real findings.** The same session caught three startup errors
(`pyenv/path.zsh:31-33: no such file or directory: /opt/homebrew/opt/pyenv/libexec/pyenv` — the
`pyenv=true` shell config assumes a Homebrew pyenv that nothing installs). A headless apply exits 0
either way; only a fresh interactive shell shows it. That's feedback for the *dotfiles* repo, and
exactly what this lane exists to catch.

While the guest is up, this is also the moment for the recorded UX checklist:

```bash
just utm-verify-manual      # 7 y/n verdicts on your TTY → artifacts/latest/manual-utm.json
```

## 5. Screenshot from the host

An Apple-backend guest has no VNC framebuffer and no in-guest screencapture over SSH — the capture
is host-side, of the UTM window itself:

```bash
just utm-shot hero          # → artifacts/<run-id>/screenshots/NN-hero.png
```

Two macOS permissions gate this, both attributed to the app your terminal session runs under (for a
tmux session, the app that owns the tmux server — the permission dialogs name it for you):

- **Screen & System Audio Recording** — without it, `screencapture` fails with `could not create
  image from display`. Enable it in System Settings → Privacy & Security.
- **Automation → System Events** — prompted on first use by the window-id resolver. With both
  granted, `utm shot` captures just the UTM window; if the resolver can't find it (window on
  another Space, permission missing), it degrades to a full-display capture rather than failing.

## 6. Tear down

```bash
just utm-destroy            # deletes the session clone; the golden VM is untouched
```

The applied PR branch, its toolchains, everything in the guest — gone with the clone. The next
`just utm-up` starts from the golden again.
