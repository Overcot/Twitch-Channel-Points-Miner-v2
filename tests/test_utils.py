import socket

import pytest

from TwitchChannelPointsMiner import utils


@pytest.mark.parametrize(
    "value, precision, expected",
    [
        (0, 2, "0"),
        (999, 2, "999"),
        (1000, 2, "1k"),
        (1500, 2, "1.5k"),
        (12345, 2, "12.35k"),
        (1_234_567, 2, "1.23M"),
        (-98765, 2, "-98.77k"),
        (999_999, 2, "1000k"),  # same rounding behaviour as the old `millify` package
        (10**15, 0, "1P"),
    ],
)
def test_millify(value, precision, expected):
    assert utils.millify(value, precision) == expected


def test_internet_check_does_not_touch_global_socket_timeout(monkeypatch):
    class Dummy:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(socket, "create_connection", lambda *a, **k: Dummy())
    before = socket.getdefaulttimeout()
    assert utils.internet_connection_available() is True
    assert socket.getdefaulttimeout() == before


def test_internet_check_false_on_oserror(monkeypatch):
    def boom(*a, **k):
        raise OSError("down")

    monkeypatch.setattr(socket, "create_connection", boom)
    assert utils.internet_connection_available() is False


def test_http_timeout_is_set_on_all_requests():
    """Every get_session().get/post/head call in the package must carry a timeout."""
    import pathlib
    import re

    root = pathlib.Path(__file__).resolve().parent.parent / "TwitchChannelPointsMiner"
    offenders = []
    for path in root.rglob("*.py"):
        src = path.read_text(encoding="utf-8")
        # Ignore the dead post_integrity() block kept inside a docstring.
        src = re.sub(r'""".*?"""', "", src, flags=re.S)
        for m in re.finditer(r"get_session\(\)\.(?:get|post|head)\(", src):
            depth, i = 1, m.end()
            while depth:
                depth += (src[i] == "(") - (src[i] == ")")
                i += 1
            if "timeout" not in src[m.end(): i]:
                offenders.append(f"{path.name}: {src[m.start(): m.start() + 60]!r}")
    assert not offenders, offenders
