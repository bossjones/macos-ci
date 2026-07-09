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
- `<name>_script` keys — one or more shell instructions that execute inside the VM. Cirrus CLI copies
  the current working directory into the VM automatically before running scripts.
  <!-- UNVERIFIED: exact CWD-copy mechanism (rsync vs tart's --dir mount) not detailed on this page -->

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
control claim in `.team/claims.jsonl` (`control-tart-doc-contains-oracle`) asserts that the integrations
page does **not** mention `sshpass`, precisely to keep that conflation from being introduced later.

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
authentication accepted. `sshpass` is a **host-side** tool — nothing is installed into the guest to make
this work. See spec `01` for the credential and guest-agent facts this rests on.

The second form, `ssh <host> < script.sh`, feeds the script over **stdin with no TTY**. That is the same
no-TTY exec path the harness depends on in
[08 §(b)](08-dotfiles-test-harness.md#the-run-composed-from-tart-primitives) to make chezmoi's
`stdinIsATTY` evaluate false — `sshpass` changes the authentication method, not the TTY semantics.

**Which one this repo uses.** `cirrus run` is the upstream-recommended path and the one spec `12` wires
to the `ci` recipe. The harness itself (spec `08`) uses plain key-based `ssh` over `tart ip`, so the
`sshpass` password path is a **documented fallback, not a dependency**: it is useful for a throwaway
one-liner against a freshly cloned VM that has no key installed yet.

Consequently `sshpass` is deliberately **not** a `just doctor` requirement. At time of writing this host
has `cirrus` 1.0.0 and does **not** have `sshpass`, and that is not a defect — adding it to the doctor
requirement table would fail the preflight for a tool no code path calls. Tooling source:
[github.com/cirruslabs/cirrus-cli](https://github.com/cirruslabs/cirrus-cli).

### How this repo would eventually use it

Framing (not yet implemented — DOCS ONLY per house scope):

1. Wrap the harness's per-VM chezmoi-apply + assertion flow (spec `08`) in a `.cirrus.yml` task whose
   `macos_instance.image` points at the golden image built in spec `02`.
2. Run it locally with `cirrus run` during development — identical syntax to what would eventually run
   in CI, satisfying "works the same locally and in CI" without extra tooling.
3. Because Cirrus CI hosted cloud restricts images to Cirrus-managed ones, a **self-hosted** CI runner
   (a Mac with Tart + Cirrus CLI installed, triggered by whatever CI system this repo adopts) is the
   only path to running our own custom golden image in an automated pipeline — this is *not* something
   hosted Cirrus CI can do for us. <!-- UNVERIFIED: no source page describes self-hosted Cirrus CI
   runner registration; inferred from the "only Cirrus-managed images" constraint -->

---

## Part B — Orchard (multi-host orchestration)

### What it is

Orchard is Cirrus Labs' orchestration layer for running Tart VMs across **multiple hosts**, via either
the `orchard` CLI or a REST API. Quoting the docs: it "allows you to orchestrate multiple Tart-capable
hosts from either an Orchard CLI or through the API." ([tart.run/orchard/quick-start/](https://tart.run/orchard/quick-start/)) This is Tart's
answer to "how do I run VMs on a fleet of Macs, not just one laptop" — per **G1**, this is the *only*
IaC-adjacent orchestration story Tart has; there is no Terraform provider for Tart or Orchard.

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
image default creds noted in **G8**). All port forwarding for these two commands "proxies a secure
connection to the Orchard Workers" through the controller — meaning a worker sitting behind a strict
firewall with no inbound ports open can still be reached for SSH/VNC as long as it can dial out to the
controller. ([tart.run/orchard/quick-start/](https://tart.run/orchard/quick-start/))

### Worker license tiers

| Env var value | Worker connections allowed |
|---|---|
| *(unset — default license)* | 4 |
| `ORCHARD_LICENSE_TIER=gold` | 20 |
| `ORCHARD_LICENSE_TIER=platinum` | 200 |

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
