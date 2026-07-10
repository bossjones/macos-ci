# 13 — Build-Time Secrets

Owner: 🔐 secrets. Sources: HashiCorp Packer docs, Homebrew's `Manpage.md`, `git-config(1)`, and direct
execution against `packer` v1.15.4 on the build host. Behaviour marked "executed" below was run, not
inferred; the reproductions are in the claims ledger.

The golden-image build ([02](./02-packer-tart-builder.md)) runs a long `brew install` chain. GitHub caps
unauthenticated REST access at **60 requests/hour** and authenticated access at **5,000/hour**, so the
build wants `HOMEBREW_GITHUB_API_TOKEN`. The artifact must not carry it.

## The Linux lane already solved this

`zsh-dotfiles` does not bake the token into a Docker layer. It mounts it:

```dockerfile
RUN --mount=type=secret,id=homebrew_token \
    HOMEBREW_GITHUB_API_TOKEN=$(cat /run/secrets/homebrew_token 2>/dev/null || true) \
    brew install python@3.12 pre-commit actionlint && \
    ...
```

(`zsh-dotfiles/Dockerfile:127`. The `|| true` is load-bearing: the build works without a token, just
slower.)

BuildKit's guarantee is that the secret is visible to the command and absent from every layer. **Packer
has no equivalent primitive.** This spec reconstructs that guarantee out of parts Packer does have. As
with the `stdinIsATTY` contract in [09](./09-dotfiles-under-test.md#the-chezmoi-template-contract-g11),
the upstream repo got there first; we are matching it, not inventing it.

## Delete-after-use is not erasure

The obvious design — upload the secret, use it, `rm` it before saving the artifact — does not work, and
fails silently, which is worse. Reproduced on the build host:

```bash
hdiutil create -quiet -size 20m -fs APFS -volname RESIDUE -type UDIF /tmp/t
DEV=$(hdiutil attach -nobrowse /tmp/t.dmg | awk '/RESIDUE/{print $1; exit}')
echo SENTINEL_TOKEN > /Volumes/RESIDUE/secret.txt && sync
rm /Volumes/RESIDUE/secret.txt && sync && hdiutil detach -quiet "$DEV"
strings -a /tmp/t.dmg | grep -c SENTINEL_TOKEN   # => 1
```

`rm` unlinks the inode and marks blocks free. It does not zero them. The plaintext survives in the
backing image and `strings` still finds it. Tart stores each VM under `~/.tart/vms/<name>/`; on the
golden image's clone lane the builder never passes `--disk-format` at all (see below), so the guest
inherits its source image's format and the same property holds there.

This inverts the strategy. **The goal is not to clean up secrets. It is never to write them to the guest
filesystem.** A design with no write has no cleanup step to get wrong and no residue to shred.

<!-- UNVERIFIED: reproduced on the host against a UDIF/APFS image via hdiutil, not inside a tart VM
against its own disk image. Unlink-does-not-zero is generic to block-backed filesystems, but the
tart-specific reproduction is what `just verify-no-secrets` turns into a standing check. -->
<!-- UNVERIFIED: whether the same holds for `disk_format = "asif"` (macOS 26+), a sparse format
rather than raw. -->

### `disk_format` does not mean what this spec used to say it meant

An earlier draft justified "raw disk image" by citing `disk_format = "raw"` as 02's documented default.
`raw` *is* the field's default — but the field reaches `tart` only on the **create** path. Read from the
local `packer-plugin-tart` clone:

| Fact | Where |
|---|---|
| `if b.config.DiskFormat == "" { b.config.DiskFormat = "raw" }` | `builder/tart/builder.go:93-94` |
| `--disk-format` appended only when creating from IPSW/ISO | `builder/tart/step_create_vm.go:33-34` |
| the clone step never mentions `DiskFormat` | `builder/tart/step_clone_vm.go` (absent) |

The plugin's own field reference agrees: *"Only applies when using `from_ipsw` and `from_iso`."* The
golden image is **cloned** from a prebuilt `ghcr.io/cirruslabs/macos-*` image, so `disk_format` is inert
on our lane — setting it to `asif` there would be a silent no-op — and the guest inherits whatever format
its source image already uses.

Two consequences, and I am careful not to overstate either. The residue argument does **not** rest on
`disk_format`; it rests on the source image's format, which this run has not established. And
[OQ-01](../../.team/macos-ci.open-questions.md) is **narrower** than it reads: `disk_format = "asif"` can
only arise on a `from_ipsw`/`from_iso` build, never on a clone. OQ-01 is not closed — a future IPSW-based
build reopens it, and the base images' own format is still unverified — but its blast radius is smaller
than the marker at `:54` implies. The marker stays. (Ledger: `tart-builder-disk-format-defaults-to-raw`,
`tart-builder-passes-disk-format-only-on-create-path`,
`CONTROL-tart-builder-clone-step-ignores-disk-format`.)

### Packer's own cleanup is that antipattern

This is not a hypothetical someone might write. It is what Packer does for you when
`use_env_var_file = true`, verified against the provisioner source pinned at the installed version
([`v1.15.4`](https://raw.githubusercontent.com/hashicorp/packer/v1.15.4/provisioner/shell/provisioner.go)):

- it writes the environment to a host tempfile, then `comm.Upload(remoteVFName, …)` **uploads it into
  the guest** as `<remote_folder>/varfile_<rand>.sh`, `chmod 0600`;
- afterwards `cleanupRemoteFile` runs **`rm -f <path>`** on the guest — an unlink, not a shred.

So the secret lands in the guest's filesystem and is then "removed" by exactly the operation this
section just showed does not erase. A successful, non-`skip_clean` build still leaves the plaintext in
the disk image. That is the whole reason `use_env_var_file` must stay `false`: not because cleanup is
unreliable, but because *cleanup cannot work*, and the only file that cannot leak is the one never
written. (Ledger: `packer-shell-use-env-var-file-uploads-into-guest`,
`packer-shell-guest-cleanup-is-an-unlink`. Both read Packer's source over the network — see OQ-13.)

## What is not needed

Three of the four things one instinctively reaches for turn out to be unnecessary here. Recording *why*,
so they are not re-litigated:

- **`HOMEBREW_GITHUB_PACKAGES_TOKEN`.** It authenticates against the GitHub Packages registry, where
  *private* taps' bottles live. Every tap in `zsh-dotfiles-prep/Brewfile` is public, and the string
  appears nowhere in either tree:
  ```bash
  grep -rI HOMEBREW_GITHUB_PACKAGES_TOKEN ~/dev/bossjones/zsh-dotfiles{,-prep}   # => no matches
  ```
  The ledger pins this for the two files that would plausibly use it (`Dockerfile`,
  `bin/zsh-dotfiles-prereq-installer`) via `absent`, which takes a single target. The broader
  "nowhere in either tree" claim rests on the `grep` above, not on the ledger.

- **An SSH private key.** `zsh-dotfiles`, `zsh-dotfiles-prep`, and `bossjones/homebrew-tap` are all
  public and clone anonymously — `HTTP 200` from `info/refs?service=git-upload-pack` for all three,
  re-executed this run with no credentials presented.

- **`~/.gitconfig` and `~/.ssh/config`.** The build's only SSH-transport URL is
  `zsh-dotfiles-prep/Brewfile:4` — `tap "bossjones/tap", "git@github.com:bossjones/homebrew-tap.git"` —
  which points at a *public* repo reached over `git@` out of habit. Git can be configured entirely from
  the environment, so the URL is rewritten to anonymous HTTPS with nothing on disk:

  ```bash
  GIT_CONFIG_COUNT=1 \
  GIT_CONFIG_KEY_0=url.https://github.com/.insteadOf \
  GIT_CONFIG_VALUE_0=git@github.com: \
    brew bundle --file=~/.Brewfile
  ```

  Executed: env-only config overrides on-disk config, and a clone through a rewrite retains the *clean*
  original URL in `.git/config` — the rewrite target never reaches the filesystem. Copying the
  operator's real `~/.ssh/config` would also drag 8.4 KB of unrelated corp hostnames into a CI image.

  **"It worked" is not evidence that the rewrite fired** — on this host `git@github.com:` would also
  succeed over the operator's own SSH agent, which a CI runner will not have. The rewrite is therefore
  demonstrated against a *disabled* SSH transport, with a negative control proving the transport really
  is dead:

  ```bash
  # A. control: ssh disabled, no rewrite      -> exit 128  (ssh transport genuinely dead)
  GIT_SSH_COMMAND=false git ls-remote git@github.com:bossjones/homebrew-tap.git HEAD
  # B. ssh disabled, rewrite applied          -> exit 0    (only HTTPS can explain this)
  GIT_SSH_COMMAND=false GIT_CONFIG_COUNT=1 \
    GIT_CONFIG_KEY_0=url.https://github.com/.insteadOf GIT_CONFIG_VALUE_0=git@github.com: \
    git ls-remote git@github.com:bossjones/homebrew-tap.git HEAD
  ```

## The design

> **This template does not exist yet.** `packer/tart-golden-image.pkr.hcl` is **absent from the repo**,
> while [`Justfile:44`](../../Justfile) invokes it — so `just build-golden` is **broken today** (defect
> D1). What follows is a *design*, not a transcript of a file on disk, and no line of it has been
> validated: `packer build` and `packer init` are outside this run's scope, so nothing here has ever
> been executed end-to-end. Whether to guard the recipe or author the template is
> [OQ-04](../../.team/macos-ci.open-questions.md), a decision for the human.
> Ledger: `justfile-build-golden-invokes-missing-template`, `golden-template-does-not-exist`.
>
> The claims below about `sensitive`, `env()`, `GIT_CONFIG_*` and `use_env_var_file` **were** executed —
> against `tests/fixtures/packer-sensitive/`, against `git`, and against Packer's own source. Keep the
> two apart: the *mechanisms* are verified, the *template that would compose them* is vapour.

```hcl
variable "homebrew_github_api_token" {
  type      = string
  sensitive = true                              # masks the value everywhere it appears
  default   = env("HOMEBREW_GITHUB_API_TOKEN")  # the same name brew itself reads
}

build {
  sources = ["source.tart-cli.golden"]

  provisioner "shell" {
    use_env_var_file = false   # default; must stay false — true writes a tempfile to the GUEST

    # compact() drops the empty string, so an unset token omits the variable entirely rather
    # than exporting HOMEBREW_GITHUB_API_TOKEN= and sending an empty Authorization header.
    environment_vars = compact([
      var.homebrew_github_api_token != ""
        ? "HOMEBREW_GITHUB_API_TOKEN=${var.homebrew_github_api_token}" : "",

      "GIT_CONFIG_COUNT=1",
      "GIT_CONFIG_KEY_0=url.https://github.com/.insteadOf",
      "GIT_CONFIG_VALUE_0=git@github.com:",
    ])

    inline = ["brew bundle --file=~/.Brewfile"]
  }
}
```

`environment_vars` are prefixed onto the remote command. With `use_env_var_file = false` — the default —
Packer never writes them to a file on the guest. That is the whole trick: the secret exists in the
guest's process environment for the life of one command, and nowhere else.

### `env()` versus `PKR_VAR_`

Both are real, and they compose rather than compete:

| Mechanism | What it does | Precedence |
|---|---|---|
| `env("NAME")` | reads an **unprefixed** env var. [Only callable in a variable block, only in `default`](https://developer.hashicorp.com/packer/docs/templates/hcl_templates/functions/contextual/env). | supplies a *default* |
| `PKR_VAR_<name>` | [assigns a declared variable](https://developer.hashicorp.com/packer/docs/templates/hcl_templates/variables) | an *assignment*, so it beats a default. Lowest priority among assignments. |

We use `env()` so the operator's existing `HOMEBREW_GITHUB_API_TOKEN` — the name `brew` reads and the
Dockerfile passes — flows through with no Packer-specific alias. Executed: `PKR_VAR_` still overrides it,
and `env()` on an unset variable yields `""` rather than erroring, which is what makes the token optional.

### Where the token comes from

Quoted verbatim from [`Justfile:41-44`](../../Justfile) — the recipe exists even though the template it
invokes does not:

```justfile
build-golden:
    @echo "📦 Building the golden image"
    @HOMEBREW_GITHUB_API_TOKEN="${HOMEBREW_GITHUB_API_TOKEN:-$(gh auth token 2>/dev/null || true)}" \
      packer build packer/tart-golden-image.pkr.hcl
```

The same shell-env-then-`gh auth token` pattern `link-check` already uses. The `|| true` is the same
load-bearing idiom as the Dockerfile's above: without it a `gh` that is installed but unauthenticated
makes the build fail instead of falling back to the unauthenticated 60-req/hr path.

Note that `gh auth token` returns the operator's **full-privilege** token. Homebrew's manpage says the
API token "doesn't require permissions for any of the scopes," so prefer a dedicated **scopeless PAT**;
the `gh` fallback is a convenience, and it hands the build VM more privilege than it needs.

No `.pkrvars.hcl`. Variable-definition files are plaintext on disk, and a secret in one is a secret in
your editor's undo history and your next `git status`.

## `sensitive` masks values, not variables

`sensitive = true` [obfuscates the value from Packer's output](https://developer.hashicorp.com/packer/docs/templates/hcl_templates/variables).
Executed against `tests/fixtures/packer-sensitive/`, three things are true, and the third is a trap:

1. The value prints as `<sensitive>`, including under `PACKER_LOG=1`. The debug log is not a bypass.
2. A non-sensitive variable holding the **same string** also prints `<sensitive>`.
3. Therefore masking is **value-based and global**, not variable-scoped. A secret whose value is `admin`
   renders an unrelated log line as `the <sensitive> user is <sensitive>`.

Claims 2 and 3 need their own probe. The fixture's non-sensitive `pub` defaults to
`plain_FIXTURE_CONTROL` — a *different* string from the sensitive `sec` — so no execution against the
fixture as written could ever have demonstrated them. (An earlier draft of this section asserted all
three "executed against the fixture". Two of them were not. The citation was decorative, which is the
precise failure this repo's ledger exists to catch, appearing in the spec that explains it.) The fixture
*can* answer the question without being modified, by assigning `pub` the secret's value on the command
line:

```console
$ packer inspect -var 'pub=ghp_FIXTURE_SENTINEL' tests/fixtures/packer-sensitive
var.pub: "<sensitive>"                     # non-sensitive variable, redacted anyway
var.sec: "<sensitive>"

$ packer inspect -var 'pub=notthesecret_CONTROL' tests/fixtures/packer-sensitive
var.pub: "notthesecret_CONTROL"            # control: -var really assigns; non-colliding values print

$ packer inspect -var 'pub=prefix-ghp_FIXTURE_SENTINEL-suffix' tests/fixtures/packer-sensitive
var.pub: "prefix-<sensitive>-suffix"       # redaction is SUBSTRING-level, not token-level
```

The third line is the sharp edge. Masking is a blind search-and-replace over Packer's output, so a
sensitive value is struck out *even in the middle of an unrelated string*. A scratch fixture marking
`admin` sensitive renders the sentence `the admin user is admin and lives at /admin/home` as
`the <sensitive> user is <sensitive> and lives at /<sensitive>/home` — mangling a filesystem path that
had nothing to do with any credential.

(Ledger: `packer-sensitive-masks-by-value-not-variable`,
`packer-sensitive-masks-substring-inside-larger-value`, controlled by
`CONTROL-packer-inspect-var-flag-assigns-plain-value`.)

**So do not mark `ssh_password` sensitive.** [02](./02-packer-tart-builder.md) hard-codes
`ssh_username = "admin"` / `ssh_password = "admin"`, which is public — it is the documented credential
for every prebuilt tart image ([01](./01-tart-core.md)). Marking it sensitive would redact the word
`admin` from every build log, destroying their readability, and protect nothing.

### The masking claims need a control

"The secret did not appear in the output" is also satisfied by *no output at all*. A bare negative probe
cannot tell a working redactor from a crashed binary: both emit zero occurrences of the secret, and
`must_fail` inverts both into a green check. The ledger therefore pairs each `must_fail` masking claim
with a control asserting that `packer inspect` does print non-sensitive literals **under the same `argv`
and the same `env`**. `tests/fixtures/packer-sensitive/fixture.pkr.hcl` exists only to be probed this
way: `packer inspect` on it needs no plugins, no stdin, and exits 0.

Both pairs were re-executed and their controls confirmed non-vacuous — `plain_FIXTURE_CONTROL` really is
printed by the identical command that fails to print `ghp_FIXTURE_SENTINEL`. But the second pair is
**weaker than its name claims**, and this is worth stating plainly rather than filing as a nit:

| | `packer-sensitive-hides-secret` | `…-under-debug-log` |
|---|---|---|
| control | `CONTROL-packer-inspect-prints-plain-literals` | `CONTROL-packer-debug-log-prints-plain-literals` |
| same `argv`, same `env`? | yes | yes |
| control asserts a literal the command really prints? | yes | yes |
| **control can detect that the debug log ran at all?** | n/a | **no** |

`plain_FIXTURE_CONTROL` appears on **stdout**, and stdout is byte-identical with and without the
overlay — 136 bytes either way, `diff` clean. `PACKER_LOG=1` adds 845 bytes on **stderr**, which the
verifier concatenates before matching. So `CONTROL-packer-debug-log-prints-plain-literals` would pass
unchanged against a Packer that ignored `PACKER_LOG` entirely, and the `must_fail` probe beside it would
then be asserting "the secret is absent from a debug log that was never produced". The pair is not
vacuous, but it does not test the thing its `id` promises. What is missing is a *discriminator*: a
literal that appears **only** under the overlay.

```console
$ PACKER_LOG=1 packer inspect tests/fixtures/packer-sensitive 2>&1 >/dev/null | head -1
2026/…  [INFO] Packer version: 1.15.4 [go1.25.11 darwin arm64]     # absent without the overlay
```

Proposed: `CONTROL-packer-log-env-overlay-is-effective` pins that line, and
`packer-debug-log-silent-when-overlay-disabled` (`must_fail`, with `"env": {"PACKER_LOG": "0"}`) proves
the overlay *causes* it. Pinning `0` rather than omitting the key is deliberate — the verifier merges
`env` over `os.environ` and cannot **unset** a variable, so an operator with `PACKER_LOG=1` exported
would silently promote every "no-env" claim to a debug-log run and nobody would see it. See
[OQ-14](../../.team/macos-ci.open-questions.md). Measured: `PACKER_LOG` unset, `""` and `0` all disable
logging; any other non-empty value — including `off` — **enables** it.

Two limits on all of the above, so the reader does not over-read the green checks. Every masking claim
probes `packer inspect`, which **never runs a provisioner**; masking on the `packer build` path that
actually produces an image is untested here (🔬 ledger's OQ-08). And `sensitive` governs *Packer's own
output* only — it does nothing about the guest's process table, which is why the residue model below
treats that surface separately.

This also exposed a real bug in the verifier, now fixed: a missing binary raised `FileNotFoundError`,
whose detail string lacked the `UNREACHABLE:` prefix, so `must_fail` **inverted it into a pass**. A
control claim would have reported `[PASS]` on a host without `packer` installed — verifying nothing.
`cli-help` now returns `UNREACHABLE:` when `argv[0]` is not on `PATH`, and gained an optional `env` dict
so the `PACKER_LOG=1` claim is expressible rather than merely asserted.

## Residue model

| Surface | Exposure |
|---|---|
| Guest filesystem, `~/.tart/vms/<name>/` | none — **because nothing is written**, not because anything is cleaned up. `use_env_var_file = false` is the entire control |
| Guest process table | visible for that command's lifetime; single-tenant, ephemeral VM. `sensitive` does not reach here |
| Packer's uploaded scripts on the guest | contain no secret; [`skip_clean` defaults to `false`](https://developer.hashicorp.com/packer/docs/provisioners/shell) so they are unlinked. Note that unlinking is *not* erasure (above) — this row is safe only because the scripts were never secret |
| Packer's uploaded **env-var file** on the guest | **would** carry the secret, and its `rm -f` cleanup would not erase it. Never created: `use_env_var_file` stays `false` |
| Host-side Packer output, incl. `PACKER_LOG=1` | masked by `sensitive = true` (executed, with a control; but see the `inspect`-vs-`build` limit above) |
| `tart push` to a registry | inherits the artifact's cleanliness; enforced by `just verify-no-secrets` |

The canary scans the VM directory rather than naming a file inside it: tart documents
[`~/.tart/vms/` as the location](https://tart.run/faq/#vm-location-on-disk) but not the disk file's name,
and `disk_format` may be `raw` or `asif`.

Quoted verbatim from [`Justfile:52-58`](../../Justfile):

```justfile
verify-no-secrets vm:
    @tok="${HOMEBREW_GITHUB_API_TOKEN:-$(gh auth token 2>/dev/null || true)}"; \
     if [ -z "$tok" ]; then echo "⚠️  no token in the environment — nothing to search for"; exit 0; fi; \
     if [ ! -d ~/.tart/vms/{{vm}} ]; then echo "no such VM: {{vm}}" >&2; exit 4; fi; \
     if LC_ALL=C grep -r -a -l -F "$tok" ~/.tart/vms/{{vm}}/ 2>/dev/null; then \
       echo "🚨 LEAK: the token is present in the artifact above"; exit 2; \
     else echo "✅ clean: token absent from ~/.tart/vms/{{vm}}/"; fi
```

The recipe is **deliberately not part of `just check`**: it takes a VM argument and no VM exists in this
run. Two of its guards deserve naming. `exit 0` on an absent token means *"nothing to search for"*, not
*"clean"* — a green `verify-no-secrets` on a tokenless host proves nothing, exactly like a masking probe
with no output. And the `[ ! -d ]` guard exits `4` rather than reporting a clean scan of a directory that
does not exist, which is the same failure wearing a different hat.

## Cross-references

- The builder fields this composes (`ssh_password`, `disk_format`, provisioners):
  [02-packer-tart-builder.md](./02-packer-tart-builder.md)
- Where the golden image is built and torn down: [08-dotfiles-test-harness.md](./08-dotfiles-test-harness.md)
- The `just` surface and the claims ledger this spec extends:
  [12-tooling-and-agent-loop.md](./12-tooling-and-agent-loop.md)
- Every URL cited above, graded: [11-sources.md](./11-sources.md#build-time-secrets)
