"""Cookie file storage: JSON on disk, with one-time migration from the legacy pickle format."""
import json
import logging
import os
import pickle
import shutil
import tempfile

logger = logging.getLogger(__name__)

_PICKLE_MAGIC = b"\x80"  # every pickle protocol >= 2 starts with the PROTO opcode


def write_cookies(path, cookies):
    """Atomically write `cookies` as JSON with owner-only permissions."""
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".cookies-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(cookies, f)
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def read_cookies(path):
    """Read cookies; a legacy pickle file is converted to JSON in place.

    The original pickle is kept next to it as `<path>.legacy` so that an older
    image can still be started after a rollback.
    """
    with open(path, "rb") as f:
        raw = f.read()

    if raw.startswith(_PICKLE_MAGIC):
        logger.info("Migrating cookies file from pickle to JSON...")
        cookies = pickle.loads(raw)  # noqa: S301 - our own legacy file
        legacy = f"{path}.legacy"
        if not os.path.exists(legacy):
            shutil.copy2(path, legacy)
        write_cookies(path, cookies)
        return cookies

    return json.loads(raw.decode("utf-8"))
