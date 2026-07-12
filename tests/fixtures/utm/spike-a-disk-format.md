# Spike A finding — golden disk format (2026-07-10)

Host: this dev machine. VM: `dotfiles-golden` (`~/.tart/vms/dotfiles-golden/`).

- `config.json` disk fields: `{"os": "darwin", "diskFormat": "raw", "arch": "arm64"}`
- `file disk.img`: `DOS/MBR boot sector; partition 1 : ID=0xee, ... extended partition table (last)`
  — i.e. a GPT-protective-MBR raw disk image, not ASIF.

Conclusion: the tart golden disk is **already raw**. No ASIF→raw conversion path is needed;
`diskutil image convert` remains untried and is no longer a live risk to hedge (delete the hedge,
not the marker for the actually-untried GUI-import boot step).
