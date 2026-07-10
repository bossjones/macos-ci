# 📡 LOGWATCH — team macos-ci-build

Append-only. Owned exclusively by 📡 log-watcher. Terminal outcome is confirmed from the log tail's own
exit banner or a background-job wait — never from `read-screen` on the 🏗 build pane.

---

## 2026-07-10T18:17:52Z — LOGWATCH ARMED

Armed on `logs/packer-build-20260710-141058.log` per lead's BUILD-LAUNCH confirmation. Log file exists
(495B at arm time), build in progress: `tart-cli.golden` cloning golden VM, pulling disk (23.7 GB
compressed), currently at ~5%. Tailing now.

- 2026-07-10T18:18:36Z [pull] [1;32m==> tart-cli.golden: Cloning virtual machine...[0m
- 2026-07-10T18:18:36Z [pull] [1;32m==> tart-cli.golden: pulling manifest...[0m
- 2026-07-10T18:18:36Z [pull] [1;32m==> tart-cli.golden: pulling disk (23.7 GB compressed)...[0m
- 2026-07-10T18:20:07Z [pull] [1;32m==> tart-cli.golden: Error pulling disk layer 9: "The network connection was lost.", attempting to re-try...[0m
- 2026-07-10T18:25:03Z [pull] [1;32m==> tart-cli.golden: Error pulling disk layer 12: "The network connection was lost.", attempting to re-try...[0m
- 2026-07-10T18:25:04Z [pull] [1;32m==> tart-cli.golden: Error pulling disk layer 11: "The network connection was lost.", attempting to re-try...[0m
