// Fixture for the claims ledger, not for building anything.
//
// `packer inspect` on this directory needs no plugins, no stdin, and exits 0.
// Four ledger claims probe it:
//
//   - `<sensitive>` appears            -> masking is on
//   - `ghp_FIXTURE_SENTINEL` absent    -> the secret never prints  (must_fail)
//   - `plain_FIXTURE_CONTROL` appears  -> control: inspect DOES print plain literals,
//                                         so the must_fail claim above is not vacuous
//   - the same, under PACKER_LOG=1     -> masking survives debug logging
//
// Without the control, "the secret didn't print" would also be satisfied by
// `packer inspect` printing nothing at all.

variable "sec" {
  type      = string
  sensitive = true
  default   = "ghp_FIXTURE_SENTINEL"
}

variable "pub" {
  type    = string
  default = "plain_FIXTURE_CONTROL"
}
