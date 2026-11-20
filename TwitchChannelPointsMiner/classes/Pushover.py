from textwrap import dedent


from TwitchChannelPointsMiner.net import get_session
from TwitchChannelPointsMiner.constants import HTTP_TIMEOUT

from TwitchChannelPointsMiner.classes.Settings import Events


class Pushover(object):
    __slots__ = ["userkey", "token", "priority", "sound", "events"]

    def __init__(self, userkey: str, token: str, priority, sound, events: list):
        self.userkey = userkey
        self.token = token
        self. priority = priority
        self.sound = sound
        self.events = [str(e) for e in events]

    def send(self, message: str, event: Events) -> None:
        if str(event) in self.events:
            get_session().post(
                url="https://api.pushover.net/1/messages.json",
                data={
                    "user": self.userkey,
                    "token": self.token,
                    "message": dedent(message),
                    "title": "Twitch Channel Points Miner",
                    "priority": self.priority,
                    "sound": self.sound,
                },
                timeout=HTTP_TIMEOUT,
            )
