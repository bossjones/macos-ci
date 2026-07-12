# Tutorials

Hands-on, step-by-step guides for using this repo. Written assuming no prior familiarity with Tart,
Packer, or UTM — each concept is introduced briefly inline, with links out to [../../specs/](../../specs/)
for anyone who wants the full design rationale rather than a re-explanation here.

Read them roughly in order if you're new to the repo; each one links to the specific [../architecture/](../architecture/) reference page it draws commands from.

| # | Tutorial | What you'll do |
|---|---|---|
| 1 | [Getting started](01-getting-started.md) | Install prerequisites, run `just doctor`, and complete a first end-to-end `just run`. |
| 2 | [Running the harness](02-running-the-harness.md) | Drive the VM lifecycle directly (`up`/`apply`/`down`/etc.), use seed configs, and iterate quickly against a live VM. |
| 3 | [Building the golden image](03-building-the-golden-image.md) | Build the base golden image with Packer and run the post-build secrets leak-canary. |
| 4 | [Verifying the truth gate](04-verifying-the-truth-gate.md) | Understand `just check` — the spec/claims verification system, distinct from VM testing. |
| 5 | [Debugging a failed run](05-debugging-a-failed-run.md) | Triage a failed or stuck run using `just status`, `just logs`, and `vm-debug sweep`. |
| 6 | [Testing a dotfiles PR branch in the UTM lane](06-utm-testing-a-pr-branch.md) | Boot a windowed guest, apply a pushed branch from GitHub with all prompts pre-answered, verify visually in iTerm2, and capture the screenshot host-side. |

A few Justfile recipes referenced elsewhere in this repo's docs (`just vnc`, `just shot`, `just logs`) are
currently broken or stubbed against the real CLI — tutorial 5 and [../architecture/cli-reference.md](../architecture/cli-reference.md) call these out explicitly rather than presenting them as working.

See also: [../architecture/](../architecture/) for reference material, and [../contributor/](../contributor/) for how this repo's own implementation was built via multi-agent orchestration.
