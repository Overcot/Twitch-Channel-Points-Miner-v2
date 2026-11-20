from textwrap import dedent


from TwitchChannelPointsMiner.net import get_session
from TwitchChannelPointsMiner.constants import HTTP_TIMEOUT

from TwitchChannelPointsMiner.classes.Settings import Events


class Webhook(object):
    __slots__ = ["endpoint", "method", "events"]

    def __init__(self, endpoint: str, method: str, events: list):
        self.endpoint = endpoint
        self.method = method
        self.events = [str(e) for e in events]

    def send(self, message: str, event: Events) -> None:
        
        if str(event) in self.events:
            url = self.endpoint + f"?event_name={str(event)}&message={message}" 
            
            if self.method.lower() == "get":
                get_session().get(url=url, timeout=HTTP_TIMEOUT)
            elif self.method.lower() == "post":
                get_session().post(url=url, timeout=HTTP_TIMEOUT)
            else:
                raise ValueError("Invalid method, use POST or GET")
