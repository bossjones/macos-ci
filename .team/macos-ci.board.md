# macos-ci Verification Run — Status Board

**State:** `DONE` ✅ (human decisions applied)  ·  **Branch:** `inital-spec`
**Workspace:** `E03FB8FF-87D2-4BD9-A65B-E2E7B1ECFE42` (`workspace:11`, `macos-ci-verify`)

> Rewritten from scratch by the 👑 lead. The prior board (an aborted Haiku-4.5 lead pass) **faked the gate**
> with a bracketed paraphrase — Defect A. Everything below is **pasted command output**.

---

## THE GATE — run personally by the lead, after human decisions

```
$ just verify-claims ; echo "EXIT=$?"     # must exit 0 BEFORE anything else proceeds
EXIT=0

$ just check ; echo "EXIT=$?"
EXIT=0
```

Complete unedited **650-line** capture: [`.team/gate-final-full.txt`](gate-final-full.txt).

**Elision declared.** Lines **1–278** are `link-check`: a header plus exactly **277** `[200]` lines.
**Zero non-200** (`grep -cE '^\[(4|5)[0-9][0-9]\]|ERROR'` → `0`). Lines **279–650** are pasted
**verbatim and complete** below: all **305** `[PASS]`, **0** `[FAIL]`, the `305/305` line, and the full
`unverified-count` output.

### The honesty budget — the arithmetic, stated explicitly

```
markers before human decisions                                        15
  08-dotfiles-test-harness.md  sheldon marker RETIRED (OQ-17)         -1   -> 14
      paid for by 6 new claims incl. CONTROL-sheldon-lock-help-prints-reinstall
      and sheldon-lock-is-mutating ("Install the plugins sources and generate the lock file")
  04-tart-licensing-risk.md    enforcement-contact marker ADDED (OQ-20) +1   -> 15
      cites OQ-20, as every added marker must
markers after                                                         15
```

Proven as a **per-file set difference**, not a count: `08` 4→3, `04` 0→1, every other file unchanged.
**No marker vanished without a claim being added. No CONFLICT.**

### Integrity sweep (lead, independent of any agent's report)

```
six original must_fail controls          INTACT, expect untouched
claims with polarity=negative            54   — every one names a control
negative claims with no control          NONE  (7 CONTROL-* doc oracles exempt by construction)
duplicate evidence groups                0
evidence targets with a `logs` component NONE
total claims / must_fail                 305 / 37
```

Adversarially re-tested by the lead, not read:
```
polarity=negative with no control  -> exit 4      logs/ evidence target -> exit 4
well-formed negative + control     -> exit 0
```

### `just check` — verify-claims + unverified-count, verbatim

```
🔬 Re-checking every spec claim against its evidence
[PASS] G11-version-manager-outside-interactive  (file-contains)
[PASS] G11-stdinIsATTY-line-2  (file-line)
         line 2: {{- $interactive := stdinIsATTY -}}
[PASS] G11-version-manager-default-asdf-line-20  (file-line)
         line 20: {{- $version_manager := "asdf" -}}
[PASS] mise-installed-by-dotfiles-on-macos  (file-contains)
[PASS] no-macos-asdf-installer  (absent)
[PASS] chezmoiignore-enforces-mutual-exclusion  (file-contains)
[PASS] smoke-test-promptstring-invocation  (file-contains)
[PASS] smoke-test-wraps-in-retry  (file-contains)
[PASS] prereq-installer-bakes-asdf  (file-contains)
[PASS] chezmoiversion-floor  (file-contains)
[PASS] tart-has-vnc-experimental  (cli-help)
[PASS] tart-has-no-graphics  (cli-help)
[PASS] utm-virtualization-page-exists  (doc-index)
[PASS] CONTROL-utm-settings-apple-devices-is-fabricated  (doc-index)
[PASS] utmctl-help-lists-exec  (cli-help)
[PASS] utmctl-help-lists-ip-address  (cli-help)
[PASS] utmctl-start-help-lists-disposable  (cli-help)
[PASS] utmctl-is-an-applescript-wrapper  (doc-contains)
[PASS] utmctl-exec-needs-qemu-guest-agent  (doc-contains)
[PASS] utm-guest-commands-need-guest-agent-v42  (doc-contains)
[PASS] utm-input-automation-is-qemu-only  (doc-contains)
[PASS] utmctl-disposable-is-qemu-only  (doc-contains)
[PASS] utmctl-usb-is-qemu-only  (doc-contains)
[PASS] utm-requires-app-open-for-headless  (doc-contains)
[PASS] CONTROL-disposable-is-not-apple-backend  (doc-contains)
[PASS] tart-recommends-cirrus-cli-for-scripts  (doc-contains)
[PASS] tart-documents-sshpass-fallback  (doc-contains)
[PASS] tart-cirrus-cli-page-exists  (doc-index)
[PASS] cirrus-cli-artifacts-dir-documented  (doc-contains)
[PASS] cirrus-run-has-artifacts-dir  (cli-help)
[PASS] tart-ip-has-agent-resolver  (cli-help)
[PASS] base-image-installs-tart-guest-agent  (file-line)
         line 167: "brew install cirruslabs/cli/tart-guest-agent",
[PASS] base-image-preinstalls-mise  (file-contains)
[PASS] vanilla-tahoe-enables-remote-login  (file-contains)
[PASS] CONTROL-tart-doc-index-oracle  (doc-index)
[PASS] CONTROL-tart-cirrus-page-has-no-sshpass  (doc-contains)
[PASS] packer-is-installed  (cli-help)
[PASS] packer-sensitive-masks-value  (cli-help)
[PASS] CONTROL-packer-inspect-prints-plain-literals  (cli-help)
[PASS] packer-sensitive-hides-secret  (cli-help)
[PASS] packer-sensitive-hides-secret-under-debug-log  (cli-help)
[PASS] CONTROL-packer-debug-log-prints-plain-literals  (cli-help)
[PASS] git-reads-config-from-env-only  (cli-help)
[PASS] gh-auth-token-subcommand-exists  (cli-help)
[PASS] linux-lane-uses-buildkit-secret-mount  (file-line)
         line 127: RUN --mount=type=secret,id=homebrew_token \
[PASS] prep-brewfile-taps-over-ssh  (file-contains)
[PASS] no-packages-token-in-dockerfile  (absent)
[PASS] no-packages-token-in-prereq-installer  (absent)
[PASS] oq02-vnc-marker-line-pin  (file-line)
         line 364: <!-- UNVERIFIED: `--vnc-experimental` is labelled experimental by Tart
[PASS] CONTROL-12-line-607-does-not-exist  (file-line)
[PASS] oq01-asif-marker-pinned-at-13-54  (file-line)
         line 54: <!-- UNVERIFIED: whether the same holds for `disk_format = "asif"` (ma
[PASS] g15-hdiutil-caveat-marker-pinned-at-13-51  (file-line)
         line 51: <!-- UNVERIFIED: reproduced on the host against a UDIF/APFS image via 
[PASS] g16-sensitive-masks-value-inside-unrelated-variable  (cli-help)
[PASS] g16-injected-secret-never-prints-in-unrelated-variable  (cli-help)
[PASS] d1-justfile-build-golden-names-absent-template  (file-line)
         line 52: packer build packer/tart-golden-image.pkr.hcl
[PASS] CONTROL-d1-packer-dir-does-not-exist  (cli-help)
[PASS] CONTROL-ls-prints-repo-root-entries  (cli-help)
[PASS] d2-spec12-carries-the-phantom-recipe-retraction  (file-contains)
[PASS] d2-justfile-has-no-build-ipsw-recipe  (absent)
[PASS] tart-quickstart-lists-monterey-xcode-15  (doc-contains)
[PASS] d5-justfile-63-discriminates-on-the-backtick  (file-line)
         line 71: @grep -rn 'UNVERIFIED' specs/ --include='*.md' | grep -v '`<!-- UNVERI
[PASS] tart-version-is-2-32-1  (cli-help)
[PASS] tart-clone-verb-exists  (cli-help)
[PASS] tart-delete-verb-exists  (cli-help)
[PASS] tart-pull-verb-exists  (cli-help)
[PASS] tart-run-has-dir-flag  (cli-help)
[PASS] tart-run-has-vnc-flag  (cli-help)
[PASS] tart-run-has-nested-flag  (cli-help)
[PASS] tart-run-help-cites-cirruslabs-guest-agent-url  (cli-help)
[PASS] tart-exec-verb-exists  (cli-help)
[PASS] tart-exec-requires-guest-agent  (cli-help)
[PASS] tart-exec-help-says-nonvanilla-images-preinstall-agent  (cli-help)
[PASS] tart-set-has-random-serial  (cli-help)
[PASS] tart-set-has-display-refit  (cli-help)
[PASS] tart-create-asif-requires-tahoe  (cli-help)
[PASS] tart-clone-has-prune-limit-flag  (cli-help)
[PASS] tart-faq-prune-limit-bounds-what-is-reclaimed  (doc-contains)
[PASS] tart-clone-has-concurrency-flag  (cli-help)
[PASS] tart-quick-start-page-exists  (doc-index)
[PASS] tart-faq-page-exists  (doc-index)
[PASS] tart-quickstart-lists-sequoia-xcode-image  (doc-contains)
[PASS] tart-quickstart-default-alloc-2cpu-4gb  (doc-contains)
[PASS] tart-quickstart-creds-work-for-gui-console-ssh  (doc-contains)
[PASS] tart-quickstart-host-requires-ventura  (doc-contains)
[PASS] tart-faq-headless-keychain-starts-at-macos-15  (doc-contains)
[PASS] tart-faq-keychain-workaround-needs-unlock-and-login-keychain  (doc-contains)
[PASS] tart-faq-nested-virt-is-m3-m4-linux-only  (doc-contains)
[PASS] g19-tart-builder-integrations-page-returns-200  (http-status)
[PASS] g19-packer-integrations-absent-from-hashicorp-sitemap  (cli-help)
[PASS] CONTROL-hashicorp-sitemap-lists-packer-docs  (cli-help)
[PASS] tart-repo-redirects-to-openai  (cli-help)
[PASS] tart-guest-agent-repo-redirects-to-openai  (cli-help)
[PASS] packer-tart-pull-concurrency-is-uint16  (file-line)
         line 36: PullConcurrency uint16   `mapstructure:"pull_concurrency"`
[PASS] packer-tart-pull-concurrency-hcl-type-is-number  (file-line)
         line 190: "pull_concurrency":             &hcldec.AttrSpec{Name: "pull_concurren
[PASS] packer-tart-pull-concurrency-passed-as-tart-concurrency  (file-line)
         line 24: commonArgs = append(commonArgs, "--concurrency", fmt.Sprintf("%d", con
[PASS] packer-tart-webdocs-mislabels-pull-concurrency-boolean  (file-contains)
[PASS] packer-tart-disk-format-only-applies-from-ipsw-or-iso  (file-contains)
[PASS] packer-tart-recovery-partition-default-is-delete  (file-contains)
[PASS] g13-packer-tart-webdocs-has-no-vnc-port-fields  (absent)
[PASS] CONTROL-packer-tart-webdocs-does-document-disable-vnc  (file-contains)
[PASS] g13-packer-tart-hcl2spec-has-no-vnc-port-fields  (absent)
[PASS] CONTROL-packer-tart-hcl2spec-documents-disable-vnc  (file-contains)
[PASS] packer-plugin-readme-requires-macos-15  (file-line)
         line 8: > **macOS 15 (Sequoia) or later**
[PASS] packer-plugin-readme-version-constraint-1-11-1  (file-line)
         line 46: version = ">= 1.11.1"
[PASS] packer-plugin-readme-defers-config-docs-to-hashicorp  (file-line)
         line 75: For more information on how to configure the plugin, please read the
[PASS] tart-licensing-page-exists  (doc-index)
[PASS] tart-free-tier-100-cores-4-workers  (doc-contains)
[PASS] tart-gold-tier-costs-12000  (doc-contains)
[PASS] tart-gold-tier-limits-500-cores-20-workers  (doc-contains)
[PASS] tart-platinum-tier-costs-36000  (doc-contains)
[PASS] tart-platinum-tier-limits-3000-cores-200-workers  (doc-contains)
[PASS] tart-diamond-tier-12-per-core-per-year  (doc-contains)
[PASS] tart-all-cores-counted-toward-license  (doc-contains)
[PASS] tart-licensing-contact-is-cirruslabs  (doc-contains)
[PASS] CONTROL-licensing-page-never-says-commercial-use-free  (doc-contains)
[PASS] CONTROL-tart-blog-is-outside-doc-index-domain  (doc-index)
[PASS] tart-2025-enforcement-press-release-is-live  (http-contains)
[PASS] tart-2025-enforcement-names-competing-product  (cli-help)
[PASS] tart-2023-post-defines-server-installation  (cli-help)
[PASS] tart-2023-post-hdmi-dummy-plug-example  (cli-help)
[PASS] tart-2023-post-royalty-free-not-agpl  (cli-help)
[PASS] cirruslabs-tart-redirects-to-openai-tart  (cli-help)
[PASS] openai-tart-license-is-fsl-1-1-alv2  (cli-help)
[PASS] openai-tart-license-copyright-is-openai  (cli-help)
[PASS] openai-tart-license-grants-apache-2-future  (cli-help)
[PASS] orchard-orchestrates-multiple-tart-hosts  (doc-contains)
[PASS] orchard-controller-proxies-secure-connection-to-workers  (doc-contains)
[PASS] orchard-default-license-allows-4-workers  (doc-contains)
[PASS] orchard-gold-tier-raises-limit-to-20-workers  (doc-contains)
[PASS] orchard-platinum-tier-raises-limit-to-200-workers  (doc-contains)
[PASS] cirrus-cli-page-copies-working-directory  (doc-contains)
[PASS] cirrus-run-dirty-copies-unless-mounted  (cli-help)
[PASS] cirrus-worker-run-has-pool-registration-token  (cli-help)
[PASS] cirrus-cli-page-restricts-cloud-images  (doc-contains)
[PASS] cirrus-cli-page-says-cirrus-ci-uses-tart  (doc-contains)
[PASS] no-terraform-provider-at-cirruslabs-tart  (cli-help)
[PASS] no-terraform-provider-at-cirruslabs-orchard  (cli-help)
[PASS] vanilla-tahoe-ssh-password-is-plain-admin-at-line-20  (file-line)
         line 20: ssh_password = "admin"
[PASS] vanilla-tahoe-ssh-username-is-plain-admin-at-line-21  (file-line)
         line 21: ssh_username = "admin"
[PASS] utm-apple-backend-no-multiple-displays  (doc-contains)
[PASS] utm-rosetta-is-for-linux-guests-only  (doc-contains)
[PASS] utm-apple-serial-is-ptty-only  (doc-contains)
[PASS] utm-trackpad-requires-ventura-guest  (doc-contains)
[PASS] utm-apple-backend-is-only-way-to-run-macos  (doc-contains)
[PASS] utm-apple-backend-less-mature-than-qemu  (doc-contains)
[PASS] utm-no-tso-toggle-on-apple-virtualization  (doc-contains)
[PASS] CONTROL-utm-apple-virtualization-page-has-toggles  (doc-contains)
[PASS] utm-tso-apple-equivalent-is-asserted  (doc-contains)
[PASS] utm-settings-qemu-devices-page-exists  (doc-index)
[PASS] utm-settings-qemu-drive-page-exists  (doc-index)
[PASS] utm-guest-support-sharing-page-exists  (doc-index)
[PASS] utm-real-devices-page-exists  (doc-index)
[PASS] utm-apple-devices-serial-child-exists  (doc-index)
[PASS] utm-virtiofs-mount-command  (doc-contains)
[PASS] utm-clipboard-uses-spice-vdagent-not-guest-agent  (doc-contains)
[PASS] utm-recovery-mode-disables-sip  (doc-contains)
[PASS] utm-apple-drive-has-sparse-image-format  (doc-contains)
[PASS] utmctl-file-help-admits-guest-agent  (cli-help)
[PASS] utmctl-usb-help-lists-connect  (cli-help)
[PASS] utmctl-start-help-lists-recovery  (cli-help)
[PASS] utmctl-delete-help-says-no-confirmation  (cli-help)
[PASS] utmctl-attach-help-has-index  (cli-help)
[PASS] utmctl-usb-group-has-no-debug-flag  (cli-help)
[PASS] CONTROL-utmctl-usb-help-prints-subcommands  (cli-help)
[PASS] utmctl-usb-leaf-does-have-debug-flag  (cli-help)
[PASS] utm-app-version-is-4-7-5  (file-contains)
[PASS] xaudit-08-tart-clone-syntax  (cli-help)
[PASS] xaudit-08-tart-run-no-graphics  (cli-help)
[PASS] xaudit-08-tart-dir-is-not-a-global-flag  (cli-help)
[PASS] CONTROL-xaudit-08-tart-help-prints-globals  (cli-help)
[PASS] xaudit-08-tart-dir-automounts-to-shared-files  (cli-help)
[PASS] xaudit-08-tart-dir-requires-ventura-guest  (cli-help)
[PASS] xaudit-08-tart-dir-automount-documented  (doc-contains)
[PASS] xaudit-08-tart-exec-requires-guest-agent  (cli-help)
[PASS] prereq-installer-brew-asdf-line-578  (file-line)
         line 578: brew install bossjones/asdf-versions/asdf@0.11.2 || true
[PASS] prereq-installer-clones-asdf-line-753  (file-line)
         line 753: git clone --verbose https://github.com/asdf-vm/asdf.git ~/.asdf --bran
[PASS] prereq-installer-installs-retry-line-589  (file-line)
         line 589: brew install kadwanev/brew/retry || true
[PASS] install-sh-brew-guard-line-206  (file-line)
         line 206: if ! command -v brew >/dev/null 2>&1; then
[PASS] install-sh-brew-guard-exits-line-209  (file-line)
         line 209: exit 1
[PASS] asdf-plugins-macos-skips-when-asdf-absent  (file-line)
         line 32: echo "asdf not available - skipping asdf plugin install"
[PASS] chezmoiignore-else-branch-line-11  (file-line)
         line 11: {{ else -}}
[PASS] no-xcode-select-in-zsh-dotfiles-tracked  (cli-help)
[PASS] CONTROL-git-grep-o-emits-matched-text  (cli-help)
[PASS] no-ansible-in-zsh-dotfiles-tracked  (cli-help)
[PASS] ansible-in-prep-brewfile-line-57  (file-line)
         line 57: brew "ansible"
[PASS] ansible-in-prep-brewfile-line-602  (file-line)
         line 602: vscode "redhat.ansible"
[PASS] prep-repo-has-no-ansible-playbook  (cli-help)
[PASS] CONTROL-prep-grep-o-i-emits-matched-text  (cli-help)
[PASS] smoke-brew-prereq-list-line-142  (file-line)
         line 142: brew install wget curl kadwanev/brew/retry go || true
[PASS] smoke-brew-prereq-list-line-143  (file-line)
         line 143: brew install openssl@3 readline libyaml gmp autoconf tmux || true
[PASS] smoke-test-never-mentions-trash  (absent)
[PASS] smoke-retry-wrapper-is-conditional-line-360  (file-line)
         line 360: if command -v retry &> /dev/null; then
[PASS] smoke-retry-apply-line-361  (file-line)
         line 361: retry -t 4 -- "$chezmoi_bin" init -R --debug -v --apply --force \
[PASS] smoke-promptstring-line-362  (file-line)
         line 362: --promptString version_manager="$VERSION_MANAGER" --source=. || chezmo
[PASS] smoke-mise-lane-never-sources-asdf-line-245  (file-line)
         line 245: if [[ "$VERSION_MANAGER" == "asdf" ]]; then
[PASS] quickstart-does-not-cite-prereq-installer  (absent)
[PASS] quickstart-line-10-curls-install-sh  (file-line)
         line 10: curl -fsSL https://raw.githubusercontent.com/bossjones/zsh-dotfiles-pr
[PASS] prereq-installer-next-steps-line-1135  (file-line)
         line 1135: logn 'You are ready to run zsh-dotfiles. Run: chezmoi init -R --debug 
[PASS] prereq-installer-pins-chezmoi-2-31-1-line-1132  (file-line)
         line 1132: sh -cx "$(curl -fsLS get.chezmoi.io)" -- -b "$HOME"/.bin -t v2.31.1
[PASS] prep-makefile-has-no-smoke-target  (absent)
[PASS] sheldon-installed-is-the-pinned-0-6-6  (cli-help)
[PASS] sheldon-lock-has-no-check-flag  (cli-help)
[PASS] CONTROL-sheldon-lock-help-prints-reinstall  (cli-help)
[PASS] sheldon-lock-is-mutating  (cli-help)
[PASS] justfile-has-build-golden  (file-contains)
[PASS] justfile-has-no-images-recipe  (absent)
[PASS] justfile-check-is-the-gate  (file-contains)
[PASS] test-dotfiles-tmux-prompt-test-is-skipped  (file-line)
         line 245: @pytest.mark.skip(reason="These tests are meant to only run locally on
[PASS] test-dotfiles-tmux-spawns-zsh-f  (file-line)
         line 254: tmux_fake_session.new_window(attach=True, window_name="test_pure_promp
[PASS] tart-licensing-free-tier-worked-example-96-cores  (doc-contains)
[PASS] tart-licensing-free-tier-counterexample-104-cores  (doc-contains)
[PASS] tart-index-does-carry-blog-shell-pages  (doc-index)
[PASS] d2-spec12-no-longer-documents-build-recipe  (absent)
[PASS] oq02-vnc-marker-exists-regardless-of-line  (file-contains)
[PASS] packer-sensitive-masks-by-value-not-variable  (cli-help)
[PASS] CONTROL-packer-inspect-var-flag-assigns-plain-value  (cli-help)
[PASS] packer-sensitive-masks-substring-inside-larger-value  (cli-help)
[PASS] CONTROL-packer-log-env-overlay-is-effective  (cli-help)
[PASS] packer-debug-log-silent-when-overlay-disabled  (cli-help)
[PASS] CONTROL-packer-log-disabled-still-prints-plain-literals  (cli-help)
[PASS] packer-shell-use-env-var-file-uploads-into-guest  (cli-help)
[PASS] packer-shell-guest-cleanup-is-an-unlink  (cli-help)
[PASS] golden-template-does-not-exist  (cli-help)
[PASS] tart-faq-documents-vms-directory  (doc-contains)
[PASS] CONTROL-tart-faq-does-not-name-the-disk-file  (doc-contains)
[PASS] tart-builder-disk-format-defaults-to-raw  (file-contains)
[PASS] tart-builder-passes-disk-format-only-on-create-path  (file-contains)
[PASS] CONTROL-tart-builder-clone-step-ignores-disk-format  (absent)
[PASS] no-ansible-uppercase-in-zsh-dotfiles-tracked  (cli-help)
[PASS] prep-repo-has-no-become-key  (cli-help)
[PASS] CONTROL-git-grep-o-i-emits-matched-text  (cli-help)
[PASS] CONTROL-prep-makefile-has-a-style-target  (file-contains)
[PASS] xaudit-09-ignore-file-does-contain-macos-install-asdf  (file-contains)
[PASS] CONTROL-xaudit-scripts-dir-lists-macos-mise-installer  (cli-help)
[PASS] CONTROL-xaudit-scripts-dir-lists-ubuntu-asdf-installer  (cli-help)
[PASS] xaudit-09-no-macos-asdf-installer-script-on-disk  (cli-help)
[PASS] verifier-missing-file-emits-unreachable  (cli-help)
[PASS] verifier-missing-file-is-not-inverted-into-a-pass  (cli-help)
[PASS] verifier-mustfail-inverts-a-plain-failure  (cli-help)
[PASS] verifier-rejects-an-uncontrolled-negative  (cli-help)
[PASS] verifier-uncontrolled-negative-never-reaches-evaluation  (cli-help)
[PASS] verifier-accepts-a-wellformed-pair  (cli-help)
[PASS] CONTROL-verifier-oracle-fixture-executes  (cli-help)
[PASS] verifier-exempts-oracle-control-from-structural-check  (cli-help)
[PASS] CONTROL-terraform-registry-serves-a-known-provider  (cli-help)
[PASS] sheldon-help-has-no-verify-subcommand  (cli-help)
[PASS] CONTROL-sheldon-help-lists-lock-subcommand  (cli-help)
[PASS] dotfiles-mise-script-short-circuits-on-existing-mise  (file-line)
         line 9: command -v mise >/dev/null 2>&1 || brew install mise || true
[PASS] vanilla-image-preinstalls-no-software  (file-line)
         line 8: * `macos-{tahoe,sequoia,sonoma}-vanilla` — a vanilla macOS installatio
[PASS] base-image-is-derived-from-vanilla  (file-line)
         line 9: * `macos-{tahoe,sequoia,sonoma}-base` — based on `macos-{tahoe,sequoia
[PASS] vanilla-sequoia-template-installs-no-mise  (absent)
[PASS] CONTROL-vanilla-sequoia-template-is-a-tart-cli-build  (file-contains)
[PASS] packer-shell-provisioner-source-is-tag-pinned  (http-status)
[PASS] tart-help-lists-create-subcommand  (cli-help)
[PASS] xaudit-01-table-lists-create-verb  (file-contains)
[PASS] tart-run-help-has-no-graphics-flag  (cli-help)
[PASS] tart-prune-space-budget-is-a-size-budget  (cli-help)
[PASS] spec12-mentions-vnc-port-min  (file-contains)
[PASS] spec12-vnc-port-mention-line-pin  (file-line)
         line 354: `boot_command` over exactly this channel — hence its `disable_vnc` and
[PASS] CONTROL-spec12-line-330-is-not-the-vnc-port-mention  (file-line)
[PASS] tart-faq-keychain-requirement-attaches-to-the-tart-process  (doc-contains)
[PASS] tart-faq-autologin-mitigation-is-a-host-mac-user-account  (doc-contains)
[PASS] vanilla-tahoe-has-passwordless-sudo  (file-contains)
[PASS] vanilla-tahoe-presets-autologin-user  (file-contains)
[PASS] synth-packer-shell-page-documents-skip-clean-default  (cli-help)
[PASS] synth-tart-licensing-says-4-hosts-for-orchard  (doc-contains)
[PASS] synth-00-overview-credits-13-to-secrets  (file-line)
         line 58: | 13 | `13-build-secrets.md` | secrets | Injecting `HOMEBREW_GITHUB_AP
[PASS] synth-00-overview-grades-match-11-sources  (file-line)
         line 56: | 11 | `11-sources.md` | synth | Every source URL, grouped, graded mea
[PASS] synth-07-appendix-declares-no-dead-links  (file-contains)
[PASS] synth-packer-version-is-1-15-4  (cli-help)
[PASS] synth-justfile-has-no-doctor-recipe  (absent)
[PASS] synth-openai-tart-license-is-fsl-1-1  (http-contains)
[PASS] synth-fsl-text-never-mentions-cores  (http-contains)
[PASS] synth-tart-licensing-page-never-mentions-openai  (doc-contains)
[PASS] synth-grep-over-cirruslabs-clones-emits-real-paths  (cli-help)
[PASS] synth-packer-plugin-clone-free-of-fixture-sentinel  (cli-help)
[PASS] CONTROL-packer-debug-log-stderr-emits-info-banner  (cli-help)
[PASS] CONTROL-packer-debug-log-stderr-prints-plain-literal  (cli-help)
[PASS] packer-sensitive-hides-secret-in-isolated-debug-log  (cli-help)
[PASS] packer-no-debug-log-on-stderr-when-overlay-disabled  (cli-help)
[PASS] packer-log-value-off-still-enables-logging  (cli-help)
[PASS] packer-shell-use-env-var-file-has-no-default-assignment  (cli-help)
[PASS] packer-shell-varfile-is-chmod-0600-in-guest  (cli-help)
[PASS] justfile-verify-no-secrets-starts-at-line-60  (file-line)
         line 60: verify-no-secrets vm:
[PASS] secrets-13-marker-51-still-present  (file-line)
         line 51: <!-- UNVERIFIED: reproduced on the host against a UDIF/APFS image via 
[PASS] secrets-13-marker-54-still-present  (file-line)
         line 54: <!-- UNVERIFIED: whether the same holds for `disk_format = "asif"` (ma
[PASS] cirruslabs-org-is-live  (http-status)
[PASS] cirruslabs-org-announces-openai-acquisition  (http-contains)
[PASS] cirruslabs-org-announcement-dated-april-7-2026  (http-contains)
[PASS] openai-tart-license-copyright-notice-via-http  (http-contains)
[PASS] fsl-text-mentions-no-cpu-cores  (http-contains)
[PASS] tart-licensing-page-never-mentions-openai  (http-contains)
[PASS] tart-licensing-page-still-says-free-tier  (http-contains)
[PASS] tart-licensing-page-still-lists-cirruslabs-contact  (http-contains)
[PASS] terraform-registry-serves-a-real-provider  (cli-help)
[PASS] xaudit-12-no-build-ipsw-recipe  (cli-help)
[PASS] xaudit-12-no-images-recipe  (cli-help)
[PASS] CONTROL-xaudit-just-summary-lists-build-golden  (cli-help)
[PASS] xaudit-09-git-grep-fatal-line-contains-a-colon  (cli-help)
[PASS] g4-enforcement-press-release-returns-200  (http-status)
[PASS] packer-shell-uploads-the-varfile-into-the-guest  (http-contains)
[PASS] packer-shell-cleans-the-varfile-with-an-unlink  (http-contains)
[PASS] justfile-build-golden-guards-on-missing-template  (file-line)
         line 46: @test -f packer/tart-golden-image.pkr.hcl || { \
[PASS] justfile-build-golden-guard-exits-4  (file-line)
         line 49: exit 4; }
[PASS] synth-sitemap-substring-packer-also-matches-hcp-packer  (cli-help)

305/305 claims verified
🕵️  <!-- UNVERIFIED --> markers by file:
specs/macos-ci/07-utm-settings-appendix.md:25:| [qemu](https://docs.getutm.app/settings-qemu/qemu/) | Logging, UEFI boot, RNG ("entropy") device, balloon device, TPM 2.0, hypervisor/TSO toggles, PS/2 fallback, UEFI variable reset, raw QEMU machine properties/arguments | Inside the `Use TSO` bullet, verbatim: "This option is not supported on macOS however when using the Apple virtualization backend, **a similar option is available**." UTM thus asserts the Apple-backend equivalent **exists**, then never names it. No page in the 78-page index documents it: [settings-apple/virtualization](https://docs.getutm.app/settings-apple/virtualization/) publishes its own complete section list (8 toggles: balloon, entropy, sound, keyboard, pointer, trackpad, Rosetta, clipboard) and TSO is not among them <!-- UNVERIFIED: the page's silence is proven (ledger: utm-no-tso-toggle-on-apple-virtualization, a must_fail probe with a positive control). Inferring from that silence that no such toggle EXISTS is inference from absence, and stays unverified. See OQ-10 --> |
specs/macos-ci/12-tooling-and-agent-loop.md:364:<!-- UNVERIFIED: `--vnc-experimental` is labelled experimental by Tart itself, and the exact stdout
specs/macos-ci/04-tart-licensing-risk.md:186:<!-- UNVERIFIED: who would ENFORCE the Fair Source terms post-acquisition, and whether
specs/macos-ci/13-build-secrets.md:51:<!-- UNVERIFIED: reproduced on the host against a UDIF/APFS image via hdiutil, not inside a tart VM
specs/macos-ci/13-build-secrets.md:54:<!-- UNVERIFIED: whether the same holds for `disk_format = "asif"` (macOS 26+), a sparse format
specs/macos-ci/02-packer-tart-builder.md:135:> <!-- UNVERIFIED: whether `tart run --graphics` parses on tart 2.32.1; settling it requires invoking `tart run`, which scope forbids. See OQ-15. -->
specs/macos-ci/02-packer-tart-builder.md:207:<!-- UNVERIFIED: composed example combining documented fields; not a block quoted verbatim from either source. -->
specs/macos-ci/05-utm-automation.md:115:macOS guest is <!-- UNVERIFIED: docs are silent, not permissive; settling it needs a booted guest. See
specs/macos-ci/05-utm-automation.md:415:| Scripted keystrokes / mouse clicks | **No** (AppleScript path) / <!-- UNVERIFIED: the `utm://` path carries no documented backend restriction either way. See OQ-09 --> (`utm://` path) | — (no CLI verb) | Input Automation Suite is QEMU-only (§2.6) |
specs/macos-ci/03-tart-ci-and-orchard.md:61:  <!-- UNVERIFIED: the copy TRANSPORT (rsync vs tart's --dir mount) is named by no source. `cirrus run
specs/macos-ci/03-tart-ci-and-orchard.md:176:   <!-- UNVERIFIED: whether a persistent worker may run a CUSTOM (non-Cirrus-managed) tart image under
specs/macos-ci/06-utm-macos-guest.md:78:<!-- UNVERIFIED: undocumented, not impossible; proving persistence needs a guest reboot. See OQ-11 --> and,
specs/macos-ci/08-dotfiles-test-harness.md:99:   <!-- UNVERIFIED: exact `tart clone` syntax — cross-check against 01-tart-core.md's verified CLI
specs/macos-ci/08-dotfiles-test-harness.md:134:   <!-- UNVERIFIED: exact headless-run flag spelling — cross-check against 01-tart-core.md's
specs/macos-ci/08-dotfiles-test-harness.md:141:   <!-- UNVERIFIED: exact `--dir` mount syntax — cross-check against 01-tart-core.md. -->
```

---

## Baseline → DONE

| Metric | SCAFFOLD | DONE |
|---|---|---|
| `just check` exit | 0 | **0** |
| Claims | 50 / 50 | **246 / 246** |
| `must_fail` | 6 | **27** (none deleted or weakened) |
| `[FAIL]` | 0 | **0** |
| Links | 250 | **275**, all `[200]` |
| Markers | 16 | **15** (−1, paid for) |
| Duplicate evidence groups | — | **0** |
| Unguarded negative records | (unchecked) | **0** |
| Claims that execute the verifier | **0** | **8** |
| Open questions | 0 | **37** (10 `NEEDS-HUMAN`) |

---

## GATE-BLOCKERS — five, all closed

| | Finding | Close |
|---|---|---|
| **GB1** | `CONTROL-git-grep-c-emits-colon-when-present` **vacuous**: `expect ":"`, and git's `fatal: … : No such file` has a colon — it passed **against a repo that does not exist** | all `":"` literals retired |
| **GB2** | Brief's `must_fail` JOB 2 demands a same-`argv` control, but for a `grep -c` probe a true negative implies **empty output** — a logical impossibility | **brief retracted** |
| **GB3** | `CONTROL-12-line-607-does-not-exist` fired on **any** unrelated `UNVERIFIED` at line 607 — a false *"the oracle is broken"* | `expect` narrowed to the specific marker |
| **GB4** | `absent` had **no control requirement**; and at `HEAD` a `must_fail` control whose **target file was deleted went GREEN** | enforced in the tool, exit `4` |
| **GB5** | The GB4 fix exempted the **kind** instead of the **oracle records**, leaving one negative `doc-contains` probe guarded only by prose | exemption narrowed; `needs_control()` |

**The pattern is the finding.** Each round the hole moved **one level up the abstraction**. GB2 scoped the rule
too narrowly; GB4 fixed the rule and scoped its *exemption* too broadly; GB5 scoped the exemption to records
that genuinely have no partner. **Every exemption clause is where enforcement stops and prose resumes.**

> The invariant is not *"negatives need controls."* It is: **every claim satisfiable by the absence of
> evidence must name the positive claim that proves the probe can see.** It now lives in
> `tools/verify_claims.py`, not in a paragraph.

---

## The verifier is now verified BY the verifier (OQ-35)

Its three trust-bearing behaviours were, until the final hour, asserted by **grepping its own source** and by
the lead's **hand-testing written up as prose** — Defect A's evidence class, differing only in the honesty of
the transcriber. **Honesty is not an evidence kind.** Eight `cli-help` claims now execute the tool against
checked-in fixtures in `tests/fixtures/verifier/`, every negative carrying its positive control on the same
`argv`:

```
verifier-missing-file-emits-unreachable                  UNREACHABLE: missing file:
verifier-missing-file-is-not-inverted-into-a-pass        (control: ^)
verifier-mustfail-inverts-a-plain-failure                1/1 claims verified
verifier-rejects-an-uncontrolled-negative                STRUCTURAL REJECTION — negative evidence without a positive control
verifier-uncontrolled-negative-never-reaches-evaluation  (control: ^)
verifier-accepts-a-wellformed-pair                       2/2 claims verified
CONTROL-verifier-oracle-fixture-executes                 CONTROL-oracle-with-no-partner
verifier-exempts-oracle-control-from-structural-check    (control: ^)
```

---

## The one marker that vanished — audited, not assumed

`01-tart-core.md:68`. Retired against **two passing claims**: `tart-quickstart-lists-sequoia-xcode-image`
(whose prose reads *"RETIRES the marker formerly at 01:68"*) and `tart-quickstart-lists-monterey-xcode-15` —
added because tart-core's *replacement prose* cited a **different image with a numeric tag** than its claim
pinned. The gap between a retired marker and its replacement sentence was itself found and closed.
**Not a silent paydown.** The only `UNVERIFIED` left in `01` is the backticked prose mention at `:222`.

---

## Retractions — the whole point of the run

| ID | Verdict |
|---|---|
| **G10** | 🔴 RETRACTED (pre-existing) — `settings-apple/devices/` **fabricated**; *"do not fetch"* prevented its disproof. |
| **G14** | 🔴 RETRACTED — the **prompt** was wrong: `packer` **is** installed (1.15.4); no `just doctor` recipe. The ledger already held the disproof. |
| **D5** | 🔴 RETRACTED → **D5′** — its "fix" was a **no-op** (22→22); its enumeration missed `specs/macos-ci.md:517`. Baseline **16**, not 17. |
| **G13** | 🔴 PARTIAL — `vnc_port_min` / `vnc_port_max` **do not exist**. |
| **G9** | 🟡 METHOD RETRACTED — *"prove it with an `absent` claim"* would **fail**: `ansible` **is** in prep's Brewfile. Survives only as *"neither repo is **provisioned by** Ansible."* |
| **Brief · `must_fail` JOB 2** | 🔴 RETRACTED in three rounds (GB2/GB4/GB5) — a property of **all** negative evidence. |
| **Brief · STATUS BOARD** | 🔴 RETRACTED (Defect F) — bare `cmux rename-tab` errors; `$CMUX_TAB_ID` holds a **workspace** UUID. |
| **Addendum · R2** | 🟡 RESOLVED (Defect G) — false dichotomy: `notify` emits **both** names; payload **redacted**. |
| **G19** | 🟢 UPHELD — absent from the sitemap, returns **200**. Never refute a page you have not fetched. |
| **G4** | 🟢 UPHELD — licence figures **unchanged** against `tart.run/licensing`. |
| **G14′, G1–G3, G5–G8, G11, G12, G15–G18** | 🟢 upheld / attacked and survived. |

### Prior-lead defects (Haiku pass) and the lead's own

| | |
|---|---|
| **A** | The board **faked the gate**: `[output: all links checked, 50/50 claims verified]`. |
| **B** | OQ-02 cited `12-…:607` in a **535-line** file. Then — *after* correction — the file grew to 577 and the marker moved `:340 → :359`, **invalidating the lead's own fix inside the same run**. Ledger caught it by *executing*. |
| **C** | Board roster pointed at a **torn-down workspace** (`pane:34–41`). |
| **E** | The backlog **claimed a dispatch that never happened**; every worker sat at a pristine prompt. |
| **D, H** | The **lead** cited a line number from memory (236 → really 87/218) and ran a negative probe with no control. Caught by execution. |

---

## Roster

| Role | Pane | Surface | Final |
|---|---|---|---|
| 👑 lead | `pane:42` | `6D646A29…` | GATE ✅ |
| 🔬 ledger | `pane:43` | `A6FE02F9…` | 246/246 · tool verified by tool |
| 🍎 tart-core | `pane:44` | `C74E75F0…` | 44 claims · G13 refuted |
| 🏭 tart-ci | `pane:45` | `258F06DE…` | 34 claims · G4 unchanged · 1 fabricated quote retracted |
| 🖥 utm | `pane:46` | `04FF0E1E…` | 44/44 · found the `absent` hole (OQ-27) |
| 🧪 harness | `pane:47` | `1DD2FCB0…` | 43 claims · 10 refuted |
| 🔐 secrets | `pane:48` | `F63FA6BD…` | G15/16/17 upheld · `PACKER_LOG` control under-powered |
| 📚 synth | `pane:49` | `586DD0B7…` | ledger verdict + OQ-33/34/35 |

Rotation (7-node derangement) — **all seven edges closed.**
