import api
import httpx
import trio
from api.jobs import PrivateServer, ServerType
from api.utilities.exceptions import NoMoreItems
from .database import get_last_account


class Games:
    def __init__(self, client: api.Client):
        self.client = client
        self.authed_recommendations = None
        self.authed_continue = None
        self.authed_favorites = None
        self.authed_user_id = None
        self.thumbnail_cache = {}
        self.icon_cache = {}
        self.avatar_cache = {}
        self.friend_servers_iterator = None
        self.public_servers_iterator = None
        self.private_servers_iterator = None
        self.search_iterator = None
        self.search_query = None
        self.public_current_place_id = None
        self.private_current_place_id = None

    def _check_user_changed(self):
        current_user = get_last_account().get("id")
        if self.authed_user_id != current_user:
            self.authed_user_id = current_user
            self.authed_recommendations = None
            self.authed_continue = None
            self.authed_favorites = None

    async def _get_page_items(self, collection: list[api.universes.Universe]):
        if collection is None:
            raise ValueError(
                "Collection not initialized. Please fetch data first.")

        current_page_ids = [item.id for item in collection]

        # Check which thumbnails/icons need to be fetched
        thumbnails_to_fetch = [
            uid for uid in current_page_ids if uid not in self.thumbnail_cache
        ]
        icons_to_fetch = [
            uid for uid in current_page_ids if uid not in self.icon_cache]

        thumbnails = []
        icons = []
        votes = []
        playability = []

        # Fetch only uncached thumbnails
        async def fetch_thumbnails():
            nonlocal thumbnails
            if thumbnails_to_fetch:
                thumbnails = await self.client.thumbnails.get_universe_thumbnails(
                    universes=thumbnails_to_fetch,
                    count_per_universe=5,
                    size=(384, 216),
                    image_format=api.ThumbnailFormat.webp,
                )

                for thumbnails_list in thumbnails:
                    if thumbnails_list.universe_id not in self.thumbnail_cache:
                        self.thumbnail_cache[thumbnails_list.universe_id] = []
                    self.thumbnail_cache[thumbnails_list.universe_id].extend(
                        thumbnails_list.thumbnails
                    )

        # Fetch only uncached icons
        async def fetch_icons():
            nonlocal icons
            if icons_to_fetch:
                icons = await self.client.thumbnails.get_universe_icons(
                    universes=icons_to_fetch,
                    size=(150, 150),
                    image_format=api.ThumbnailFormat.webp,
                )

                for icon in icons:
                    self.icon_cache[icon.target_id] = icon.image_url

        async def fetch_votes():
            nonlocal votes
            votes = await self.client.universes.get_votes(current_page_ids)

        async def fetch_playability():
            nonlocal playability
            playability = await self.client.universes.get_playability(current_page_ids)

        async with trio.open_nursery() as nursery:
            nursery.start_soon(fetch_thumbnails)
            nursery.start_soon(fetch_icons)
            nursery.start_soon(fetch_votes)
            nursery.start_soon(fetch_playability)

        playability_map = {item["universe_id"]: item for item in playability}
        # Use cached thumbnail_map
        thumbnail_map = self.thumbnail_cache

        return [
            {
                "id": item.id,
                "name": item.name,
                "description": item.description,
                "placeId": item.root_place.id,
                "creator": {
                    "id": item.creator.id,
                    "name": item.creator.name,
                    "type": item.creator_type.name,
                },
                "thumbnailUrl": [thumb.image_url for thumb in thumbnail_map[item.id]]
                if item.id in thumbnail_map
                else [],
                "iconUrl": self.icon_cache.get(item.id, ""),
                "price": item.price,
                "allowedGearGenres": item.allowed_gear_genres,
                "allowedGearCategories": item.allowed_gear_categories,
                "isGenreEnforced": item.is_genre_enforced,
                "copyingAllowed": item.copying_allowed,
                "playCount": item.playing,
                "visits": item.visits,
                "maxPlayers": item.max_players,
                "created": item.created.isoformat(),
                "updated": item.updated.isoformat(),
                "studioAccessToApisAllowed": item.studio_access_to_apis_allowed,
                "createVipServersAllowed": item.create_vip_servers_allowed,
                "universeAvatarType": item.universe_avatar_type.name,
                "genre": item.genre.name,
                "isAllGenre": item.is_all_genre,
                "isFavoritedByUser": item.is_favorited_by_user,
                "favoritedCount": item.favorited_count,
                "upvotes": votes[current_page_ids.index(item.id)].upVotes,
                "downvotes": votes[current_page_ids.index(item.id)].downVotes,
                "playability": {
                    "isPlayable": playability_map[item.id]["is_playable"],
                    "playabilityStatus": playability_map[item.id]["playability_status"],
                },
            }
            for item in collection
        ]

    def get_authed_recommendations(self, max_per_page: int = 12):
        async def fetch():
            self._check_user_changed()

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.authed_recommendations = (
                        await self.client.universes.get_authed_recommendations_universe(
                            max_per_page
                        )
                    )
                    if not self.authed_recommendations:
                        raise ValueError("No recommendations found.")
                    return await self._get_page_items(
                        await self.authed_recommendations.get_page(1)
                    )
                except (
                    httpx.ConnectTimeout,
                    httpx.ReadTimeout,
                    httpx.ConnectError,
                ) as e:
                    if attempt < max_retries - 1:
                        # Exponential backoff
                        await trio.sleep(1.0 * (attempt + 1))
                        continue
                    raise ValueError(
                        f"Connection timeout after {max_retries} attempts: {e}"
                    )

        return trio.run(fetch)

    def get_authed_recommendations_page(self, page: int):
        async def fetch():
            page_data = await self.authed_recommendations.get_page(page)
            return await self._get_page_items(page_data)

        return trio.run(fetch)

    def get_authed_continue(self, max_per_page: int = 12):
        async def fetch():
            self._check_user_changed()

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.authed_continue = (
                        await self.client.universes.get_authed_continue_universe(
                            max_per_page
                        )
                    )
                    if not self.authed_continue:
                        raise ValueError("No continue games found.")
                    return await self._get_page_items(
                        await self.authed_continue.get_page(1)
                    )
                except (
                    httpx.ConnectTimeout,
                    httpx.ReadTimeout,
                    httpx.ConnectError,
                ) as e:
                    if attempt < max_retries - 1:
                        # Exponential backoff
                        await trio.sleep(1.0 * (attempt + 1))
                        continue
                    raise ValueError(
                        f"Connection timeout after {max_retries} attempts: {e}"
                    )

        return trio.run(fetch)

    def get_authed_continue_page(self, page: int):
        async def fetch():
            page_data = await self.authed_continue.get_page(page)
            return await self._get_page_items(page_data)

        return trio.run(fetch)

    def get_authed_favorites(self, max_per_page: int = 24):
        async def fetch():
            self._check_user_changed()

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.authed_favorites = (
                        await self.client.universes.get_authed_favorites_universe(
                            max_per_page
                        )
                    )
                    if not self.authed_favorites:
                        raise ValueError("No favorite games found.")
                    return await self._get_page_items(
                        await self.authed_favorites.get_page(1)
                    )
                except (
                    httpx.ConnectTimeout,
                    httpx.ReadTimeout,
                    httpx.ConnectError,
                ) as e:
                    if attempt < max_retries - 1:
                        # Exponential backoff
                        await trio.sleep(1.0 * (attempt + 1))
                        continue
                    raise ValueError(
                        f"Connection timeout after {max_retries} attempts: {e}"
                    )

        return trio.run(fetch)

    def get_authed_favorites_page(self, page: int):
        async def fetch():
            page_data = await self.authed_favorites.get_page(page)
            return await self._get_page_items(page_data)

        return trio.run(fetch)

    async def _process_servers(self, servers):
        """Helper method to process server data and fetch avatars."""
        # Collect all unique player tokens
        all_tokens = set()
        for server in servers:
            all_tokens.update(server.player_tokens)
            all_tokens.update(
                [token.player_token for token in server.players if server.players]
            )

        # Check which avatars need to be fetched
        tokens_to_fetch = [
            token for token in all_tokens if token not in self.avatar_cache
        ]

        # Fetch only uncached avatars
        if tokens_to_fetch:
            avatars = await self.client.thumbnails.get_user_avatar_with_token(
                tokens=tokens_to_fetch,
                size=(48, 48),
                image_format=api.ThumbnailFormat.webp,
            )
            for avatar in avatars:
                # Extract token from requestId format: 0:TOKEN:AvatarHeadshot:150x150:webp:regular:
                request_parts = avatar.request_id.split(":")
                if len(request_parts) > 1:
                    token = request_parts[1]
                    self.avatar_cache[token] = avatar.image_url

    def get_servers(self, id: int, page_size: int = 10):
        async def fetch():
            # Always reinitialize iterators for a new place to avoid lock issues
            # if self.public_current_place_id != id:
            #     self.public_current_place_id = id
            #     self.friend_servers_iterator = None
            #     self.public_servers_iterator = None

            # # Initialize iterators if not initialized
            # if not self.friend_servers_iterator or not self.public_servers_iterator:
            baseplace = self.client.places.get_base_place(id)
            self.friend_servers_iterator = baseplace.get_servers(
                server_type=ServerType.friend, page_size=page_size
            )
            self.public_servers_iterator = baseplace.get_servers(
                server_type=ServerType.public, page_size=page_size
            )

            # Fetch first page from both iterators
            friend_servers = []
            public_servers = []
            next_cursor = ""

            async def get_friend_servers():
                nonlocal friend_servers
                try:
                    friend_servers = await self.friend_servers_iterator.next()
                except NoMoreItems:
                    pass
                except Exception as e:
                    print(f"Friend servers error: {e}", flush=True)

            async def get_public_servers():
                nonlocal public_servers, next_cursor
                try:
                    public_servers = await self.public_servers_iterator.next()
                    next_cursor = self.public_servers_iterator.next_cursor
                except NoMoreItems:
                    pass
                except Exception as e:
                    print(f"Public servers error: {e}", flush=True)

            # --- Concurrency using Trio Nursery ---
            async with trio.open_nursery() as nursery:
                nursery.start_soon(get_friend_servers)
                nursery.start_soon(get_public_servers)

            # Merge servers with friend servers first, removing duplicates
            seen_ids = set()
            all_servers = []
            for server in friend_servers + public_servers:
                if server.id not in seen_ids:
                    seen_ids.add(server.id)
                    all_servers.append(server)
            await self._process_servers(all_servers)

            return [
                {
                    "id": server.id,
                    "maxPlayers": server.max_players,
                    "playing": server.playing,
                    "playerTokens": server.player_tokens,
                    "playerAvatars": [
                        self.avatar_cache.get(token, "")
                        for token in server.player_tokens
                    ],
                    "fps": server.fps,
                    "ping": server.ping,
                    "nextCursor": next_cursor,
                }
                for server in all_servers
            ]

        return trio.run(fetch)

    def get_servers_next_page(self):
        async def fetch():
            if not self.friend_servers_iterator or not self.public_servers_iterator:
                raise ValueError(
                    "Iterators not initialized. Call get_servers first.")

            # Fetch next page from both iterators
            friend_servers = []
            public_servers = []
            next_cursor = ""

            try:
                friend_servers = await self.friend_servers_iterator.next()
            except NoMoreItems:
                pass
            except Exception as e:
                print(f"Friend servers next page error: {e}", flush=True)

            try:
                public_servers = await self.public_servers_iterator.next()
                next_cursor = self.public_servers_iterator.next_cursor
            except NoMoreItems:
                pass
            except Exception as e:
                print(f"Public servers next page error: {e}", flush=True)

            # Merge servers, removing duplicates
            seen_ids = set()
            all_servers = []
            for server in friend_servers + public_servers:
                if server.id not in seen_ids:
                    seen_ids.add(server.id)
                    all_servers.append(server)

            await self._process_servers(all_servers)

            return [
                {
                    "id": server.id,
                    "maxPlayers": server.max_players,
                    "playing": server.playing,
                    "playerTokens": server.player_tokens,
                    "playerAvatars": [
                        self.avatar_cache.get(token, "")
                        for token in server.player_tokens
                    ],
                    "fps": server.fps,
                    "ping": server.ping,
                    "nextCursor": next_cursor,
                }
                for server in all_servers
            ]

        return trio.run(fetch)

    def get_servers_private(self, id: int, page_size: int = 10):
        async def fetch():
            # # Always reinitialize iterator for a new place to avoid lock issues
            # if self.private_current_place_id != id:
            #     self.private_current_place_id = id
            #     self.private_servers_iterator = None

            # Initialize iterator if not initialized
            # if not self.private_servers_iterator:
            baseplace = self.client.places.get_base_place(id)
            self.private_servers_iterator = baseplace.get_private_servers(
                page_size=page_size
            )

            # Fetch first page
            servers: list[PrivateServer] = []
            next_cursor = ""
            try:
                servers = await self.private_servers_iterator.next()
                next_cursor = self.private_servers_iterator.next_cursor
            except NoMoreItems:
                pass
            except Exception as e:
                print(f"Private servers error: {e}", flush=True)

            await self._process_servers(servers)

            return [
                {
                    "id": server.vip_server_id,
                    "maxPlayers": server.max_players,
                    "playing": server.playing,
                    "playerTokens": server.player_tokens,
                    "playerAvatars": [
                        self.avatar_cache.get(token, "")
                        for token in server.player_tokens
                    ],
                    "fps": server.fps,
                    "ping": server.ping,
                    "name": server.name,
                    "accessCode": server.access_code,
                    "owner": {
                        "id": server.owner.id,
                        "name": server.owner.name,
                        "displayName": server.owner.display_name,
                    },
                    "nextCursor": next_cursor,
                }
                for server in servers
            ]

        return trio.run(fetch)

    def get_servers_private_next_page(self):
        async def fetch():
            if not self.private_servers_iterator:
                raise ValueError(
                    "Iterator not initialized. Call get_servers_private first."
                )

            # Fetch next page
            servers: list[PrivateServer] = []
            next_cursor = ""
            try:
                servers = await self.private_servers_iterator.next()
                next_cursor = self.private_servers_iterator.next_cursor
            except NoMoreItems:
                pass
            except Exception as e:
                print(f"Private servers next page error: {e}", flush=True)

            await self._process_servers(servers)

            return [
                {
                    "id": server.vip_server_id,
                    "maxPlayers": server.max_players,
                    "playing": server.playing,
                    "playerTokens": server.player_tokens,
                    "playerAvatars": [
                        self.avatar_cache.get(token, "")
                        for token in server.player_tokens
                    ],
                    "fps": server.fps,
                    "ping": server.ping,
                    "name": server.name,
                    "accessCode": server.access_code,
                    "owner": {
                        "id": server.owner.id,
                        "name": server.owner.name,
                        "displayName": server.owner.display_name,
                    },
                    "nextCursor": next_cursor,
                }
                for server in servers
            ]

        return trio.run(fetch)

    def set_favorite(self, universe_id: int, favorite: bool):
        async def fetch():
            await self.client.universes.set_favorite(universe_id, favorite)

        return trio.run(fetch)

    def get_vote_status(self, universe_id: int):
        async def fetch():
            vote_status = await self.client.universes.get_vote_status(universe_id)
            return {
                "canVote": vote_status.canVote,
                "userVote": vote_status.userVote,
                "reason": vote_status.reason,
            }

        return trio.run(fetch)

    def set_vote(self, universe_id: int, vote: bool):
        async def fetch():
            await self.client.universes.set_vote(universe_id, vote)

        return trio.run(fetch)

    def search_universes(self, query: str):
        async def fetch():
            self.search_query = query
            self.search_iterator = self.client.universes.search_universes(
                query)

            items: list[dict] = []
            next_cursor = ""
            try:
                items = await self.search_iterator.next()
                next_cursor = self.search_iterator.next_cursor
            except NoMoreItems:
                pass
            except Exception as e:
                print(f"Private servers next page error: {e}", flush=True)

            async def get_universes():
                universe_ids = [
                    content["universeId"]
                    for result in items
                    for content in (
                        result["contents"]
                        if isinstance(result["contents"], list)
                        else [result["contents"]]
                    )
                ]
                universes_data = await self.client.universes.get_universes(
                    universe_ids=universe_ids
                )
                return universes_data

            return [next_cursor, await self._get_page_items(await get_universes())]

        return trio.run(fetch)

    def search_universes_next_page(self):
        async def fetch():
            if not self.search_iterator:
                raise ValueError(
                    "Iterator not initialized. Call search_universes first."
                )

            items: list[dict] = []
            next_cursor = ""
            try:
                items = await self.search_iterator.next()
                next_cursor = self.search_iterator.next_cursor
            except NoMoreItems:
                pass
            except Exception as e:
                print(f"Private servers next page error: {e}", flush=True)

            async def get_universes():
                universe_ids = [
                    content["universeId"]
                    for result in items
                    for content in (
                        result["contents"]
                        if isinstance(result["contents"], list)
                        else [result["contents"]]
                    )
                ]
                universes_data = await self.client.universes.get_universes(
                    universe_ids=universe_ids
                )
                return universes_data

            return [next_cursor, await self._get_page_items(await get_universes())]

        return trio.run(fetch)

    def search_suggestions(self, query: str):
        async def fetch():
            suggestions = await self.client.universes.search_suggestions(
                query=query,
            )
            return suggestions

        return trio.run(fetch)
