# 13 — Build-Time Secrets

Owner: 🧪 harness. Sources: HashiCorp Packer docs, Homebrew's `Manpage.md`, `git-config(1)`, and direct
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
backing image and `strings` still finds it. Tart stores each VM under `~/.tart/vms/<name>/` with a raw
disk image by default (`disk_format = "raw"`, [02](./02-packer-tart-builder.md)), so the same property
holds there.

This inverts the strategy. **The goal is not to clean up secrets. It is never to write them to the guest
filesystem.** A design with no write has no cleanup step to get wrong and no residue to shred.

<!-- UNVERIFIED: reproduced on the host against a UDIF/APFS image via hdiutil, not inside a tart VM
against its own disk image. Unlink-does-not-zero is generic to block-backed filesystems, but the
tart-specific reproduction is what `just verify-no-secrets` turns into a standing check. -->
<!-- UNVERIFIED: whether the same holds for `disk_format = "asif"` (macOS 26+), a sparse format
rather than raw. -->

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
  public and clone anonymously (`HTTP 200` from `info/refs?service=git-upload-pack`).

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

## The design

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

```make
build-golden:
    @HOMEBREW_GITHUB_API_TOKEN="${HOMEBREW_GITHUB_API_TOKEN:-$(gh auth token 2>/dev/null)}" \
      packer build packer/tart-golden-image.pkr.hcl
```

The same shell-env-then-`gh auth token` pattern `link-check` already uses. Note that `gh auth token`
returns the operator's **full-privilege** token. Homebrew's manpage says the API token "doesn't require
permissions for any of the scopes," so prefer a dedicated **scopeless PAT**; the `gh` fallback is a
convenience, and it hands the build VM more privilege than it needs.

No `.pkrvars.hcl`. Variable-definition files are plaintext on disk, and a secret in one is a secret in
your editor's undo history and your next `git status`.

## `sensitive` masks values, not variables

`sensitive = true` [obfuscates the value from Packer's output](https://developer.hashicorp.com/packer/docs/templates/hcl_templates/variables).
Executed against `tests/fixtures/packer-sensitive/`, three things are true, and the third is a trap:

1. The value prints as `<sensitive>`, including under `PACKER_LOG=1`. The debug log is not a bypass.
2. A non-sensitive variable holding the **same string** also prints `<sensitive>`.
3. Therefore masking is **value-based and global**, not variable-scoped. A secret whose value is `admin`
   renders an unrelated log line as `the <sensitive> user is <sensitive>`.

**So do not mark `ssh_password` sensitive.** [02](./02-packer-tart-builder.md) hard-codes
`ssh_username = "admin"` / `ssh_password = "admin"`, which is public — it is the documented credential
for every prebuilt tart image ([01](./01-tart-core.md)). Marking it sensitive would redact the word
`admin` from every build log, destroying their readability, and protect nothing.

### The masking claims need a control

"The secret did not appear in the output" is also satisfied by *no output at all*. The ledger therefore
pairs each `must_fail` masking claim with a control asserting that `packer inspect` does print
non-sensitive literals under the same conditions. `tests/fixtures/packer-sensitive/fixture.pkr.hcl`
exists only to be probed this way: `packer inspect` on it needs no plugins, no stdin, and exits 0.

This also exposed a real bug in the verifier, now fixed: a missing binary raised `FileNotFoundError`,
whose detail string lacked the `UNREACHABLE:` prefix, so `must_fail` **inverted it into a pass**. A
control claim would have reported `[PASS]` on a host without `packer` installed — verifying nothing.
`cli-help` now returns `UNREACHABLE:` when `argv[0]` is not on `PATH`, and gained an optional `env` dict
so the `PACKER_LOG=1` claim is expressible rather than merely asserted.

## Residue model

| Surface | Exposure |
|---|---|
| Guest filesystem, `~/.tart/vms/<name>/` | none — the token exists only as an env var on one command |
| Guest process table | visible for that command's lifetime; single-tenant, ephemeral VM |
| Packer's uploaded scripts on the guest | contain no secret; [`skip_clean` defaults to `false`](https://developer.hashicorp.com/packer/docs/provisioners/shell) and removes them anyway |
| Host-side Packer output, incl. `PACKER_LOG=1` | masked by `sensitive = true` (executed, with a control) |
| `tart push` to a registry | inherits the artifact's cleanliness; enforced by `just verify-no-secrets` |

The canary scans the VM directory rather than naming a file inside it: tart documents
[`~/.tart/vms/` as the location](https://tart.run/faq/#vm-location-on-disk) but not the disk file's name,
and `disk_format` may be `raw` or `asif`.

```make
verify-no-secrets vm:
    @tok="${HOMEBREW_GITHUB_API_TOKEN:-$(gh auth token 2>/dev/null)}"; \
     test -n "$tok" || { echo "no token to search for"; exit 0; }; \
     if LC_ALL=C grep -r -a -l -F "$tok" ~/.tart/vms/{{vm}}/ 2>/dev/null; then \
       echo "LEAK: token found in artifact"; exit 2; \
     else echo "clean: token absent from ~/.tart/vms/{{vm}}/"; fi
```

## Cross-references

- The builder fields this composes (`ssh_password`, `disk_format`, provisioners):
  [02-packer-tart-builder.md](./02-packer-tart-builder.md)
- Where the golden image is built and torn down: [08-dotfiles-test-harness.md](./08-dotfiles-test-harness.md)
- The `just` surface and the claims ledger this spec extends:
  [12-tooling-and-agent-loop.md](./12-tooling-and-agent-loop.md)
- Every URL cited above, graded: [11-sources.md](./11-sources.md#build-time-secrets)
