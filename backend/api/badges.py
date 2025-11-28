"""

This module contains classes intended to parse and deal with data from Roblox badge information endpoints.

"""
from __future__ import annotations
from typing import TYPE_CHECKING

from datetime import datetime
from dateutil.parser import parse

from .bases.baseasset import BaseAsset
from .bases.basebadge import BaseBadge
from .bases.basegamepass import BaseGamePass
from .partials.partialuniverse import PartialUniverse
from .utilities.exceptions import BadgeNotFound, NotFound


if TYPE_CHECKING:
    from .client import Client


class BadgeStatistics:
    """
    Attributes:
        past_day_awarded_count: How many instances of this badge were awarded in the last day.
        awarded_count: How many instances of this badge have been awarded.
        win_rate_percentage: Percentage of players who have joined the parent universe have been awarded this badge.
    """

    def __init__(self, data: dict):
        """
        Arguments:
            data: The raw input data.
        """
        self.past_day_awarded_count: int = data["pastDayAwardedCount"]
        self.awarded_count: int = data["awardedCount"]
        self.win_rate_percentage: int = data["winRatePercentage"]

    def __repr__(self):
        return f"<{self.__class__.__name__} past_day_awarded_count={self.past_day_awarded_count} awarded_count={self.awarded_count} win_rate_percentage={self.win_rate_percentage}>"


class Badge(BaseBadge):
    """
    Represents a badge from the API.

    Attributes:
        id: The badge Id.
        name: The name of the badge.
        description: The badge description.
        display_name: The localized name of the badge.
        display_description: The localized badge description.
        enabled: Whether or not the badge is enabled.
        icon: The badge icon.
        display_icon: The localized badge icon.
        created: When the badge was created.
        updated: When the badge was updated.
        statistics: Badge award statistics.
        awarding_universe: The universe the badge is being awarded from.
    """

    def __init__(self, client: Client, data: dict):
        """
        Arguments:
            client: The Client to be used when getting information on badges.
            data: The data from the endpoint.
        """
        self.id: int = data["id"]

        super().__init__(client=client, badge_id=self.id)

        self.name: str = data["name"]
        self.description: str = data["description"]
        self.display_name: str = data["displayName"]
        self.display_description: str = data["displayDescription"]
        self.enabled: bool = data["enabled"]
        self.icon: BaseAsset = BaseAsset(
            client=client, asset_id=data["iconImageId"])
        self.display_icon: BaseAsset = BaseAsset(
            client=client, asset_id=data["displayIconImageId"])
        self.created: datetime = parse(data["created"])
        self.updated: datetime = parse(data["updated"])

        self.statistics: BadgeStatistics = BadgeStatistics(
            data=data["statistics"])
        self.awarding_universe: PartialUniverse = PartialUniverse(
            client=client, data=data["awardingUniverse"])


class BadgeProvider:
    """
    Provides methods to interact with Roblox badges and gamepasses.
    """

    def __init__(self, client: Client):
        """
        Arguments:
            client: The Client to be used when getting badge information.
        """
        self._client: Client = client

    async def get_badge(self, badge_id: int) -> Badge:
        """
        Gets a badge with the passed ID.

        Arguments:
            badge_id: A Roblox badge ID.

        Returns:
            A Badge.
        """
        try:
            badge_response = await self._client.requests.get(
                url=self._client.url_generator.get_url(
                    "badges", f"v1/badges/{badge_id}"
                )
            )
        except NotFound as exception:
            raise BadgeNotFound(
                message="Invalid badge.",
                response=exception.response
            ) from None
        badge_data = badge_response.json()
        return Badge(client=self._client, data=badge_data)

    def get_base_badge(self, badge_id: int) -> BaseBadge:
        """
        Gets a base badge.

        !!! note
            This method does not send any requests - it just generates an object.
            For more information on bases, please see [Bases](../tutorials/bases.md).

        Arguments:
            badge_id: A Roblox badge ID.

        Returns:
            A BaseBadge.
        """
        return BaseBadge(client=self._client, badge_id=badge_id)

    def get_base_gamepass(self, gamepass_id: int) -> BaseGamePass:
        """
        Gets a base gamepass.

        !!! note
            This method does not send any requests - it just generates an object.
            For more information on bases, please see [Bases](../tutorials/bases.md).

        Arguments:
            gamepass_id: A Roblox gamepass ID.

        Returns: A BaseGamePass.
        """
        return BaseGamePass(client=self._client, gamepass_id=gamepass_id)
