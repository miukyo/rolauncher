"""

Contains the Client, which is the core object at the center of all ro.py applications.

"""

from typing import Optional

from .realtime import WebSocketBuilder

from .account import AccountProvider
from .assets import AssetProvider
from .badges import BadgeProvider
from .chat import ChatProvider
from .delivery import DeliveryProvider
from .groups import GroupProvider
from .places import PlaceProvider
from .plugins import PluginProvider
from .presence import PresenceProvider
from .thumbnails import ThumbnailProvider
from .universes import UniverseProvider
from .users import UserProvider
from .utilities.requests import Requests
from .utilities.url import URLGenerator


class Client:
    """
    Represents a Roblox client.

    Attributes:
        requests: The requests object, which is used to send requests to Roblox endpoints.
        url_generator: The URL generator object, which is used to generate URLs to send requests to endpoints.
        presence: The presence provider object.
        thumbnails: The thumbnail provider object.
        delivery: The delivery provider object.
        chat: The chat provider object.
        account: The account provider object.
        users: The user provider object.
        groups: The group provider object.
        universes: The universe provider object.
        places: The place provider object.
        assets: The asset provider object.
        plugins: The plugin provider object.
        badges: The badge provider object.
    """

    def __init__(self, token: str = None, base_url: str = "roproxy.com", ws_url: str = "realtime-signalr.roblox.com/userhub", enable_websocket: bool = True):
        """
        Arguments:
            token: A .ROBLOSECURITY token to authenticate the client with.
            base_url: The base URL to use when sending requests.
            enable_websocket: Whether to enable the WebSocket connection.
        """
        self._url_generator: URLGenerator = URLGenerator(base_url=base_url)
        self._url_generator_roblox = URLGenerator(base_url="roblox.com")
        self._url_generator_roproxy = URLGenerator(base_url="roproxy.com")
        self._requests: Requests = Requests()
        self._ws_url: str = ws_url
        self._enable_websocket: bool = enable_websocket

        self.url_generator: URLGenerator = self._url_generator
        self.requests: Requests = self._requests
        self.websocket: WebSocketBuilder = None

        self.presence: PresenceProvider = PresenceProvider(client=self)
        self.thumbnails: ThumbnailProvider = ThumbnailProvider(client=self)
        self.delivery: DeliveryProvider = DeliveryProvider(client=self)
        self.chat: ChatProvider = ChatProvider(client=self)
        self.account: AccountProvider = AccountProvider(client=self)
        self.users: UserProvider = UserProvider(client=self)
        self.groups: GroupProvider = GroupProvider(client=self)
        self.universes: UniverseProvider = UniverseProvider(client=self)
        self.places: PlaceProvider = PlaceProvider(client=self)
        self.assets: AssetProvider = AssetProvider(client=self)
        self.plugins: PluginProvider = PluginProvider(client=self)
        self.badges: BadgeProvider = BadgeProvider(client=self)

        if token:
            self.set_token(token)

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    # Authentication
    def set_token(self, token: Optional[str] = None) -> None:
        """
        Authenticates the client with the passed .ROBLOSECURITY token.
        This method does not send any requests and will not throw if the token is invalid.

        Arguments:
            token: A .ROBLOSECURITY token to authenticate the client with.

        """
        if self.websocket and self._enable_websocket:
            self.websocket.set_token(token)
        elif self._enable_websocket:
            self.websocket = WebSocketBuilder(
                url=f"wss://{self._ws_url}", token=token)

        self._requests.session.cookies[".ROBLOSECURITY"] = token

    def set_base_url(self, base_url: str) -> None:
        """
        Changes the base URL used for generating URLs.

        Arguments:
            base_url: The new base URL to use.
        """
        self._url_generator.base_url = base_url

    async def get_authentication_ticket(self) -> Optional[str]:
        """
        Gets the authentication ticket for the current authenticated session.

        Returns:
            The authentication ticket, or None if the client is not authenticated.
        """
        client_assertion = await self.requests.get(
            url=self.url_generator.get_url(
                "auth", "v1/client-assertion/"
            )
        )
        authentication_ticket = await self.requests.post(
            url=self.url_generator.get_url(
                "auth", "v1/authentication-ticket/"
            ),
            json={
                "clientAssertion": client_assertion.json().get("clientAssertion"),
            }
        )

        return authentication_ticket.headers.get("rbx-authentication-ticket")

    async def get_authentication_ticket_from_token(self, token: str) -> Optional[str]:
        """
        Gets the authentication ticket for the passed .ROBLOSECURITY token.

        Arguments:
            token: A .ROBLOSECURITY token to get the authentication ticket for.
        Returns:
            The authentication ticket, or None if the token is invalid.
        """
        temp_client = Client(
            token=token, base_url=self._url_generator.base_url, enable_websocket=False)
        try:
            return await temp_client.get_authentication_ticket()
        finally:
            del temp_client
