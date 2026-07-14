from scripts.check_protected_scope import find_violations


def test_protected_file_is_rejected() -> None:
    violations = find_violations(["docs/VIDEO_RUNBOOK.md"], "")
    assert violations == ["protected file changed: docs/VIDEO_RUNBOOK.md"]


def test_changed_video_field_is_rejected() -> None:
    diff = "\n".join(
        [
            "+++ b/docs/SUBMISSION_CHECKLIST.md",
            "-Pitch video | <VIDEO_LINK_HERE>",
            "+Pitch video | https://youtube.example/demo",
        ]
    )
    violations = find_violations(["docs/SUBMISSION_CHECKLIST.md"], diff)
    assert len(violations) == 2


def test_unrelated_documentation_change_is_allowed() -> None:
    diff = "\n".join(
        [
            "+++ b/docs/CLAIMS_REGISTER.md",
            "-The case store has no deletion endpoint.",
            "+The case store exposes an authenticated deletion endpoint.",
        ]
    )
    assert find_violations(["docs/CLAIMS_REGISTER.md"], diff) == []
