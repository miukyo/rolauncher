"""

This module contains classes intended to parse and deal with data from Roblox plugin information endpoints.

"""
from __future__ import annotations
from typing import TYPE_CHECKING, List
if TYPE_CHECKING:
    from .client import Client
from datetime import datetime

from dateutil.parser import parse

from .bases.baseplugin import BasePlugin
from .utilities.exceptions import PluginNotFound


class Plugin(BasePlugin):
    """
    Represents a Roblox plugin.
    It is intended to parse data from https://develop.roblox.com/v1/plugins.

    Attributes:
        id: The ID of the plugin.
        name: The name of the plugin.
        description: The plugin's description.
        comments_enabled: Whether comments are enabled or disabled.
        version_id: The plugin's current version ID.
        created: When the plugin was created.
        updated: When the plugin was updated.
    """

    def __init__(self, client: Client, data: dict):
        """
        Attributes:
            client: The Client object, which is passed to all objects this Client generates.
            data: data to make the magic happen.
        """
        super().__init__(client=client, plugin_id=data["id"])

        self.id: int = data["id"]
        self.name: str = data["name"]
        self.description: str = data["description"]
        self.comments_enabled: bool = data["commentsEnabled"]
        self.version_id: int = data["versionId"]
        self.created: datetime = parse(data["created"])
        self.updated: datetime = parse(data["updated"])


class PluginProvider:
    """
    Provides methods to interact with Roblox plugins.
    """

    def __init__(self, client: Client):
        """
        Arguments:
            client: The Client to be used when getting plugin information.
        """
        self._client: Client = client

    async def get_plugins(self, plugin_ids: List[int]) -> List[Plugin]:
        """
        Grabs a list of plugins corresponding to each ID in the list.

        Arguments:
            plugin_ids: A list of Roblox plugin IDs.

        Returns:
            A list of Plugins.
        """
        plugins_response = await self._client.requests.get(
            url=self._client.url_generator.get_url(
                "develop", "v1/plugins"
            ),
            params={
                "pluginIds": ",".join(map(str, plugin_ids))
            }
        )
        plugins_data = plugins_response.json()["data"]
        return [Plugin(client=self._client, data=plugin_data) for plugin_data in plugins_data]

    async def get_plugin(self, plugin_id: int) -> Plugin:
        """
        Grabs a plugin with the passed ID.

        Arguments:
            plugin_id: A Roblox plugin ID.

        Returns:
            A Plugin.
        """
        plugins = await self.get_plugins([plugin_id])
        try:
            return plugins[0]
        except IndexError:
            raise PluginNotFound("Invalid plugin.") from None

    def get_base_plugin(self, plugin_id: int) -> BasePlugin:
        """
        Gets a base plugin.

        !!! note
            This method does not send any requests - it just generates an object.
            For more information on bases, please see [Bases](../tutorials/bases.md).

        Arguments:
            plugin_id: A Roblox plugin ID.

        Returns:
            A BasePlugin.
        """
        return BasePlugin(client=self._client, plugin_id=plugin_id)
