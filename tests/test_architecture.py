from scripts.check_architecture import check


def test_backend_architecture_gates_pass():
    assert check() == []
