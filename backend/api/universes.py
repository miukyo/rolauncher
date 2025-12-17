"""

This module contains classes intended to parse and deal with data from Roblox universe information endpoints.

"""
from __future__ import annotations

from typing import TYPE_CHECKING

from .utilities.iterators import OmniPageIterator

if TYPE_CHECKING:
    from .client import Client
from datetime import datetime
from enum import Enum
from typing import Optional, List, Union

from dateutil.parser import parse
import uuid

from .bases.baseplace import BasePlace
from .bases.baseuniverse import BaseUniverse
from .creatortype import CreatorType
from .partials.partialgroup import UniversePartialGroup
from .partials.partialuser import PartialUser
from .utilities.exceptions import UniverseNotFound


class UniverseAvatarType(Enum):
    """
    The current avatar type of the universe.
    """

    R6 = "MorphToR6"
    R15 = "MorphToR15"
    player_choice = "PlayerChoice"


class UniverseGenre(Enum):
    """
    The universe's genre.
    """

    all = "All"
    building = "Building"
    horror = "Horror"
    town_and_city = "Town and City"
    military = "Military"
    comedy = "Comedy"
    medieval = "Medieval"
    adventure = "Adventure"
    sci_fi = "Sci-Fi"
    naval = "Naval"
    fps = "FPS"
    rpg = "RPG"
    sports = "Sports"
    fighting = "Fighting"
    western = "Western"


class Universe(BaseUniverse):
    """
    Represents the response data of https://games.roblox.com/v1/games.

    Attributes:
        id: The ID of this specific universe
        root_place: The thumbnail provider object.
        name: The delivery provider object.
        description: The description of the game.
        creator_type: Is the creator a group or a user.
        creator: creator information.
        price: how much you need to pay to play the game.
        allowed_gear_genres: Unknown
        allowed_gear_categories: Unknown
        is_genre_enforced: Unknown
        copying_allowed: are you allowed to copy the game.
        playing: amount of people currently playing the game.
        visits: amount of visits to the game.
        max_players: the maximum amount of players ber server.
        created: when the game was created.
        updated: when the game as been updated for the last time.
        studio_access_to_apis_allowed: does studio have access to the apis.
        create_vip_servers_allowed: can you create a vip server?
        universe_avatar_type: type of avatars in the game.
        genre: what genre the game is.
        is_all_genre: if it is all genres?
        is_favorited_by_user: if the authenticated user has it favorited.
        favorited_count: the total amount of people who favorited the game.
    """

    def __init__(self, client: Client, data: dict):
        """
        Arguments:
            client: The Client.
            data: The universe data.
        """

        self._client: Client = client

        self.id: int = data["id"]
        super().__init__(client=client, universe_id=self.id)
        self.root_place: BasePlace = BasePlace(
            client=client, place_id=data["rootPlaceId"])
        self.name: str = data["name"]
        self.description: str = data["description"]
        self.creator_type: Enum = CreatorType(data["creator"]["type"])
        # isRNVAccount is not part of PartialUser, UniversePartialGroup
        self.creator: Union[PartialUser, UniversePartialGroup]
        if self.creator_type == CreatorType.group:
            self.creator = UniversePartialGroup(client, data["creator"])
        elif self.creator_type == CreatorType.user:
            self.creator = PartialUser(client, data["creator"])
        self.price: Optional[int] = data["price"]
        self.allowed_gear_genres: List[str] = data["allowedGearGenres"]
        self.allowed_gear_categories: List[str] = data["allowedGearCategories"]
        self.is_genre_enforced: bool = data["isGenreEnforced"]
        self.copying_allowed: bool = data["copyingAllowed"]
        self.playing: int = data["playing"]
        self.visits: int = data["visits"]
        self.max_players: int = data["maxPlayers"]
        self.created: datetime = parse(data["created"])
        self.updated: datetime = parse(data["updated"])
        self.studio_access_to_apis_allowed: bool = data["studioAccessToApisAllowed"]
        self.create_vip_servers_allowed: bool = data["createVipServersAllowed"]
        self.universe_avatar_type: UniverseAvatarType = UniverseAvatarType(
            data["universeAvatarType"])
        self.genre: UniverseGenre = UniverseGenre(data["genre"])
        self.is_all_genre: bool = data["isAllGenre"]
        # gameRating seems to be null across all games, so I omitted it from this class.
        self.is_favorited_by_user: bool = data["isFavoritedByUser"]
        self.favorited_count: int = data["favoritedCount"]


class UniverseIterator:
    def __init__(self, client: Client, topic: str, max_per_page: int = 10):
        """
        Initializes the UniverseIterator.

        Arguments:
            client: The Client instance to make requests.
            topic: The topic to filter universes (e.g., "Recommended For You", "Continue").
            max_per_page: Maximum number of universes to fetch per page.
        """
        self._client = client
        self._topic = topic
        self._max_per_page = max_per_page
        self._current_index = 0
        self._universe_ids = []
        self._universes_cache = {}  # Cache fetched universes by ID
        self._has_fetched = False

    async def _fetch_all(self):
        """
        Fetches all universes for the given topic.
        """
        import trio

        max_retries = 3
        for attempt in range(max_retries):
            response = await self._client.requests.cache_post(
                url=self._client.url_generator.get_url(
                    "apis", "discovery-api/omni-recommendation"
                ),
                json={
                    "pageType": "GameHomePage",
                    "sessionId": str(uuid.uuid4())
                },
            )

            data = response.json()

            # Check if 'sorts' key exists in the response
            if "sorts" not in data:
                if attempt < max_retries - 1:
                    # Wait before retrying
                    await trio.sleep(2 * (attempt + 1))
                    continue
                else:
                    raise ValueError(
                        f"API response missing 'sorts' key after {max_retries} attempts. Response keys: {list(data.keys())}, Response: {data}"
                    )

            recommendation_data = list()
            for sort in data["sorts"]:
                if sort["topic"] == self._topic and sort.get("recommendationList"):
                    recommendation_data = sort["recommendationList"]
                    break

            self._universe_ids = [item["contentId"]
                                  for item in recommendation_data if item["contentType"] == "Game"]
            self._has_fetched = True
            break

    async def get_page(self, page_number: int) -> List[Universe]:
        """
        Fetches a specific page of universes.

        Arguments:
            page_number: The page number to fetch (1-based index).

        Returns:
            A list of Universe objects.
        """
        if not self._has_fetched:
            await self._fetch_all()

        start_index = (page_number - 1) * self._max_per_page
        end_index = start_index + self._max_per_page

        if start_index >= len(self._universe_ids):
            raise ValueError("Page number out of range.")

        batch_ids = self._universe_ids[start_index:end_index]

        # Check which universes we need to fetch
        to_fetch = [
            uid for uid in batch_ids if uid not in self._universes_cache]

        # Fetch only the ones we don't have cached
        if to_fetch:
            fetched_universes = await UniverseProvider(self._client).get_universes(universe_ids=to_fetch)
            for universe in fetched_universes:
                self._universes_cache[universe.id] = universe

        # Return universes in the original order
        return [self._universes_cache[uid] for uid in batch_ids if uid in self._universes_cache]

    async def get_all(self) -> List[Universe]:
        """
        Fetches all universes for the topic.

        Returns:
            A list of all Universe objects.
        """
        if not self._has_fetched:
            await self._fetch_all()

        # Check which universes we need to fetch
        to_fetch = [
            uid for uid in self._universe_ids if uid not in self._universes_cache]

        # Fetch only the ones we don't have cached
        if to_fetch:
            fetched_universes = await UniverseProvider(self._client).get_universes(universe_ids=to_fetch)
            for universe in fetched_universes:
                self._universes_cache[universe.id] = universe

        # Return all universes in the original order
        return [self._universes_cache[uid] for uid in self._universe_ids if uid in self._universes_cache]


class UniverseProvider:
    """
    Provides methods to interact with Roblox universes.
    """

    def __init__(self, client: Client):
        """
        Arguments:
            client: The Client to be used when getting universe information.
        """
        self._client: Client = client

    async def get_universes(self, universe_ids: List[int]) -> List[Universe]:
        """
        Grabs a list of universes corresponding to each ID in the list, processing in batches of 50.

        Arguments:
            universe_ids: A list of Roblox universe IDs.

        Returns:
            A list of Universes.
        """
        all_universes = []

        # Process universe_ids in chunks of 50
        for i in range(0, len(universe_ids), 50):
            batch = universe_ids[i:i + 50]
            universes_response = await self._client.requests.cache_get(
                url=self._client._url_generator_roproxy.get_url(
                    "games", "v1/games"),
                params={"universeIds": ",".join(map(str, batch))},
            )
            universes_data = universes_response.json()["data"]

            # Append the results of the current batch
            all_universes.extend(
                Universe(client=self._client, data=universe_data)
                for universe_data in universes_data
            )

        return all_universes

    async def get_universe(self, universe_id: int) -> Universe:
        """
        Gets a universe with the passed ID.

        Arguments:
            universe_id: A Roblox universe ID.

        Returns:
            A Universe.
        """
        universes = await self.get_universes(universe_ids=[universe_id])
        try:
            return universes[0]
        except IndexError:
            raise UniverseNotFound("Invalid universe.") from None

    def get_base_universe(self, universe_id: int) -> BaseUniverse:
        """
        Gets a base universe.

        !!! note
            This method does not send any requests - it just generates an object.
            For more information on bases, please see [Bases](../tutorials/bases.md).

        Arguments:
            universe_id: A Roblox universe ID.

        Returns:
            A BaseUniverse.
        """
        return BaseUniverse(client=self._client)

    async def get_authed_recommendations_universe(self, max_per_page: int = 10) -> UniverseIterator:
        """
        Gets an iterable for the authenticated user's recommended universes.

        Arguments:
            max_per_page: Maximum number of universes to fetch per page.

        Returns:
            A UniverseIterator instance.
        """
        return UniverseIterator(client=self._client, topic="Recommended For You", max_per_page=max_per_page)

    async def get_authed_continue_universe(self, max_per_page: int = 10) -> UniverseIterator:
        """
        Gets an iterable for the authenticated user's continue universes.

        Arguments:
            max_per_page: Maximum number of universes to fetch per page.

        Returns:
            A UniverseIterator instance.
        """
        return UniverseIterator(client=self._client, topic="Continue", max_per_page=max_per_page)

    async def get_authed_favorites_universe(self, max_per_page: int = 10) -> UniverseIterator:
        """
        Gets an iterable for the authenticated user's favorite universes.

        Arguments:
            max_per_page: Maximum number of universes to fetch per page.
        Returns:
            A UniverseIterator instance.
        """
        return UniverseIterator(client=self._client, topic="Favorites", max_per_page=max_per_page)

    async def set_favorite(self, universe_id: int, favorite: bool) -> None:
        """
        Sets the favorite status for a universe.

        Arguments:
            universe_id: A Roblox universe ID.
            favorite: Whether to favorite (True) or unfavorite (False).
        """

        await self._client.requests.post(
            url=self._client._url_generator_roblox.get_url(
                "games", f"v1/games/{universe_id}/favorites"
            ),
            json={
                "isFavorited": favorite
            }
        )

    class Votes:
        id: int
        upVotes: int
        downVotes: int

        def __init__(self, id: int, upVotes: int, downVotes: int):
            self.id = id
            self.upVotes = upVotes
            self.downVotes = downVotes

    async def get_votes(self, universe_ids: List[int]) -> List[Votes]:
        """
        Gets the upvote and downvote counts for universes, processing in batches of 50.

        Arguments:
            universe_ids: A list of Roblox universe IDs.

        Returns:
            A list of Votes objects.
        """
        all_votes = []

        # Process universe_ids in chunks of 50
        for i in range(0, len(universe_ids), 50):
            batch = universe_ids[i:i + 50]
            votes_response = await self._client.requests.cache_get(
                url=self._client._url_generator_roblox.get_url(
                    "games", f"v1/games/votes"
                ),
                params={"universeIds": ",".join(map(str, batch))}
            )
            votes_data = votes_response.json()

            # Append the results of the current batch
            all_votes.extend(
                self.Votes(
                    id=int(vote["id"]),
                    upVotes=int(vote["upVotes"]),
                    downVotes=int(vote["downVotes"])
                ) for vote in votes_data["data"]
            )

        return all_votes

    class VoteStatus:
        canVote: bool
        userVote: bool
        reason: Optional[str]

        def __init__(self, canVote: bool, userVote: Optional[bool], reason: Optional[str]):
            self.canVote = canVote
            self.userVote = userVote
            self.reason = reason

    async def get_vote_status(self, universe_id: int) -> VoteStatus:
        """
        Gets the vote status for a universe.

        Arguments:
            universe_id: A Roblox universe ID.
        Returns:
            The vote status.
        """
        vote_status_response = await self._client.requests.get(
            url=self._client._url_generator_roblox.get_url(
                "games", f"v1/games/{universe_id}/votes/user"
            ),
        )
        vote_status_data = vote_status_response.json()
        return self.VoteStatus(
            canVote=bool(vote_status_data["canVote"]),
            userVote=bool(vote_status_data["userVote"]),
            reason=vote_status_data.get("reason"))

    async def set_vote(self, universe_id: int, upvote: bool) -> None:
        """
        Sets the vote for a universe.

        Arguments:
            universe_id: A Roblox universe ID.
            upvote: Whether to upvote(True) or downvote(False).
        """
        await self._client.requests.patch(
            url=self._client._url_generator_roblox.get_url(
                "games", f"v1/games/{universe_id}/user-votes"
            ),
            json={
                "vote": upvote
            }
        )

    async def get_playability(self, universe_ids: List[int]) -> List[bool]:
        """
        Gets the playability status for universes, processing in batches of 50.

        Arguments:
            universe_ids: A list of Roblox universe IDs.

        Returns:
            A list of booleans indicating playability.
        """
        playability_status = []

        # Process universe_ids in chunks of 50
        for i in range(0, len(universe_ids), 50):
            batch = universe_ids[i:i + 50]
            playability_response = await self._client.requests.get(
                url=self._client.url_generator.get_url(
                    "games", f"v1/games/multiget-playability-status"
                ),
                params={"universeIds": ",".join(map(str, batch))}
            )
            playability_data = playability_response.json()
            # Append the results of the current batch
            playability_status.extend({
                "universe_id": int(item["universeId"]),
                "is_playable": bool(item["isPlayable"]),
                "playability_status": item["playabilityStatus"]
            } for item in playability_data
            )

        return playability_status

    def search_universes(self, query: str) -> OmniPageIterator:
        """
        Searches for universes based on a query.

        Arguments:
            query: The search query.
            page_size: How many universes should be returned for each page.
            sort_order: Order in which data should be grabbed.
            max_items: The maximum items to return when looping through this object.
        Returns:
            A PageIterator containing Universes.
        """

        return OmniPageIterator(
            client=self._client,
            url=self._client.url_generator.get_url(
                "apis", f"search-api/omni-search"),
            extra_url_parameters={"sessionId": str(
                uuid.uuid4()), "searchQuery": query},
            handler=lambda client, data: data
        )

    async def search_suggestions(self, query: str) -> List[str]:
        """
        Gets search suggestions for universes based on a query.

        Arguments:
            query: The search query.
        Returns:
            A list of search suggestions.
        """
        response = await self._client.requests.cache_get(
            url=self._client.url_generator.get_url(
                "apis", f"games-autocomplete/v1/get-suggestion/{query}")
        )
        data = response.json()
        return [suggestion["searchQuery"] for suggestion in data["entries"]]
