# 03 — Tart CI Integration (Cirrus CLI) and Orchard Orchestration

Owner: tart-ci · Sources: [tart.run/integrations/cirrus-cli/](https://tart.run/integrations/cirrus-cli/), [tart.run/orchard/quick-start/](https://tart.run/orchard/quick-start/), [tart.run/quick-start/#ssh-access](https://tart.run/quick-start/#ssh-access)

This file covers the two ways this repo could eventually automate macOS VM workloads at scale:
single-host CI via Cirrus CLI, and multi-host orchestration via Orchard. Both are framed against the
concrete goal of this repo: running dotfiles-install tests against Tart VMs, first locally, later on a
fleet.

---

## Part A — Cirrus CLI (`cirrus run`)

### What it is

Cirrus CLI is a standalone task runner that reads a `.cirrus.yml` file and executes the tasks it
describes. When a task specifies a `macos_instance`, Cirrus CLI uses **Tart** as the virtualization
backend to run that task inside a Tart VM. (source: [tart.run/integrations/cirrus-cli/](https://tart.run/integrations/cirrus-cli/))

Critically, the *same* `.cirrus.yml` that runs locally via `cirrus run` also runs unchanged in Cirrus
CI's hosted cloud — "Cirrus CI ... leverages Tart to power its macOS cloud infrastructure."
([tart.run/integrations/cirrus-cli/](https://tart.run/integrations/cirrus-cli/)) The cloud caveat: "Cirrus CI only allows images managed and
regularly updated by us" — i.e. you cannot point hosted Cirrus CI at an arbitrary custom Tart image the
way you can locally. For this repo (self-hosted, local Tart images built per spec `02`), that cloud
constraint is irrelevant — we only care about the **local** `cirrus run` path.

### Install

```
brew install cirruslabs/cli/cirrus
```

([tart.run/integrations/cirrus-cli/](https://tart.run/integrations/cirrus-cli/))

### `.cirrus.yml` syntax for a macOS task

```yaml
task:
  name: hello
  macos_instance:
    image: ghcr.io/cirruslabs/macos-tahoe-base:latest
  hello_script:
    - echo "Hello from within a Tart VM!"
```

([tart.run/integrations/cirrus-cli/](https://tart.run/integrations/cirrus-cli/)) Elements:

- `macos_instance.image` — a Tart image reference, which may be **remote** (an `ghcr.io/...` OCI
  registry image, pulled and cached — see spec `01`) or a **local** VM already present in
  `tart list`. This is the same image identity spec `01` documents for `tart clone`/`tart run`.
- `<name>_script` keys — one or more shell instructions that execute inside the VM. Cirrus CLI "will copy
  over working directory" into the VM before running scripts.
  ([tart.run/integrations/cirrus-cli/](https://tart.run/integrations/cirrus-cli/), ledger:
  `cirrus-cli-page-copies-working-directory`)

  **Copy, not mount — and `.gitignore` is honoured.** The docs page never says which, but the installed
  binary does. `cirrus run --help` documents `--dirty`: *"if set the project directory will be mounted in
  read-write mode, otherwise the project directory files are copied, taking `.gitignore` into account."*
  (ledger: `cirrus-run-dirty-copies-unless-mounted`) The `.gitignore` filter is load-bearing for a
  dotfiles harness: **an ignored file never reaches the VM.**
  <!-- UNVERIFIED: the copy TRANSPORT (rsync vs tart's --dir mount) is named by no source. `cirrus run
  --help` settles copy-vs-mount and the .gitignore filter, not the mechanism. See OQ-21. -->

### Running locally vs. cloud

```
cirrus run
```

executes `.cirrus.yml` against local Tart, using whatever Tart images/hosts are available on the
machine running the command. ([tart.run/integrations/cirrus-cli/](https://tart.run/integrations/cirrus-cli/))

### Artifact extraction

Declare artifacts with an `artifacts` instruction inside a task:

```yaml
binary_artifacts:
  path: .build/debug/tart
```

then pull them out of the VM into the host after the run:

```
cirrus run --artifacts-dir artifacts
```

Retrieved files are prefixed with the task name and the `artifacts` instruction name, so the above
resolves to a host path like `$PWD/artifacts/Build/binary/.build/debug/tart`.
([tart.run/integrations/cirrus-cli/](https://tart.run/integrations/cirrus-cli/)) For this repo, this is
the mechanism by which a dotfiles-test task could pull back logs, `chezmoi diff` output, or
assertion-script results without a separate `tart ip` + `scp` round trip (see spec `08`).

### Running scripts in a VM: `cirrus run` vs. plain `ssh`

Tart's own docs state a preference:

> We recommend using Cirrus CLI to run scripts and/or retrieve artifacts from within Tart virtual
> machines. Alternatively, you can use plain ssh connection and `tart ip` command.

— [tart.run/quick-start/#ssh-access](https://tart.run/quick-start/#ssh-access)

Note the citation. That recommendation lives on the **quick-start page**, not on the
[integrations page](https://tart.run/integrations/cirrus-cli/) the rest of this Part A cites, and the
`sshpass` fallback below appears *only* on quick-start. The two are easy to conflate — a `must_fail`
control claim in `.team/claims.jsonl`, **`CONTROL-tart-cirrus-page-has-no-sshpass`**, asserts that the
integrations page does **not** mention `sshpass`, precisely to keep that conflation from being introduced
later.

> **Correction.** This sentence previously named the control `control-tart-doc-contains-oracle`. **No such
> claim exists** — `grep -c 'control-tart-doc-contains-oracle' .team/claims.jsonl` → `0`. The ledger's
> four controls are `CONTROL-tart-cirrus-page-has-no-sshpass`, `CONTROL-tart-doc-index-oracle`,
> `CONTROL-utm-settings-apple-devices-is-fabricated` and `CONTROL-disposable-is-not-apple-backend`. A spec
> citing a ledger id that does not exist is the ledger's own failure mode, one level up.

The named alternative, verbatim from that page:

```bash
brew install cirruslabs/cli/sshpass
sshpass -p admin ssh -o "StrictHostKeyChecking no" -o "UserKnownHostsFile=/dev/null" \
  admin@$(tart ip tahoe-base) "uname -a"
sshpass -p admin ssh -o "StrictHostKeyChecking no" -o "UserKnownHostsFile=/dev/null" \
  admin@$(tart ip tahoe-base) < script.sh
```

**Why the password path works at all** is a property of how the images are built, not of Tart. The
`vanilla-*` Packer templates that produce every `ghcr.io/cirruslabs/macos-*` image set
`ssh_password = "admin"` / `ssh_username = "admin"`
([`vanilla-tahoe.pkr.hcl:20-21`](https://github.com/cirruslabs/macos-image-templates/blob/main/templates/vanilla-tahoe.pkr.hcl))
and enable **Remote Login** during first-boot setup, so the guest runs stock macOS `sshd` with password
authentication accepted. The `:20-21` citation was **re-derived with `sed -n`, not inherited**, against
the local clone, and is correct (ledger: `vanilla-tahoe-ssh-password-is-plain-admin-at-line-20`,
`vanilla-tahoe-ssh-username-is-plain-admin-at-line-21`). Both values are **public** and must never be
marked `sensitive` — per **G16**, Packer masks *values*, so doing so would redact the word `admin`
everywhere it appears. `sshpass` is a **host-side** tool — nothing is installed into the guest to make
this work. See spec `01` for the credential and guest-agent facts this rests on.

The second form, `ssh <host> < script.sh`, feeds the script over **stdin with no TTY**. That is the same
no-TTY exec path the harness depends on in
[08 §(b)](08-dotfiles-test-harness.md#the-run-composed-from-tart-primitives) to make chezmoi's
`stdinIsATTY` evaluate false — `sshpass` changes the authentication method, not the TTY semantics.

**Which one this repo uses.** `cirrus run` is the upstream-recommended path and the one spec `12` wires
to the `ci` recipe. The harness itself (spec `08`) uses plain key-based `ssh` over `tart ip`, so the
`sshpass` password path is a **documented fallback, not a dependency**: it is useful for a throwaway
one-liner against a freshly cloned VM that has no key installed yet.

Consequently `sshpass` is deliberately **not** a preflight requirement. At time of writing this host has
`cirrus` `1.0.0-1769788` and does **not** have `sshpass` (`command -v sshpass` → absent), and that is not
a defect — requiring a tool no code path calls would fail the preflight for nothing. Tooling source:
[github.com/cirruslabs/cirrus-cli](https://github.com/cirruslabs/cirrus-cli).

> **Correction.** This paragraph twice referred to a **`just doctor`** recipe and a "doctor requirement
> table". **Neither exists.** `just --summary` →
> `build-golden check default link-check link-check-fresh link-check-verbose unverified-count
> verify-claims verify-claims-json verify-no-secrets`, and `grep -in doctor Justfile` returns nothing.
> This is the same fiction the brief's own retracted **G14** asserted, surviving inside a spec that
> nobody re-checked.

### How this repo would eventually use it

Framing (not yet implemented — DOCS ONLY per house scope):

1. Wrap the harness's per-VM chezmoi-apply + assertion flow (spec `08`) in a `.cirrus.yml` task whose
   `macos_instance.image` points at the golden image built in spec `02`.
2. Run it locally with `cirrus run` during development — identical syntax to what would eventually run
   in CI, satisfying "works the same locally and in CI" without extra tooling.
3. Because Cirrus CI hosted cloud restricts images to Cirrus-managed ones (ledger:
   `cirrus-cli-page-restricts-cloud-images`), a **self-hosted** runner (a Mac with Tart + Cirrus CLI
   installed) is the path to running our own custom golden image in an automated pipeline.

   The mechanism has a name and it ships in the installed binary: **`cirrus worker` — "Persistent worker
   mode"**. `cirrus worker run --help` exposes `--token` ("pool registration token") and `--name`
   ("worker name to use when registering in the pool"). (ledger:
   `cirrus-worker-run-has-pool-registration-token`)
   <!-- UNVERIFIED: whether a persistent worker may run a CUSTOM (non-Cirrus-managed) tart image under
   hosted Cirrus CI. `cirrus worker run --help` proves pool registration EXISTS; it does not prove the
   image restriction is lifted for such workers, and no tart.run page describes Cirrus CI persistent
   workers at all ('self-hosted' appears in the tart index only under integrations/gitlab-runner). See
   OQ-22. -->

   > **Correction.** The marker on this item previously read *"no source page describes self-hosted Cirrus
   > CI runner registration; inferred from the 'only Cirrus-managed images' constraint."* Its stated
   > reason is **false**: `cirrus worker run --help` is a source, it is installed on this host, and it
   > describes pool registration precisely. The *conclusion* remains unverified — but for a different and
   > narrower reason, now stated above. An `<!-- UNVERIFIED -->` marker whose reason is wrong is worse
   > than no marker: it tells the next reader the question was already looked into.

---

## Part B — Orchard (multi-host orchestration)

### What it is

Orchard is Cirrus Labs' orchestration layer for running Tart VMs across **multiple hosts**, via either
the `orchard` CLI or a REST API. Quoting the docs: it *"allows you to orchestrate multiple Tart-capable
hosts from either an Orchard CLI (which we demonstrate below) or through the API."*
([tart.run/orchard/quick-start/](https://tart.run/orchard/quick-start/), ledger:
`orchard-orchestrates-multiple-tart-hosts`) This is Tart's answer to "how do I run VMs on a fleet of
Macs, not just one laptop" — per **G1**, this is the *only* IaC-adjacent orchestration story Tart has.

**G1, re-attacked rather than inherited.** The Terraform Registry returns **HTTP 404** for both
`cirruslabs/tart` and `cirruslabs/orchard` (ledger: `no-terraform-provider-at-cirruslabs-tart`,
`no-terraform-provider-at-cirruslabs-orchard`). Scope that evidence honestly: it refutes the **canonical
addresses only**. The registry's `/v1/providers?q=` search parameter is **ignored** — `q=tart`, `q=utm`
and `q=orchard` all return the identical `hashicorp/*` top-100 — so an *exhaustive* negative across every
namespace is **not** established here, and this spec does not claim one.

### Architecture

Controller/worker split:

- **Orchard Controller** — handles API requests, authentication, and secure connections out to workers.
- **Orchard Worker** — runs on each Tart-capable host and executes the actual VM operations.

In development mode both roles run in a single process with no auth required. Production deployments
separate controller and worker onto different machines and enable security by default.
([tart.run/orchard/quick-start/](https://tart.run/orchard/quick-start/))

### Install and dev quick-start

```
brew install cirruslabs/cli/orchard
orchard dev
```

`orchard dev` runs a combined controller+worker locally with no authentication — the fastest way to
try the CLI commands below without standing up real infrastructure. ([tart.run/orchard/quick-start/](https://tart.run/orchard/quick-start/))

### Core VM commands

```
orchard create vm --image ghcr.io/cirruslabs/macos-tahoe-base:latest tahoe-base
orchard list vms
orchard delete vm tahoe-base
```

([tart.run/orchard/quick-start/](https://tart.run/orchard/quick-start/)) Note the image reference syntax is the same `ghcr.io/...` OCI form
used by plain Tart (spec `01`) — Orchard does not introduce a separate image format.

### Access: SSH and VNC proxy

```
orchard ssh vm tahoe-base
orchard ssh vm tahoe-base --username admin --password admin
orchard ssh vm tahoe-base "uname -a"
orchard ssh vm tahoe-base "bash -s" < script.sh

orchard vnc vm tahoe-base
```

Both `ssh` and `vnc` accept `--username`/`--password` (default `admin`/`admin`, matching the prebuilt
image default creds noted in **G8**). Upstream, verbatim: *"All port forwarding connections are done via
the Orchard Controller instance which "proxies" a secure connection to the Orchard Workers."* — meaning a
worker sitting behind a strict firewall with no inbound ports open can still be reached for SSH/VNC as
long as it can dial out to the controller.
([tart.run/orchard/quick-start/](https://tart.run/orchard/quick-start/), ledger:
`orchard-controller-proxies-secure-connection-to-workers`)

### Worker license tiers

| Env var value | Worker connections allowed | Ledger claim |
|---|---|---|
| *(unset — default license)* | 4 | `orchard-default-license-allows-4-workers` |
| `ORCHARD_LICENSE_TIER=gold` | 20 | `orchard-gold-tier-raises-limit-to-20-workers` |
| `ORCHARD_LICENSE_TIER=platinum` | 200 | `orchard-platinum-tier-raises-limit-to-200-workers` |

([tart.run/orchard/quick-start/](https://tart.run/orchard/quick-start/)) These numbers are the same Gold/Platinum tier boundaries priced in
spec `04`; Orchard enforces the *worker-count* axis of the license, distinct from Tart's *CPU-core* axis
enforced per-host. Other environment variables of note: `ORCHARD_HOME` (override home dir),
`ORCHARD_URL` (controller URL override), `ORCHARD_SERVICE_ACCOUNT_NAME` /
`ORCHARD_SERVICE_ACCOUNT_TOKEN` (API auth for non-interactive/service use — relevant if a CI pipeline
needs to drive Orchard headlessly). ([tart.run/orchard/quick-start/](https://tart.run/orchard/quick-start/))

### How this repo would eventually use it

Framing (not implemented — DOCS ONLY):

Today, this repo's scale is a single dev workstation running Tart directly (spec `01`/`02`), which needs
no orchestration at all. Orchard becomes relevant only if/when dotfiles testing needs to run **the same
suite across multiple physical Macs concurrently** — e.g. fanning a matrix of `version_manager` /
toggle-config combinations (spec `09`) across several hosts to cut wall-clock time, or running a
scheduled nightly sweep. In that future state:

1. One host runs `orchard controller` (or `orchard dev` for a still-small setup), the rest run
   `orchard worker` and register against it.
2. The harness's per-VM chezmoi-apply job (spec `08`) becomes an `orchard create vm --image <golden>`
   call instead of `tart clone`, with `orchard ssh vm <name> "bash -s" < run-harness.sh` replacing the
   direct `tart ip` + `ssh` flow.
3. Teardown becomes `orchard delete vm <name>` — same as `tart delete` per-host (see **G5** / spec `08`
   part d, where UTM has no equivalent).
4. The **free** default (4 workers, Tart's 100-core ceiling) is almost certainly sufficient for a
   personal dotfiles-testing fleet of 2-4 old Macs — see spec `04` for the concrete threshold math. Only
   scale past that if the fleet genuinely grows past 4 physical worker hosts or 100 combined CPU cores.

Orchard is therefore documented here as the **scale-out answer**, not a near-term requirement — the
harness (spec `08`) should be built Orchard-agnostic (plain `tart` + `ssh` primitives) so it can be
re-pointed at Orchard later without a redesign.
