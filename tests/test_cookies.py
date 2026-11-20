import json
import os
import pickle
import stat

import pytest

from TwitchChannelPointsMiner.classes.Exceptions import WrongCookiesException
from TwitchChannelPointsMiner.classes.TwitchLogin import TwitchLogin
from TwitchChannelPointsMiner.cookiestore import read_cookies, write_cookies

COOKIES = [{"name": "auth-token", "value": "abc"}, {"name": "persistent", "value": "123%3Ax"}]


def test_json_round_trip(tmp_path):
    f = tmp_path / "u.pkl"
    write_cookies(str(f), COOKIES)
    assert json.loads(f.read_text()) == COOKIES
    assert read_cookies(str(f)) == COOKIES


def test_file_is_owner_only_and_no_tmp_left(tmp_path):
    f = tmp_path / "u.pkl"
    write_cookies(str(f), COOKIES)
    assert stat.S_IMODE(os.stat(f).st_mode) == 0o600
    assert os.listdir(tmp_path) == ["u.pkl"]


def test_legacy_pickle_is_migrated_and_backed_up(tmp_path):
    f = tmp_path / "u.pkl"
    f.write_bytes(pickle.dumps(COOKIES))
    assert read_cookies(str(f)) == COOKIES
    assert json.loads(f.read_text()) == COOKIES  # converted in place
    assert pickle.loads((tmp_path / "u.pkl.legacy").read_bytes()) == COOKIES
    assert read_cookies(str(f)) == COOKIES  # second read goes through JSON


def test_failed_write_keeps_old_file(tmp_path):
    f = tmp_path / "u.pkl"
    write_cookies(str(f), COOKIES)
    with pytest.raises(TypeError):
        write_cookies(str(f), [object()])
    assert read_cookies(str(f)) == COOKIES
    assert os.listdir(tmp_path) == ["u.pkl"]


def test_load_cookies_wraps_garbage(tmp_path):
    f = tmp_path / "u.pkl"
    f.write_bytes(b"not a cookie file")
    login = TwitchLogin("client", "dev", "user", "ua")
    with pytest.raises(WrongCookiesException):
        login.load_cookies(str(f))


def test_load_cookies_missing_file(tmp_path):
    login = TwitchLogin("client", "dev", "user", "ua")
    with pytest.raises(WrongCookiesException):
        login.load_cookies(str(tmp_path / "nope.pkl"))
