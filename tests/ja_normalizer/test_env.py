from ja_normalizer.env import PACKAGE_DIR


def test_package_dir() -> None:
    assert PACKAGE_DIR.exists()
