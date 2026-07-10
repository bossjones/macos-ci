# macos-ci

Repo to manage my virtualized macOS images and test things that I don't want to run on my host machine
yet — chiefly, a disposable-VM harness that installs
[zsh-dotfiles](https://github.com/bossjones/zsh-dotfiles) into a clean macOS guest and asserts it worked.

**Stack: Tart (primary) + Packer + UTM (escape hatch).**

Tart drives CI: it has a Packer builder, an OCI image registry, a CLI, and an orchestrator (Orchard).
UTM stays for interactive and GUI work, recovery-mode fiddling, and non-ARM guests.

There is **no Terraform provider for tart or for UTM**, and neither dotfiles repo under test uses
Ansible — so neither is part of this stack. See
[specs/macos-ci/10-tart-vs-utm-adr.md](specs/macos-ci/10-tart-vs-utm-adr.md) for the full decision, and
the Fair Source licensing risk we accept to get there.

## Where to look

- [specs/macos-ci.md](specs/macos-ci.md) — the implementation plan
- [specs/macos-ci/00-overview.md](specs/macos-ci/00-overview.md) — orientation and reading order
- [specs/macos-ci/11-sources.md](specs/macos-ci/11-sources.md) — every source, graded

## Licensing accepted-risk sign-off (G4)

**Human sign-off given 2026-07-10.** Tart/Orchard ship Fair Source (`FSL-1.1-ALv2`, copyright holder
OpenAI following the Cirrus Labs acquisition announced 2026-04-07); the Free Tier is capped at **100
combined CPU cores** and **4 Orchard workers** across headless ("server installation") hosts. This
repo's accepted posture, per [specs/macos-ci/04-tart-licensing-risk.md](specs/macos-ci/04-tart-licensing-risk.md):

- Fleet ceiling: **at most 3 hosts, at most 100 combined CPU cores**.
- Never build a competing virtualization product on top of Tart.
- `just doctor` must **report** this ceiling as a checked precondition — it must never silently approve it.

Re-litigate only if fleet size grows past 3 hosts or the combined core count approaches 100.

## Development

```bash
just link-check    # verify every link in every markdown file (requires lychee)
```
