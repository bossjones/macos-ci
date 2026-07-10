# 11 — Sources

Every URL fetched (or attempted) across the research pass, grouped by bucket, each with a one-line
"what it gave us" and a grade:

| Grade | Meaning |
|---|---|
| `[meaty]` | Substantial, directly-cited content |
| `[thin]` | A stub, index, or TOC page — useful mainly as a pointer |
| `[cited-as-exclusion]` | Read only to establish what it does **not** support; never cited as evidence |

**Every source URL in this research is live.** Probed with
`curl -sS -o /dev/null -w '%{http_code}' -L`: 47/47 return `200`. There is no `[404]` grade because
nothing is dead — see the retraction below for the URL that was wrongly believed to be.

**Every URL below is a live markdown link on purpose.** `just link-check` runs
[lychee](https://github.com/lycheeverse/lychee) over this file; a bare-backtick URL would be invisible to
it, which is how the mistake in the retraction section below survived a full cross-check pass.

## Tart core

| URL | Grade | What it gave us |
|---|---|---|
| [tart.run/quick-start/](https://tart.run/quick-start/) | `[meaty]` | Install, full core CLI verb table, prebuilt ghcr.io image matrix + default creds, `--dir` shared-mount syntax, disk-resize recovery procedure — [01](01-tart-core.md) |
| [tart.run/faq/](https://tart.run/faq/) | `[meaty]` | NAT vs bridged networking, `~/.tart` layout + auto-pruning, macOS 15+ headless keychain requirement (G8), nested-virtualization M3/M4+Linux-only limit (G8) — [01](01-tart-core.md) |

## Packer + Tart builder

| URL | Grade | What it gave us |
|---|---|---|
| [github.com/cirruslabs/packer-plugin-tart](https://github.com/cirruslabs/packer-plugin-tart) | `[thin]` | Install snippet, macOS 15 host requirement, Sequoia local-network SSH workaround — explicitly defers config docs elsewhere — [02](02-packer-tart-builder.md) |
| [developer.hashicorp.com — tart builder](https://developer.hashicorp.com/packer/integrations/cirruslabs/tart/latest/components/builder/tart) | `[meaty]` | Canonical full field reference (source-VM, registry, resources, disk, display/boot, runtime, SSH, HTTP server, VNC) — [02](02-packer-tart-builder.md) |
| [github.com/markkenny/macos-virtualisation](https://github.com/markkenny/macos-virtualisation) | `[meaty]` | Real-world reference pipeline: `Packer.sh`/`Tarter.sh`, 15-20 min build time, IPSW sourcing, clone-and-run pattern, Ansible-during-build precedent, config toggles — [02](02-packer-tart-builder.md) |

### Verifying packer docs URLs

`developer.hashicorp.com` is a Next.js app, not MkDocs/Jekyll — it ships no static search-index JSON
like `tart.run` or `docs.getutm.app` do. Its client-side search is Algolia (index `product_PACKER`,
`searchOnlyApiKey` visible per-page in the embedded `__NEXT_DATA__` blob), but querying it needs the
Algolia `appId`, which is a build-time-inlined constant absent from every served HTML/JSON page —
extracting it would mean scraping a minified JS bundle, so this is rejected as a verification method.

The usable authoritative-page-list equivalent is its
[server-sitemap.xml](https://developer.hashicorp.com/server-sitemap.xml), advertised in `robots.txt`:

```bash
curl -fsSL https://developer.hashicorp.com/server-sitemap.xml |
  grep -o '<loc>https://developer.hashicorp.com/packer/docs[^<]*</loc>'
```

This returns **203 pages** under `/packer/docs` (out of 337 total `/packer/*` URLs in the sitemap).

**It does not cover `/packer/integrations/**`** — including the tart-builder page cited above as the
canonical field reference. 0 of the 337 `/packer/*` sitemap entries match `/packer/integrations`.
Root cause, confirmed against the plugin's own GitHub repo:
[cirruslabs/packer-plugin-tart's `.web-docs/`](https://github.com/cirruslabs/packer-plugin-tart/tree/main/.web-docs)
directory (`components/`, `metadata.hcl`, `README.md`) — HashiCorp renders third-party
plugin/integration pages directly from that directory, per release tag, rather than from its own
CMS/sitemap. The plugin repo is the actual source of truth for that page, not
`developer.hashicorp.com` itself. Verify an integrations page with a plain
`curl -sS -o /dev/null -w '%{http_code}'` against the URL, or by reading the plugin repo's
`.web-docs/` directly — grepping the sitemap won't find it.

Other avenues checked and rejected: `llms.txt` / `llms-full.txt` (404), a `.md` content-negotiation
suffix on doc pages (404), and a few guessed content/registry API paths (all 404).

## Tart CI integration and Orchard

| URL | Grade | What it gave us |
|---|---|---|
| [tart.run/integrations/cirrus-cli/](https://tart.run/integrations/cirrus-cli/) | `[meaty]` | `.cirrus.yml` macOS-task syntax, local/cloud parity, artifact extraction (`--artifacts-dir`) — [03](03-tart-ci-and-orchard.md). **Does not contain the "we recommend Cirrus CLI" sentence, nor `sshpass`** — those are on [tart.run/quick-start/](https://tart.run/quick-start/), and conflating the two is guarded by a `must_fail` control claim |
| [tart.run/quick-start/#ssh-access](https://tart.run/quick-start/#ssh-access) | `[meaty]` | The upstream recommendation to use Cirrus CLI for running scripts / retrieving artifacts in a Tart VM, **and** the `sshpass -p admin ssh …` + `tart ip` fallback it names (incl. `brew install cirruslabs/cli/sshpass` and the `< script.sh` stdin form) — [03](03-tart-ci-and-orchard.md) |
| [github.com/cirruslabs/cirrus-cli](https://github.com/cirruslabs/cirrus-cli) | `[thin]` | The tool's own repo. Install and `.cirrus.yml` reference; the Tart-specific framing lives on the two `tart.run` pages above — [03](03-tart-ci-and-orchard.md) |
| [tart.run/orchard/quick-start/](https://tart.run/orchard/quick-start/) | `[meaty]` | Controller/worker architecture, `orchard dev`, core VM commands, SSH/VNC proxy, worker license tiers by env var — [03](03-tart-ci-and-orchard.md), [04](04-tart-licensing-risk.md) |

## Tart / Orchard licensing (G4)

| URL | Grade | What it gave us |
|---|---|---|
| [tart.run/licensing/](https://tart.run/licensing/) | `[meaty]` | Current tier table (Free/Gold/Platinum/Diamond), the "all cores always counted" clarification — [04](04-tart-licensing-risk.md) |
| [tart.run/blog/](https://tart.run/blog/) | `[thin]` | Blog index; the two posts below are what mattered |
| [Changing Tart's license (2023-02-11)](https://tart.run/blog/2023/02/11/changing-tart-license/) | `[meaty]` | Fair Source 100 transition, personal-use exemption, "server installation" definition (no connected display) — [04](04-tart-licensing-risk.md) |
| [Cirrus Labs enforces its Fair Source license (2025-10-27)](https://tart.run/blog/2025/10/27/press-release-cirrus-labs-successfully-enforces-its-fair-source-license/) | `[meaty]` | Proof enforcement is not theoretical — competing-product violation, paid settlement, named counsel — [04](04-tart-licensing-risk.md) |

## UTM automation and the IaC gap

| URL | Grade | What it gave us |
|---|---|---|
| [docs.getutm.app/](https://docs.getutm.app/) | `[thin]` | Docs home; nav is the authoritative page index (and revealed pages the brief omitted) |
| [mac.getutm.app/](https://mac.getutm.app/) | `[thin]` | Product landing page — download, feature bullets. No automation content |
| [docs.getutm.app/installation/macos/](https://docs.getutm.app/installation/macos/) | `[thin]` | How a human installs UTM.app. No CLI/unattended install path |
| [scripting/reference/](https://docs.getutm.app/scripting/reference/) | `[meaty]` | Full AppleScript dictionary: UTM/Guest/Configuration/USB/Registry/Input suites, **the QEMU-guest-agent gate on the Guest Suite**, `apple configuration` field reference — [05](05-utm-automation.md), [06](06-utm-macos-guest.md) |
| [scripting/cheat-sheet/](https://docs.getutm.app/scripting/cheat-sheet/) | `[meaty]` | Worked AppleScript snippets for every suite, annotated for backend applicability — [05](05-utm-automation.md) |
| [advanced/remote-control/](https://docs.getutm.app/advanced/remote-control/) | `[meaty]` | `utm://` URL-scheme command table, Shortcuts/Automator recipes, improper-shutdown warnings — [05](05-utm-automation.md) |
| [advanced/headless/](https://docs.getutm.app/advanced/headless/) | `[meaty]` | Headless setup (delete display / serial-terminal device), dock-icon hiding — [05](05-utm-automation.md) |
| [preferences/macos/](https://docs.getutm.app/preferences/macos/) | `[thin]` | App-wide prefs incl. dock-icon toggle and UTM server remote-access settings — [05](05-utm-automation.md), [07](07-utm-settings-appendix.md) |
| [basics/actions/](https://docs.getutm.app/basics/actions/) | `[thin]` | GUI VM actions (start/pause/stop/clone/share). The AppleScript equivalents in `scripting/reference` supersede this for automation |
| [basics/controls/](https://docs.getutm.app/basics/controls/) | `[thin]` | GUI toolbar/input controls. No automation surface |
| [advanced/version/](https://docs.getutm.app/advanced/version/) | `[thin]` | How to read the UTM build version. No bearing on the harness |
| [utmapp/UTM discussion #3618](https://github.com/utmapp/UTM/discussions/3618) | `[meaty]` | The "Machines-as-code" IaC feature request and the maintainer's "a long way off" reply — direct source for **G1** — [05](05-utm-automation.md) |
| [utmapp/UTM issue #3718](https://github.com/utmapp/UTM/issues/3718) | `[thin]` | The tracked, still-open IaC-support issue referenced by the discussion above — [05](05-utm-automation.md) |

## UTM macOS guest support

| URL | Grade | What it gave us |
|---|---|---|
| [guest-support/macos/](https://docs.getutm.app/guest-support/macos/) | `[meaty]` | macOS 12+/Apple-Silicon-host requirement, IPSW sourcing, the master missing-features list, VirtioFS + network-sharing mount instructions, clipboard sharing steps — [06](06-utm-macos-guest.md) |
| [settings-apple/virtualization/](https://docs.getutm.app/settings-apple/virtualization/) | `[meaty]` | **The page the brief omitted.** Balloon, entropy, sound/keyboard/pointer (macOS 12+), trackpad (13+), Rosetta (13+), clipboard sharing — each with its guest-version gate — [06](06-utm-macos-guest.md) §9 |
| [advanced/disposable/](https://docs.getutm.app/advanced/disposable/) | `[thin]` | Single-sentence confirmation: disposable mode is QEMU-backend only — direct source for **G5** — [06](06-utm-macos-guest.md) |
| [advanced/multiple-displays/](https://docs.getutm.app/advanced/multiple-displays/) | `[thin]` | Single-sentence confirmation: no multi-display on Apple backend — direct source for **G6** — [06](06-utm-macos-guest.md) |
| [advanced/recovery/](https://docs.getutm.app/advanced/recovery/) | `[thin]` | 1TR recovery-mode boot, macOS 13+/Apple-backend-only, SIP-disable use case — [06](06-utm-macos-guest.md) |
| [advanced/serial/](https://docs.getutm.app/advanced/serial/) | `[thin]` | PTTY-vs-network-socket serial backends, `screen /dev/ttysNNN` connection pattern — [06](06-utm-macos-guest.md) |
| [advanced/rosetta/](https://docs.getutm.app/advanced/rosetta/) | `[thin]` | Confirms Rosetta (x86_64-on-ARM) applies to **Linux** guests only — direct source for **G7** |
| [guest-support/dynamic-resolution/](https://docs.getutm.app/guest-support/dynamic-resolution/) | `[thin]` | macOS 14+ Apple-backend auto-resolution vs QEMU's manual `xrandr` workaround — [06](06-utm-macos-guest.md) |
| [guides/guides/](https://docs.getutm.app/guides/guides/) | `[thin]` | Index of per-guest walkthroughs. All non-macOS except `classic-macos` |
| [guides/classic-macos/](https://docs.getutm.app/guides/classic-macos/) | `[thin]` | Confirmed out-of-scope: classic 68k/PPC Mac OS emulation, unrelated to macOS 12+ Apple-backend — [06](06-utm-macos-guest.md) |

## UTM settings pages (thin appendix)

| URL | Grade | What it gave us |
|---|---|---|
| [settings-apple/settings-apple/](https://docs.getutm.app/settings-apple/settings-apple/) | `[meaty]` | The Settings (Apple) index. Source of a load-bearing ADR claim: *"Apple Virtualization backend supports only virtualization and is less mature than QEMU. It is the only way to run macOS virtualized on Apple Silicon."* TOC = Boot, Devices, Drive, Information, Sharing, System, Virtualization |
| [settings-qemu/settings-qemu/](https://docs.getutm.app/settings-qemu/settings-qemu/) | `[thin]` | The Settings (QEMU) index; contrast-only |
| [settings-apple/boot/](https://docs.getutm.app/settings-apple/boot/) | `[thin]` | OS selection, IPSW field — [07](07-utm-settings-appendix.md) |
| [settings-apple/drive/](https://docs.getutm.app/settings-apple/drive/) | `[thin]` | Drive fields incl. macOS 26+ ASIF format — [07](07-utm-settings-appendix.md) |
| [settings-apple/system/](https://docs.getutm.app/settings-apple/system/) | `[thin]` | CPU/memory fields — [07](07-utm-settings-appendix.md) |
| [settings-apple/information/](https://docs.getutm.app/settings-apple/information/) | `[thin]` | Cosmetic name/notes/icon — [07](07-utm-settings-appendix.md) |
| [settings-apple/sharing/](https://docs.getutm.app/settings-apple/sharing/) | `[thin]` | Shared-directory list — [07](07-utm-settings-appendix.md) |
| [settings-apple/devices/devices/](https://docs.getutm.app/settings-apple/devices/devices/) | `[thin]` | Index only: add/remove a device. TOC = Display, Network, Serial — [07](07-utm-settings-appendix.md) |
| [settings-qemu/system/](https://docs.getutm.app/settings-qemu/system/) | `[thin]` | Contrast-only: QEMU arch/CPU/memory fields — [07](07-utm-settings-appendix.md) |
| [settings-qemu/qemu/](https://docs.getutm.app/settings-qemu/qemu/) | `[thin]` | Contrast-only: logging/UEFI/RNG/balloon/TPM/TSO toggles — [07](07-utm-settings-appendix.md) |
| [settings-qemu/sharing/](https://docs.getutm.app/settings-qemu/sharing/) | `[thin]` | Contrast-only: SPICE WebDAV/VirtFS sharing — [07](07-utm-settings-appendix.md) |
| [settings-qemu/input/](https://docs.getutm.app/settings-qemu/input/) | `[thin]` | Contrast-only: USB bus version/limits, N/A to Apple backend — [07](07-utm-settings-appendix.md) |
| [settings-qemu/information/](https://docs.getutm.app/settings-qemu/information/) | `[thin]` | Byte-identical to the Apple-backend information page — [07](07-utm-settings-appendix.md) |
| [settings-qemu/devices/devices/](https://docs.getutm.app/settings-qemu/devices/devices/) | `[thin]` | Index only: add/remove a device. TOC = Display, Network, Serial, Sound |
| [settings-qemu/drive/drive/](https://docs.getutm.app/settings-qemu/drive/drive/) | `[meaty]` | Contrast-only: QEMU drive creation, importing, deletion, boot order, removable, interface, image type, raw images |
| [guest-support/sharing/sharing/](https://docs.getutm.app/guest-support/sharing/sharing/) | `[thin]` | Index over Clipboard / Directory / USB sharing; the children carry the content (SPICE WebDAV, VirtFS backends) |

## Build-time secrets

Consumed by [13](13-build-secrets.md). Everything in this bucket about Packer's own behaviour was also
**executed** against `packer` v1.15.4 and pinned in `.team/claims.jsonl`; the docs are cited for the
contract, the ledger for the fact.

| URL | Grade | What it gave us |
|---|---|---|
| [packer/docs/templates/hcl_templates/variables](https://developer.hashicorp.com/packer/docs/templates/hcl_templates/variables) | `[meaty]` | `sensitive` ("obfuscated from Packer's output"), `PKR_VAR_<name>` as a lowest-priority assignment, and the full precedence table — [13](13-build-secrets.md) |
| [packer/docs/.../functions/contextual/env](https://developer.hashicorp.com/packer/docs/templates/hcl_templates/functions/contextual/env) | `[meaty]` | `env()` is "the only function callable from a variable block", and only in `default`. Direct source for choosing the unprefixed name over `PKR_VAR_` — [13](13-build-secrets.md) |
| [packer/docs/.../functions/collection/compact](https://developer.hashicorp.com/packer/docs/templates/hcl_templates/functions/collection/compact) | `[thin]` | "returns a new list with any empty string elements removed" — the mechanism that makes the token optional — [13](13-build-secrets.md) |
| [packer/docs/provisioners/shell](https://developer.hashicorp.com/packer/docs/provisioners/shell) | `[meaty]` | `environment_vars`, and the two defaults the whole design rests on: `use_env_var_file` (false — true writes a tempfile to the guest) and `skip_clean` (false — uploaded scripts are removed) — [13](13-build-secrets.md) |
| [packer/docs/.../legacy_json_templates/user-variables](https://developer.hashicorp.com/packer/docs/templates/legacy_json_templates/user-variables) | `[cited-as-exclusion]` | The JSON-era `"sensitive-variables"` list. Read only to confirm it is the *legacy* spelling, superseded by HCL's `sensitive = true`; not the API we use |
| [Homebrew/brew `docs/Manpage.md`](https://github.com/Homebrew/brew/blob/master/docs/Manpage.md) | `[meaty]` | `HOMEBREW_GITHUB_API_TOKEN` ("Homebrew doesn't require permissions for any of the scopes" — hence the scopeless-PAT advice), `HOMEBREW_GITHUB_PACKAGES_TOKEN` (GitHub Packages registry, i.e. private-tap bottles — which is why we don't need it), and `HOMEBREW_API_DOMAIN` (default `https://formulae.brew.sh/api`) — [13](13-build-secrets.md) |
| [GitHub REST rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api) | `[meaty]` | 60 requests/hour unauthenticated vs 5,000/hour authenticated — the entire justification for injecting a token — [13](13-build-secrets.md) |
| [git-config(1)](https://git-scm.com/docs/git-config) | `[meaty]` | `GIT_CONFIG_COUNT` / `GIT_CONFIG_KEY_<n>` / `GIT_CONFIG_VALUE_<n>`: git configured wholly from the environment. This is why no `~/.gitconfig` or `~/.ssh/config` is copied into the guest — [13](13-build-secrets.md) |
| [tart.run/faq/#vm-location-on-disk](https://tart.run/faq/#vm-location-on-disk) | `[thin]` | "Local images that you can run are stored in `~/.tart/vms/`" — the directory `just verify-no-secrets` scans. Notably it does *not* name the disk file, which is why the canary globs the directory — [13](13-build-secrets.md) |
| [ivobeerens.nl — pass a GitHub variable to a Packer provisioner](https://www.ivobeerens.nl/blog/2024/06/pass-github-variable-to-packer-powershell-provisioner/) | `[thin]` | Prior art for the shape (sensitive var → provisioner env). PowerShell/Windows-flavoured, so the mechanism transfers but none of the commands do — [13](13-build-secrets.md) |

## Retraction — the G10 prune list was wrong

The research brief carried a ground truth **G10** instructing every agent that four URLs were 404 and
must not be fetched or cited. **Not one of them was a dead page.** Verified with
`curl -sS -o /dev/null -w '%{http_code}' -L`:

| URL | G10 claimed | Actual |
|---|---|---|
| [settings-qemu/devices/devices/](https://docs.getutm.app/settings-qemu/devices/devices/) | 404 | **200** |
| [settings-qemu/drive/drive/](https://docs.getutm.app/settings-qemu/drive/drive/) | 404 | **200** |
| [guest-support/sharing/sharing/](https://docs.getutm.app/guest-support/sharing/sharing/) | 404 | **200** |
| `docs.getutm.app/settings-apple/devices/` | 404 | 404 — **but this path never existed.** Not a link, hence not linked here |

That fourth entry is the interesting one. It does return 404, but it is not a page that died — it is a
**malformed path that was never in the source list**. The Settings (Apple) section is served at
[settings-apple/settings-apple/](https://docs.getutm.app/settings-apple/settings-apple/), and its Devices
child at [settings-apple/devices/devices/](https://docs.getutm.app/settings-apple/devices/devices/). The
`404` was manufactured by requesting a URL nobody had ever published, and its "deadness" was then
generalized onto three live URLs sitting next to it in the list.

Every one of the 47 URLs actually supplied for this research returns `200`.

Two things made the error durable:

1. **The instruction was self-sealing.** "Do not fetch, do not cite" guaranteed no agent could ever
   surface evidence against it. The lead's cross-check ledger marked G10 `verified` — but verifying a
   *don't-look* rule only confirms nobody looked.
2. **The brief's URL list omitted
   [settings-apple/virtualization/](https://docs.getutm.app/settings-apple/virtualization/)**, the page
   that actually documents the Apple-backend balloon/entropy/sound/keyboard/pointer/trackpad/Rosetta/
   clipboard toggles. `06` was ordered to produce that content, could not find it, and correctly recorded
   the gap — blaming the wrong cause.

The mis-pruned pages turned out to be mostly thin index/TOC pages, so little substance was lost. The real
loss was `settings-apple/virtualization/`, now written up in [06](06-utm-macos-guest.md) §9. **G10 is
retracted**; the ledger row in `.team/macos-ci.board.md` is marked accordingly. `just link-check` now
guards against a repeat.

## Local working trees (read directly, not fetched — G11)

| Path | Grade | What it gave us |
|---|---|---|
| `/Users/bossjones/dev/bossjones/zsh-dotfiles` | `[meaty]` | `.chezmoiroot`, `.chezmoiversion`, `home/.chezmoi.yaml.tmpl` (the `stdinIsATTY` non-interactive contract), `scripts/smoke-test-docker.sh` (canonical non-TTY invocation + assertion vocabulary), `test_dotfiles.py`, `CLAUDE.md`, `.github/workflows/tests.yml` — [08](08-dotfiles-test-harness.md), [09](09-dotfiles-under-test.md) |
| `/Users/bossjones/dev/bossjones/zsh-dotfiles-prep` | `[meaty]` | `bin/zsh-dotfiles-prereq-installer`, `Brewfile`, `Makefile`, `TESTING.md`/`DEBUG.md`, `Dockerfile-{centos-9,debian-12,ubuntu-2204}` (the existing Linux coverage this repo has no macOS equivalent of) — [09](09-dotfiles-under-test.md) |
| `/Users/bossjones/dev/cirruslabs/packer-plugin-tart` | `[meaty]` | The builder's own source tree, at `c10d611`. **`.web-docs/components/builder/tart/README.md` is the file HashiCorp renders as the `/packer/integrations/...` field reference cited in [02](02-packer-tart-builder.md)** — that page is absent from HashiCorp's sitemap, so this tree, not the CMS, is its ground truth (see [Verifying Packer docs URLs](#verifying-packer-docs-urls)). `builder/tart/builder.hcl2spec.go` is the generated config schema behind that reference; `step_run.go`, `step_clone_vm.go`, `step_disk_resize.go` are the build steps; `vnc.go` is the VNC/boot-command machinery behind [12](12-tooling-and-agent-loop.md)'s `gui.py`. Also `docs/builders/tart.mdx`, `example/`, `.cirrus.yml` |
| `/Users/bossjones/dev/cirruslabs/macos-image-templates` | `[meaty]` | The Packer templates that build every `ghcr.io/cirruslabs/macos-*` image, at `cd2d1c6`. **Ground truth for what is actually inside the prebuilt images**, where the prose docs only assert it. `templates/vanilla-tahoe.pkr.hcl` sets `ssh_password`/`ssh_username = "admin"` (the G8 default creds), enables Remote Login (which is what makes the `sshpass` path in [03](03-tart-ci-and-orchard.md) work at all), and enables passwordless sudo + auto-login (the latter bears on the macOS 15+ keychain requirement). `templates/base.pkr.hcl` preinstalls the **Tart guest agent** (`brew install cirruslabs/cli/tart-guest-agent`, as both LaunchDaemon and LaunchAgent — the component backing `tart ip --resolver=agent`, see [01](01-tart-core.md#the-tart-guest-agent)) *and* Homebrew, `mise`, `rbenv`, `node@24` — which is why `-base` is not a cold-start substrate for the dotfiles under test ([08](08-dotfiles-test-harness.md)). `README.md` documents the `vanilla → base → xcode → runner` layering |
| `/Users/bossjones/dev/motionbug/macad.uk2025` | `[meaty]` | "Silicon Sandbox: Mastering Mac virtualisation for Jamf workflows" (macad.uk 2025), at `270dc24`. `packer-templates/apple-tart-tahoe.pkr.hcl` is a complete `tart-cli` IPSW-lane template for macOS 26: `from_ipsw`, `recovery_partition = "keep"` (kept so `softwareupdate` still works), `create_grace_time`, and a fully variable-ised account/MDM-enrollment config. Its Setup Assistant `boot_command` — opening `"<wait60s><spacebar>"` — is a **second independent instance** of the brittle keystroke automation [12](12-tooling-and-agent-loop.md) flags via `markkenny/macos-virtualisation`, and evidence the fragility is inherent to the approach, not one author's typo |

The two bootstrap one-liners quoted verbatim in [09](09-dotfiles-under-test.md) (G9):

| URL | Grade | What it gave us |
|---|---|---|
| [chezmoi.io/get](https://chezmoi.io/get) | `[meaty]` | The chezmoi installer the `zsh-dotfiles` bootstrap pipes into `sh` |
| [github.com/bossjones/zsh-dotfiles](https://github.com/bossjones/zsh-dotfiles) | `[meaty]` | The chezmoi source repo the bootstrap one-liner targets |
| [zsh-dotfiles-prereq-installer](https://raw.githubusercontent.com/bossjones/zsh-dotfiles-prep/main/bin/zsh-dotfiles-prereq-installer) | `[meaty]` | The prereq installer the `zsh-dotfiles-prep` bootstrap pipes into `bash` |

## Read as counter-evidence, never cited as support (G2)

| URL | Grade | What it gave us |
|---|---|---|
| [tonyyo11 — Prepping for Learning Terraform (Oct 2025)](https://tonyyo11.github.io/posts/October-Learning-Terraform/) | `[cited-as-exclusion]` | Uses Terraform to manage **Jamf Pro resources**, not VMs. Establishes **G2**: it is not evidence of VM-as-code for either tool. Referenced only in [10](10-tart-vs-utm-adr.md) to preempt the misreading |
| [motionbug — Baking Up Your Perfect Jamf Pro Test VM](https://motionbug.com/the-cookbook-baking-up-your-perfect-jamf-pro-test-vm/) | `[cited-as-exclusion]` | A Jamf-Pro-flavored VM cookbook. Same trap as above: adjacent tooling, not a VM-as-code story for tart or UTM |

## Coverage — measured, not estimated

`docs.getutm.app` publishes **78 pages**. Enumerated from its own search index, not from the nav:

```bash
curl -fsSL https://docs.getutm.app/assets/js/search-data.json |
  python3 -c 'import json,sys; print(*sorted({v["relUrl"].split("#")[0] for v in json.load(sys.stdin).values()}), sep="\n")'
```

**39 of 78 are cited above.** The 39 uncited pages, grouped — none load-bearing for this harness, but
they exist and are unread, so no reader should infer they were judged and dismissed:

| Group | Pages |
|---|---|
| Apple-backend device children | `settings-apple/devices/{display,network,serial}` |
| QEMU-backend device children | `settings-qemu/devices/{display,serial,sound}`, `.../network/{network,port-forwarding}`, `settings-qemu/drive/resize-and-compress` |
| Non-macOS guest support | `guest-support/{linux,windows}`, `guest-support/sharing/{clipboard,directory}` |
| Per-guest walkthroughs | `guides/{classic-windows,debian,fedora,kali,ubuntu,windows,windows-10}`, `guide/windows` |
| iOS | `installation/ios`, `preferences/ios` |
| Remote / UTM server | `remote/`, `remote/server/` |
| Section landing pages | `advanced/advanced`, `basics/basics`, `installation/installation`, `preferences/preferences`, `guest-support/guest-support`, `advanced/scripting` |
| Release notes | `updates/updates`, `updates/v4.0`, `v4.1`, `v4.3`, `v4.4`, `v4.5`, `v4.6`, `v4.7` |

`guest-support/sharing/{clipboard,directory}` are the only ones with plausible future relevance — they
document the SPICE WebDAV / VirtFS directory-sharing backends. Tracked in `.team/macos-ci.backlog.md`.

Three pages moved out of this list when `utmctl` was documented in [05](05-utm-automation.md) §4:
`scripting/scripting` (the CLI's wrapper nature), `guest-support/sharing/usb` (USB is QEMU-only), and
`updates/v4.2` (the release notes that introduced the guest-agent-gated commands). Recount rather than
adjust by hand:

```bash
python3 - <<'EOF'
import json, re, urllib.request, pathlib

norm = lambda u: u.split("#")[0].rstrip("/") or "/"   # the site root is a real page ("What is UTM?")

idx = urllib.request.Request("https://docs.getutm.app/assets/js/search-data.json",
                             headers={"User-Agent": "coverage/1.0"})
pages = {norm(v["relUrl"])
         for v in json.loads(urllib.request.urlopen(idx, timeout=20).read()).values()}
cited = {norm(m.group(1))
         for f in list(pathlib.Path("specs").rglob("*.md")) + [pathlib.Path("CLAUDE.md")]
         for m in re.finditer(r"https://docs\.getutm\.app(/[^)\s\"'>|]*)", f.read_text())} & pages

print(f"{len(cited)} of {len(pages)} cited")
for p in sorted(pages - cited): print("  uncited:", p)
EOF
```
