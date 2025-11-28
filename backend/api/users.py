"""

This module contains classes intended to parse and deal with data from Roblox user information endpoints.

"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional, List, Union

if TYPE_CHECKING:
    from .client import Client

from datetime import datetime
from dateutil.parser import parse

from .bases.baseuser import BaseUser
from .partials.partialuser import PartialUser, RequestedUsernamePartialUser, PreviousUsernamesPartialUser
from .utilities.exceptions import UserNotFound, NotFound
from .utilities.iterators import PageIterator


class User(BaseUser):
    """
    Represents a single conversation.

    Attributes:
        id: The id of the current user.
        name: The name of the current user.
        display_name: The display name of the current user.
        is_banned: If the user is banned.
        description: The description the current user wrote for themself.
        created: When the user created their account.
        has_verified_badge: If the user has a verified badge.
    """

    def __init__(self, client: Client, data: dict):
        """
        Arguments:
            client: Client object.
            data: The data from the request.
        """
        super().__init__(client=client, user_id=data["id"])

        self._client: Client = client

        self.name: str = data["name"]
        self.display_name: str = data["displayName"]
        self.is_banned: bool = data["isBanned"]
        self.description: str = data["description"]
        self.created: datetime = parse(data["created"])
        self.has_verified_badge: bool = data["hasVerifiedBadge"]


class UserProvider:
    """
    Provides methods to interact with Roblox users.
    """

    def __init__(self, client: Client):
        """
        Arguments:
            client: The Client to be used when getting user information.
        """
        self._client: Client = client

    async def get_user(self, user_id: int) -> User:
        """
        Gets a user with the specified user ID.

        Arguments:
            user_id: A Roblox user ID.

        Returns:
            A user object.
        """
        try:
            user_response = await self._client.requests.get(
                url=self._client.url_generator.get_url(
                    "users", f"v1/users/{user_id}")
            )
        except NotFound as exception:
            raise UserNotFound(
                message="Invalid user.",
                response=exception.response
            ) from None
        user_data = user_response.json()
        return User(client=self._client, data=user_data)

    async def get_authenticated_user(
            self, expand: bool = True
    ) -> Union[User, PartialUser]:
        """
        Grabs the authenticated user.

        Arguments:
            expand: Whether to return a User (2 requests) rather than a PartialUser (1 request)

        Returns:
            The authenticated user.
        """
        authenticated_user_response = await self._client.requests.get(
            url=self._client.url_generator.get_url(
                "users", f"v1/users/authenticated")
        )
        authenticated_user_data = authenticated_user_response.json()

        if expand:
            return await self.get_user(authenticated_user_data["id"])
        else:
            return PartialUser(client=self._client, data=authenticated_user_data)

    async def get_authenticated_user_from_token(
            self, token: str, expand: bool = True
    ) -> Union[User, PartialUser]:
        """
        Grabs the authenticated user from a .ROBLOSECURITY token.

        Arguments:
            token: A .ROBLOSECURITY token.
            expand: Whether to return a User (2 requests) rather than a PartialUser (1 request)
        Returns:
            The authenticated user.
        """
        from .client import Client
        temp_client = Client(token=token, enable_websocket=False)
        authenticated_user_response = await temp_client.requests.get(
            url=temp_client.url_generator.get_url(
                "users", f"v1/users/authenticated")
        )
        authenticated_user_data = authenticated_user_response.json()
        try:
            if expand:
                return await self.get_user(authenticated_user_data["id"])
            else:
                return PartialUser(client=self._client, data=authenticated_user_data)
        finally:
            del temp_client

    async def get_users(
            self,
            user_ids: List[int],
            exclude_banned_users: bool = False,
            expand: bool = False,
    ) -> Union[List[PartialUser], List[User]]:
        """
        Grabs a list of users corresponding to each user ID in the list.

        Arguments:
            user_ids: A list of Roblox user IDs.
            exclude_banned_users: Whether to exclude banned users from the data.
            expand: Whether to return a list of Users (2 requests) rather than PartialUsers (1 request)

        Returns:
            A List of Users or partial users.
        """
        users_response = await self._client.requests.post(
            url=self._client.url_generator.get_url("users", f"v1/users"),
            json={"userIds": user_ids, "excludeBannedUsers": exclude_banned_users},
        )
        users_data = users_response.json()["data"]

        if expand:
            return [await self.get_user(user_data["id"]) for user_data in users_data]
        else:
            return [
                PartialUser(client=self._client, data=user_data)
                for user_data in users_data
            ]

    async def get_users_by_usernames(
            self,
            usernames: List[str],
            exclude_banned_users: bool = False,
            expand: bool = False,
    ) -> Union[List[RequestedUsernamePartialUser], List[User]]:
        """
        Grabs a list of users corresponding to each username in the list.

        Arguments:
            usernames: A list of Roblox usernames.
            exclude_banned_users: Whether to exclude banned users from the data.
            expand: Whether to return a list of Users (2 requests) rather than RequestedUsernamePartialUsers (1 request)

        Returns:
            A list of User or RequestedUsernamePartialUser, depending on the expand argument.
        """
        users_response = await self._client.requests.post(
            url=self._client.url_generator.get_url(
                "users", f"v1/usernames/users"),
            json={"usernames": usernames,
                  "excludeBannedUsers": exclude_banned_users},
        )
        users_data = users_response.json()["data"]

        if expand:
            return [await self.get_user(user_data["id"]) for user_data in users_data]
        else:
            return [
                RequestedUsernamePartialUser(
                    client=self._client, data=user_data)
                for user_data in users_data
            ]

    async def get_user_by_username(
            self, username: str, exclude_banned_users: bool = False, expand: bool = True
    ) -> Union[RequestedUsernamePartialUser, User]:
        """
        Grabs a user corresponding to the passed username.

        Arguments:
            username: A Roblox username.
            exclude_banned_users: Whether to exclude banned users from the data.
            expand: Whether to return a User (2 requests) rather than a RequestedUsernamePartialUser (1 request)

        Returns:
            A User or RequestedUsernamePartialUser depending on the expand argument.
        """
        users = await self.get_users_by_usernames(
            usernames=[username],
            exclude_banned_users=exclude_banned_users,
            expand=expand,
        )
        try:
            return users[0]
        except IndexError:
            raise UserNotFound("Invalid username.") from None

    def get_base_user(self, user_id: int) -> BaseUser:
        """
        Gets a base user.

        !!! note
            This method does not send any requests - it just generates an object.
            For more information on bases, please see [Bases](../tutorials/bases.md).

        Arguments:
            user_id: A Roblox user ID.

        Returns:
            A BaseUser.
        """
        return BaseUser(client=self._client, user_id=user_id)

    def get_user_search(self, keyword: str, page_size: int = 10,
                        max_items: int = None) -> PageIterator:
        """
        Search for users with a keyword.

        Arguments:
            keyword: A keyword to search for.
            page_size: How many members should be returned for each page.
            max_items: The maximum items to return when looping through this object.

        Returns:
            A PageIterator containing RequestedUsernamePartialUser.
        """
        return PageIterator(
            client=self._client,
            url=self._client.url_generator.get_url(
                "users", f"v1/users/search"),
            page_size=page_size,
            max_items=max_items,
            extra_parameters={"keyword": keyword},
            handler=lambda client, data: PartialUser(
                client=client, data=data),
        )

    class FriendStatus:
        """Represents the friend status between two users."""

        def __init__(self, user_id: int, status: str):
            self.user_id: int = user_id
            self.status: str = status

    async def get_friend_status(self, user_id: int, user_ids: list[int]) -> list[FriendStatus]:
        """
        Gets the friend status between the authenticated user and the specified user.

        Arguments:
            user_id: A Roblox user ID.
            user_ids: A list of Roblox user IDs.
        Returns:
            The friend status.
        """
        response = await self._client.requests.get(
            url=self._client.url_generator.get_url(
                "friends", f"/v1/users/{user_id}/friends/statuses"),
            params={"userIds": ",".join(map(str, user_ids))}
        )

        response_data = response.json()["data"]

        return [
            self.FriendStatus(item["id"], item["status"])
            for item in response_data]
