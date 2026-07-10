# Documentation

This is the documentation tree for `macos-ci` — a Packer/Tart-based disposable macOS CI harness that
installs [zsh-dotfiles](https://github.com/bossjones/zsh-dotfiles) into a clean macOS VM guest and asserts
the install worked.

If you're looking for *why* this repo is built the way it is (Tart vs. UTM, licensing risk, the harness
design), start at [../specs/](../specs/) instead — that tree is the authoritative source of design
rationale. This tree (`docs/`) covers *using* the repo, *what the current code actually does*, and *how
its own development was orchestrated*.

| Folder | For | Start here |
|---|---|---|
| [tutorials/](tutorials/) | Using the repo, step by step | [tutorials/01-getting-started.md](tutorials/01-getting-started.md) |
| [architecture/](architecture/) | Understanding what exists and how it fits together | [architecture/repo-structure.md](architecture/repo-structure.md) |
| [contributor/](contributor/) | Contributing to `macos-ci` itself, including via multi-agent orchestration | [contributor/boss-cmux-workflow.md](contributor/boss-cmux-workflow.md) |

## Quick links

- New to the repo? → [tutorials/01-getting-started.md](tutorials/01-getting-started.md)
- Want the full CLI/Justfile command surface? → [architecture/cli-reference.md](architecture/cli-reference.md), [architecture/justfile-reference.md](architecture/justfile-reference.md)
- Want to know how the golden image gets built? → [architecture/build-pipeline.md](architecture/build-pipeline.md)
- Want to understand the design decisions behind Tart vs. UTM? → [../specs/macos-ci/10-tart-vs-utm-adr.md](../specs/macos-ci/10-tart-vs-utm-adr.md)
- Want to run or extend a multi-agent build against this repo? → [contributor/boss-cmux-workflow.md](contributor/boss-cmux-workflow.md), [contributor/team-coordination-mechanics.md](contributor/team-coordination-mechanics.md)

## A note on accuracy

Every page in this tree is grounded in the checked-in code as of this writing, not inference — where a
Justfile recipe or CLI command doesn't currently work as documented elsewhere (e.g. a stub, a
not-yet-implemented recipe), the relevant page says so explicitly rather than presenting it as working.
This matches the rest of the repo's own convention (see [../CLAUDE.md](../CLAUDE.md) §"Conventions"):
prefer a shorter, entirely true document over a longer one padded with plausible detail.
