# harness/ssh — the throwaway harness keypair

`id_ed25519_harness` / `id_ed25519_harness.pub` — an ed25519 keypair generated for and used by this
harness only, resolving OQ-03/OQ-05 (`.team/macos-ci-build.open-questions.md`).

## Why a committed private key is fine here

This is **not** a secret in the sense `13-build-secrets.md`'s canary (`verify-no-secrets`) cares about.
It authenticates the harness host to a **disposable clone** that `just destroy`/`tart delete` throws
away after every run — never the golden image, never anything long-lived, never anything that grants
access outside this repo's own ephemeral VMs. Its private half being public would let someone SSH into
*your own locally-cloned throwaway VM*, which they'd need local access to reach in the first place.
Compare: the Homebrew token `verify-no-secrets` guards against leaking is a real, reusable credential
scoped to GitHub's API — a fundamentally different risk class.

## The two-phase auth model (OQ-05)

The golden image only configures password auth (`ssh_username`/`ssh_password` = `admin`/`admin`,
Packer's *build-time* communicator config — see `packer/tart-golden-image.pkr.hcl`). It has no
`authorized_keys` provisioning step, and rebuilding it to add one costs another build cycle. Rather than
touch 📦 packer-builder's template, `harness.py` bootstraps key trust itself, once per clone:

1. **Bootstrap** (once per clone, right after `tart run` + first `tart ip`, before the pre-apply
   `chezmoi diff` lint): `sshpass -p admin ssh -o BatchMode=no admin@<ip>` appends
   `id_ed25519_harness.pub` to the guest's `~/.ssh/authorized_keys`. This is the *only* place password
   auth or `sshpass` is used.
2. **Steady state** (everything after — `chezmoi diff`, the apply command, every `-m vm`/`-m pty` test):
   the spec-mandated `ssh_opts` (`BatchMode=yes`, per `12-tooling-and-agent-loop.md`) with
   `-i harness/ssh/id_ed25519_harness`.

`harness.py` `chmod`s the private key to `0600` before first use — git does not preserve that bit past a
fresh checkout, and OpenSSH refuses a group/world-readable private key outright.
