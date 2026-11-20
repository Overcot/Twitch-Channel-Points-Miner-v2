from textwrap import dedent


from TwitchChannelPointsMiner.net import get_session
from TwitchChannelPointsMiner.constants import HTTP_TIMEOUT

from TwitchChannelPointsMiner.classes.Settings import Events


class Discord(object):
    __slots__ = ["webhook_api", "events"]

    def __init__(self, webhook_api: str, events: list):
        self.webhook_api = webhook_api
        self.events = [str(e) for e in events]

    def send(self, message: str, event: Events) -> None:
        if str(event) in self.events:
            get_session().post(
                url=self.webhook_api,
                data={
                    "content": dedent(message),
                    "username": "Twitch Channel Points Miner",
                    "avatar_url": "https://i.imgur.com/X9fEkhT.png",
                },
                timeout=HTTP_TIMEOUT,
            )
