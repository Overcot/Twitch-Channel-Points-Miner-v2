import pathlib
import re
import threading

import requests

from TwitchChannelPointsMiner import net


def test_session_is_reused_within_a_thread():
    assert net.get_session() is net.get_session()


def test_session_is_per_thread():
    seen = []
    t = threading.Thread(target=lambda: seen.append(net.get_session()))
    t.start()
    t.join()
    assert seen[0] is not net.get_session()


def test_retries_never_replay_sent_requests():
    retry = net.get_session().get_adapter("https://x").max_retries
    assert retry.connect == 2
    assert retry.read == 0
    assert retry.status == 0


def test_cookies_are_not_kept():
    import urllib.request

    s = net.get_session()
    cookie = requests.cookies.create_cookie(name="a", value="b", domain="twitch.tv")
    request = urllib.request.Request("https://www.twitch.tv/")
    assert s.cookies.get_policy().set_ok(cookie, request) is False


def test_no_bare_requests_calls_left():
    root = pathlib.Path(__file__).resolve().parent.parent / "TwitchChannelPointsMiner"
    offenders = []
    for path in root.rglob("*.py"):
        src = re.sub(r'""".*?"""', "", path.read_text(encoding="utf-8"), flags=re.S)
        if re.search(r"\brequests\.(?:get|post|head|put|delete)\(", src):
            offenders.append(path.name)
    assert not offenders, offenders
