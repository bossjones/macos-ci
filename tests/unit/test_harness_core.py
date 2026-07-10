from macos_ci._harness_core import (  # noqa: PLC2701
    RunArtifactPaths,
    _TOOLCHAIN_PATH_EXPORT,
    artifact_paths,
    bootstrap_ssh_argv,
    chezmoi_argv,
    chezmoi_identity_env,
    chezmoi_init_only_argv,
    clone_name,
    format_run_id,
    steady_state_ssh_argv,
)


def test_chezmoi_init_only_argv_has_no_apply_or_force_flags():
    # OQ-08: this is the pre-diff config-generation step -- it must never touch the destination.
    argv = chezmoi_init_only_argv(
        source="/Volumes/My Shared Files/dotfiles", version_manager="mise"
    )
    assert argv == [
        "chezmoi",
        "init",
        "--promptString",
        "version_manager=mise",
        "--source=/Volumes/My Shared Files/dotfiles",
    ]
    assert "--apply" not in argv
    assert "--force" not in argv


def test_chezmoi_argv_matches_smoke_test_docker_verbatim():
    # zsh-dotfiles/scripts/smoke-test-docker.sh:361-365, --source pointed at the tart --dir mount
    # instead of a local checkout (spec 08 §"The run, composed from tart primitives" step 4).
    assert chezmoi_argv(source="/Volumes/My Shared Files/dotfiles") == [
        "chezmoi",
        "init",
        "-R",
        "--debug",
        "-v",
        "--apply",
        "--force",
        "--promptString",
        "version_manager=mise",
        "--source=/Volumes/My Shared Files/dotfiles",
    ]


def test_chezmoi_argv_parameterized_on_version_manager():
    argv = chezmoi_argv(source=".", version_manager="asdf")
    assert "version_manager=asdf" in argv
    assert "version_manager=mise" not in argv


def test_chezmoi_argv_does_not_include_the_retry_wrapper():
    # `retry -t 4 --` is harness.py's job (spec 08 step 4) -- _harness_core stays pure and only
    # builds the chezmoi invocation itself.
    argv = chezmoi_argv(source=".")
    assert argv[0] == "chezmoi"
    assert "retry" not in argv


def test_format_run_id_is_deterministic_given_explicit_inputs():
    assert format_run_id(timestamp="20260710-181234", suffix="ab12cd") == "20260710-181234-ab12cd"


def test_clone_name_matches_spec_08_naming():
    # spec 08 §"The run, composed from tart primitives": "dotfiles-test-<run-id>"
    assert clone_name("20260710-181234-ab12cd") == "dotfiles-test-20260710-181234-ab12cd"


def test_chezmoi_identity_env_sets_computer_name_and_hostname():
    # spec 08 step 6: CM_computer_name / CM_hostname, unconditional env-var fields.
    env = chezmoi_identity_env("20260710-181234-ab12cd")
    assert env == {
        "CM_computer_name": "20260710-181234-ab12cd",
        "CM_hostname": "20260710-181234-ab12cd",
    }


def test_artifact_paths_layout_matches_spec_12_contract():
    paths = artifact_paths("20260710-181234-ab12cd")
    assert isinstance(paths, RunArtifactPaths)
    assert paths.root == "artifacts/20260710-181234-ab12cd"
    assert paths.state == "artifacts/20260710-181234-ab12cd/state.json"
    assert paths.doctor == "artifacts/20260710-181234-ab12cd/doctor.json"
    assert paths.chezmoi_diff == "artifacts/20260710-181234-ab12cd/chezmoi-diff.txt"
    assert paths.apply_log == "artifacts/20260710-181234-ab12cd/apply.log"
    assert paths.pytest_json == "artifacts/20260710-181234-ab12cd/pytest.json"
    assert paths.manual_json == "artifacts/20260710-181234-ab12cd/manual.json"
    assert paths.screenshots_dir == "artifacts/20260710-181234-ab12cd/screenshots"
    assert paths.logs_dir == "artifacts/20260710-181234-ab12cd/logs"
    assert paths.verdict == "artifacts/20260710-181234-ab12cd/verdict.json"


def test_bootstrap_ssh_argv_uses_sshpass_and_password_auth():
    # OQ-05 phase 1: the ONE connection allowed to use password auth, to seed key trust.
    argv = bootstrap_ssh_argv("10.0.0.5")
    assert argv[:3] == ["sshpass", "-p", "admin"]
    assert "ssh" in argv
    assert "BatchMode=no" in argv
    assert "admin@10.0.0.5" in argv
    assert "authorized_keys" in argv[-1]


def test_bootstrap_ssh_argv_parameterized_on_user_and_password():
    argv = bootstrap_ssh_argv("10.0.0.5", user="tester", password="hunter2")
    assert argv[:3] == ["sshpass", "-p", "hunter2"]
    assert "tester@10.0.0.5" in argv


def test_ssh_opts_carry_a_server_alive_backstop():
    # OQ-09: ConnectTimeout only bounds the TCP handshake, not a connection that goes dead
    # afterward (host sleep, network drop). This is a network-level backstop, not a substitute
    # for a per-command timeout on the remote side.
    argv = bootstrap_ssh_argv("10.0.0.5")
    assert "ServerAliveInterval=15" in argv
    assert "ServerAliveCountMax=3" in argv


def test_steady_state_ssh_argv_is_batch_mode_yes_key_based():
    # OQ-05 phase 2: spec 12's ssh_opts verbatim (BatchMode=yes), plus -i <throwaway key>.
    argv = steady_state_ssh_argv(
        "10.0.0.5", "chezmoi diff", key_path="harness/ssh/id_ed25519_harness"
    )
    assert "BatchMode=yes" in argv
    assert "BatchMode=no" not in argv
    assert "-i" in argv
    assert "harness/ssh/id_ed25519_harness" in argv
    assert argv[-1].endswith("chezmoi diff")


def test_steady_state_ssh_argv_exports_toolchain_path_first():
    # OQ-08: a non-interactive SSH exec never sources .zprofile/brew shellenv, so chezmoi/retry/
    # brew (all under /opt/homebrew) and mise-managed tools (under the mise shims dir) are off
    # PATH unless exported explicitly, every time.
    argv = steady_state_ssh_argv("10.0.0.5", "chezmoi diff")
    assert argv[-1].startswith(_TOOLCHAIN_PATH_EXPORT)


def test_steady_state_ssh_argv_never_carries_a_tty_flag():
    # G11: the absence of a TTY is what makes chezmoi's stdinIsATTY resolve false.
    argv = steady_state_ssh_argv("10.0.0.5", "chezmoi diff")
    assert "-t" not in argv
    assert "-tt" not in argv


def test_steady_state_ssh_argv_exports_identity_env_after_path_before_the_command():
    argv = steady_state_ssh_argv(
        "10.0.0.5", "chezmoi diff", env=chezmoi_identity_env("20260710-181234-ab12cd")
    )
    assert argv[-1].startswith(_TOOLCHAIN_PATH_EXPORT)
    assert "export CM_computer_name=" in argv[-1]
    assert argv[-1].endswith("chezmoi diff")
