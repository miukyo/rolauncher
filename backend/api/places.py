"""

This module contains classes intended to parse and deal with data from Roblox place information endpoints.

"""
from __future__ import annotations
from typing import TYPE_CHECKING, List
if TYPE_CHECKING:
    from .client import Client
from .bases.baseplace import BasePlace
from .bases.baseuniverse import BaseUniverse
from .utilities.exceptions import PlaceNotFound


class Place(BasePlace):
    """
    Represents a Roblox place.

    Attributes:
        id: id of the place.
        name: Name of the place.
        description: Description of the place.
        url: URL for the place.
        builder: The name of the user or group who owns the place.
        builder_id: The ID of the player or group who owns the place.
        is_playable: Whether the authenticated user can play this game.
        reason_prohibited: If the place is not playable, contains the reason why the user cannot play the game.
        universe: The BaseUniverse that contains this place.
        universe_root_place: The root place that the universe contains.
        price: How much it costs to play the game.
        image_token: Can be used to generate thumbnails for this place.
        has_verified_badge: If the place has a verified badge.
    """

    def __init__(self, client: Client, data: dict):
        """
        Arguments:
            client: The Client object, which is passed to all objects this Client generates.
            data: data to make the magic happen.
        """
        super().__init__(client=client, place_id=data["placeId"])

        self._client: Client = client

        self.id: int = data["placeId"]
        self.name: str = data["name"]
        self.description: str = data["description"]
        self.url: str = data["url"]

        self.builder: str = data["builder"]
        self.builder_id: int = data["builderId"]

        self.is_playable: bool = data["isPlayable"]
        self.reason_prohibited: str = data["reasonProhibited"]
        self.universe: BaseUniverse = BaseUniverse(
            client=self._client, universe_id=data["universeId"])
        self.universe_root_place: BasePlace = BasePlace(
            client=self._client, place_id=data["universeRootPlaceId"])

        self.price: int = data["price"]
        self.image_token: str = data["imageToken"]
        self.has_verified_badge: bool = data["hasVerifiedBadge"]


class PlaceProvider:
    """
    Provides methods to interact with Roblox places.
    """

    def __init__(self, client: Client):
        """
        Arguments:
            client: The Client to be used when getting place information.
        """
        self._client: Client = client

    async def get_places(self, place_ids: List[int]) -> List[Place]:
        """
        Grabs a list of places corresponding to each ID in the list.

        Arguments:
            place_ids: A list of Roblox place IDs.

        Returns:
            A list of Places.
        """
        places_response = await self._client.requests.get(
            url=self._client.url_generator.get_url(
                "games", f"v1/games/multiget-place-details"
            ),
            params={"placeIds": ",".join(map(str, place_ids))},
        )
        places_data = places_response.json()
        return [
            Place(client=self._client, data=place_data) for place_data in places_data
        ]

    async def get_place(self, place_id: int) -> Place:
        """
        Gets a place with the passed ID.

        Arguments:
            place_id: A Roblox place ID.

        Returns:
            A Place.
        """
        places = await self.get_places(place_ids=[place_id])
        try:
            return places[0]
        except IndexError:
            raise PlaceNotFound("Invalid place.") from None

    def get_base_place(self, place_id: int) -> BasePlace:
        """
        Gets a base place.

        !!! note
            This method does not send any requests - it just generates an object.
            For more information on bases, please see [Bases](../tutorials/bases.md).

        Arguments:
            place_id: A Roblox place ID.

        Returns:
            A BasePlace.
        """
        return BasePlace(client=self._client, place_id=place_id)
