"""

This file contains the BaseUser object, which represents a Roblox user ID.

"""

from __future__ import annotations
from enum import Enum
from typing import Optional, List, TYPE_CHECKING

from ..utilities.url import URLGenerator

from .baseitem import BaseItem
from ..bases.basebadge import BaseBadge
from ..instances import ItemInstance, InstanceType, AssetInstance, GamePassInstance, instance_classes
from ..partials.partialbadge import PartialBadge
from ..presence import Presence
from ..promotionchannels import UserPromotionChannels
from ..robloxbadges import RobloxBadge
from ..utilities.iterators import PageIterator, CursoredPageIterator, SortOrder
from ..bases.baseplace import BasePlace
from ..bases.baseuniverse import BaseUniverse
from ..bases.basejob import BaseJob

if TYPE_CHECKING:
    from ..client import Client
    from ..roles import Role
    from ..utilities.types import AssetOrAssetId, GamePassOrGamePassId, GroupOrGroupId


class UserSort(Enum):
    friend_score = "FriendScore"
    friendship_created_date = "CreatedDate"
    status_frequents = "StatusFrequents"


class FriendType(Enum):
    all = 0
    trusted_friend = 1
    friend = 2


class BaseUser(BaseItem):
    """
    Represents a Roblox user ID.

    Attributes:
        id: The user ID.
    """

    def __init__(self, client: Client, user_id: int, other: Optional[any] = None):
        """
        Arguments:
            client: The Client this object belongs to.
            user_id: The user ID.
            other: Optional additional data.
        """

        self._client: Client = client
        self.id: int = user_id
        self.other: Optional[any] = other

    def username_history(
            self, page_size: int = 10, sort_order: SortOrder = SortOrder.Ascending, max_items: int = None
    ) -> PageIterator:
        """
        Grabs the user's username history.

        Arguments:
            page_size: How many members should be returned for each page.
            sort_order: Order in which data should be grabbed.
            max_items: The maximum items to return when looping through this object.

        Returns:
            A PageIterator containing the user's username history.
        """
        return PageIterator(
            client=self._client,
            url=self._client.url_generator.get_url(
                "users", f"v1/users/{self.id}/username-history"
            ),
            page_size=page_size,
            sort_order=sort_order,
            max_items=max_items,
            handler=lambda client, data: data["name"],
        )

    async def get_presence(self) -> Optional[Presence]:
        """
        Grabs the user's presence.

        Returns:
            The user's presence, if they have an active presence.
        """
        presences = await self._client.presence.get_user_presences([self.id])
        try:
            return presences[0]
        except IndexError:
            return None

    def get_friends(self, friend_type: FriendType = FriendType.all, page_size: int = 50, sort_order: UserSort = UserSort.friend_score) -> CursoredPageIterator:
        """
        Grabs the user's friends.

        Arguments:
            friend_type: The type of friends to iterate through.
            page_size: How many friends should be returned for each page. Can only be a number between 1 to 50.
            sort_order: Order in which data should be grabbed.

        Returns:
            A list of the user's friends.
        """

        return CursoredPageIterator(
            self._client,
            self._client.url_generator.get_url(
                "friends", f"v1/users/{self.id}/friends/find"),
            {
                "limit": page_size,
                "userSort": sort_order.value,
                "findFriendsType": friend_type.value
            },
            handler=lambda client, data: data
        )

    class Friends:
        def __init__(self, data):
            self.id: int = data["id"]
            self.name: str = data["name"]
            self.displayName: str = data["displayName"]
            self.presence: Presence = data["presence"]
            self.sortScore: float = data["sortScore"]

    async def get_friendsv2(self):
        """
        Grabs the user's friends using the v2 endpoint.

        Returns:
            A CursoredPageIterator of the user's friends.
        """

        response = await self._client.requests.get(
            url=self._client._url_generator_roproxy.get_url(
                "friends", f"v1/users/{self.id}/friends"),
        )
        friends_data = response.json()["data"]

        usernames_response = await self._client.requests.post(
            url=self._client._url_generator_roproxy.get_url(
                "apis", f"user-profile-api/v1/user/profiles/get-profiles"),
            json={"userIds": [friends_data[i]["id"]
                              for i in range(len(friends_data))], "fields": ["names.combinedName", "names.username"]}
        )
        usernames_data = usernames_response.json()["profileDetails"]
        username_map = {user["userId"]: user for user in usernames_data}
        for friend in friends_data:
            friend_id = friend["id"]
            if friend_id in username_map:
                friend["name"] = username_map[friend_id]["names"]["username"]
                friend["displayName"] = username_map[friend_id]["names"]["combinedName"]
            else:
                friend["name"] = ""
                friend["displayName"] = ""

        # Fetch presences using the public presence endpoint
        friend_ids = [friend["id"] for friend in friends_data]
        presences = await self._client.presence.get_user_presences(friend_ids)
        presence_map = {p.user.id: p for p in presences}

        # Add presence information to friends data
        for friend in friends_data:
            friend_id = friend["id"]
            if friend_id in presence_map:
                friend["presence"] = presence_map[friend_id]

                # Calculate sort score manually
                ptype = friend["presence"].user_presence_type.value
                # 2=InGame, 3=Studio, 1=Online, 0=Offline
                if ptype == 2:
                    score = 30
                elif ptype == 3:
                    score = 20
                elif ptype == 1:
                    score = 10
                else:
                    score = 0
                friend["sortScore"] = score
            else:
                friend["presence"] = Presence(
                    self._client, {
                        "userId": friend_id,
                        "userPresenceType": 0,
                        "lastLocation": None,
                        "placeId": None,
                        "rootPlaceId": None,
                        "gameId": None,
                        "universeId": None,
                    })
                # Lowest score for offline users
                friend["sortScore"] = float('-inf')

        # Sort friends by sortScore in descending order
        friends_data.sort(key=lambda x: x["sortScore"], reverse=True)

        # Add type information to each friend
        result = [
            self.Friends(friend)
            for friend in friends_data
        ]

        return result

    async def get_currency(self) -> int:
        """
        Grabs the user's current Robux amount. Only works on the authenticated user.

        Returns:
            The user's Robux amount.
        """
        currency_response = await self._client.requests.get(
            url=self._client.url_generator.get_url(
                "economy", f"v1/user/currency")
        )

        try:
            currency_data = currency_response.json()
        except:
            return 0

        return currency_data["robux"]

    async def has_premium(self) -> bool:
        """
        Checks if the user has a Roblox Premium membership.

        Returns:
            Whether the user has Premium or not.
        """
        premium_response = await self._client.requests.get(
            url=self._client.url_generator.get_url(
                "premiumfeatures", f"v1/users/{self.id}/validate-membership")
        )
        premium_data = premium_response.text
        return premium_data == "true"

    async def get_item_instance(self, item_type: InstanceType, item_id: int) -> Optional[ItemInstance]:
        """
        Gets an item instance for a specific user.

        Arguments:
            item_type: The type of item to get an instance for.
            item_id: The item's ID.

        Returns: An ItemInstance, if it exists.
        """

        item_type: str = item_type.value.lower()

        # this is so we can have special classes for other types
        item_class = instance_classes.get(item_type) or ItemInstance

        instance_response = await self._client.requests.get(
            url=self._client.url_generator.get_url(
                "inventory", f"v1/users/{self.id}/items/{item_type}/{item_id}")
        )
        instance_data = instance_response.json()["data"]
        if len(instance_data) > 0:
            return item_class(
                client=self._client,
                data=instance_data[0]
            )
        else:
            return None

    async def get_asset_instance(self, asset: AssetOrAssetId) -> Optional[AssetInstance]:
        """
        Checks if a user owns the asset, and returns details about the asset if they do.

        Returns:
            An asset instance, if the user owns this asset.
        """
        return await self.get_item_instance(
            item_type=InstanceType.asset,
            item_id=int(asset)
        )

    async def get_gamepass_instance(self, gamepass: GamePassOrGamePassId) -> Optional[GamePassInstance]:
        """
        Checks if a user owns the gamepass, and returns details about the asset if they do.

        Returns:
            An gamepass instance, if the user owns this gamepass.
        """
        return await self.get_item_instance(
            item_type=InstanceType.gamepass,
            item_id=int(gamepass)
        )

    async def get_badge_awarded_dates(self, badges: list[BaseBadge]) -> List[PartialBadge]:
        """
        Gets the dates that each badge in a list of badges were awarded to this user.

        Returns:
            A list of partial badges containing badge awarded dates.
        """
        awarded_response = await self._client.requests.get(
            url=self._client.url_generator.get_url(
                "badges", f"v1/users/{self.id}/badges/awarded-dates"),
            params={
                "badgeIds": [badge.id for badge in badges]
            }
        )
        awarded_data: list = awarded_response.json()["data"]
        return [
            PartialBadge(
                client=self._client,
                data=partial_data
            ) for partial_data in awarded_data
        ]

    async def get_group_roles(self) -> List[Role]:
        """
        Gets a list of roles for all groups this user is in.

        Returns:
            A list of roles.
        """
        from ..roles import Role
        from ..groups import Group
        roles_response = await self._client.requests.cache_get(
            url=self._client.url_generator.get_url(
                "groups", f"v1/users/{self.id}/groups/roles")
        )
        roles_data = roles_response.json()["data"]
        return [
            Role(
                client=self._client,
                data=role_data["role"],
                group=Group(
                    client=self._client,
                    data=role_data["group"]
                )
            ) for role_data in roles_data
        ]

    async def get_roblox_badges(self) -> List[RobloxBadge]:
        """
        Gets the user's Roblox badges.

        Returns:
            A list of Roblox badges.
        """

        badges_response = await self._client.requests.cache_get(
            url=self._client.url_generator.get_url(
                "accountinformation", f"v1/users/{self.id}/roblox-badges")
        )
        badges_data = badges_response.json()
        return [RobloxBadge(client=self._client, data=badge_data) for badge_data in badges_data]

    async def get_promotion_channels(self) -> UserPromotionChannels:
        """
        Gets the user's promotion channels.

        Returns:
            The user's promotion channels.
        """
        channels_response = await self._client.requests.cache_get(
            url=self._client.url_generator.get_url(
                "accountinformation", f"v1/users/{self.id}/promotion-channels")
        )
        channels_data = channels_response.json()
        return UserPromotionChannels(
            data=channels_data
        )

    async def _get_friend_channel_count(self, channel: str) -> int:
        count_response = await self._client.requests.get(
            url=self._client.url_generator.get_url(
                "friends", f"v1/users/{self.id}/{channel}/count")
        )
        return count_response.json()["count"]

    def _get_friend_channel_iterator(
            self,
            channel: str,
            page_size: int = 10,
            sort_order: SortOrder = SortOrder.Ascending,
            max_items: int = None
    ) -> PageIterator:
        return PageIterator(
            client=self._client,
            url=self._client.url_generator.get_url(
                "friends", f"v1/users/{self.id}/{channel}"),
            page_size=page_size,
            sort_order=sort_order,
            max_items=max_items,
            handler=lambda client, data: BaseUser(
                client=client, user_id=data["id"])
        )

    async def get_friend_count(self) -> int:
        """
        Gets the user's friend count.

        Returns:
            The user's friend count.
        """
        return await self._get_friend_channel_count("friends")

    async def get_follower_count(self) -> int:
        """
        Gets the user's follower count.

        Returns:
            The user's follower count.
        """
        return await self._get_friend_channel_count("followers")

    async def get_following_count(self) -> int:
        """
        Gets the user's following count.

        Returns:
            The user's following count.
        """
        return await self._get_friend_channel_count("followings")

    def get_followers(
            self,
            page_size: int = 10,
            sort_order: SortOrder = SortOrder.Ascending, max_items: int = None
    ) -> PageIterator:
        """
        Gets the user's followers.

        Returns:
            A PageIterator containing everyone who follows this user.
        """
        return self._get_friend_channel_iterator(
            channel="followers",
            page_size=page_size,
            sort_order=sort_order,
            max_items=max_items,
        )

    def get_followings(
            self,
            page_size: int = 10,
            sort_order: SortOrder = SortOrder.Ascending,
            max_items: int = None
    ) -> PageIterator:
        """
        Gets the user's followings.

        Returns:
            A PageIterator containing everyone that this user is following.
        """
        return self._get_friend_channel_iterator(
            channel="followings",
            page_size=page_size,
            sort_order=sort_order,
            max_items=max_items,
        )

    async def send_friend_request(self) -> bool:
        """
        Sends a friend request to this user. Only works on the authenticated user.

        Returns:
            None
        """
        response = await self._client.requests.post(
            url=self._client._url_generator_roblox.get_url(
                "friends", f"v1/users/{self.id}/request-friendship"
            ),
            json={
                "friendshipOriginSourceType": "PlayerSearch"
            }
        )
        import json
        print(json.dumps(response.json(), indent=2), flush=True)
        print(response.headers, flush=True)
        return response.status_code == 200

    async def accept_friend_request(self) -> bool:
        """
        Accepts a friend request from this user. Only works on the authenticated user.

        Returns:
            None
        """
        response = await self._client.requests.post(
            url=self._client._url_generator_roblox.get_url(
                "friends", f"v1/users/{self.id}/accept-friend-request"
            )
        )
        return response.status_code == 200

    async def decline_friend_request(self) -> bool:
        """
        Declines a friend request from this user. Only works on the authenticated user.

        Returns:
            None
        """
        response = await self._client.requests.post(
            url=self._client._url_generator_roblox.get_url(
                "friends", f"v1/users/{self.id}/decline-friend-request"
            )
        )
        return response.status_code == 200

    async def remove_friend(self) -> bool:
        """
        Removes this user from the authenticated user's friends list.

        Returns:
            None
        """
        response = await self._client.requests.post(
            url=self._client._url_generator_roblox.get_url(
                "friends", f"v1/users/{self.id}/unfriend"
            )
        )
        return response.status_code == 200
