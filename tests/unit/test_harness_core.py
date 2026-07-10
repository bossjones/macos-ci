from macos_ci._harness_core import (
    RunArtifactPaths,
    artifact_paths,
    chezmoi_argv,
    chezmoi_identity_env,
    clone_name,
    format_run_id,
)


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
