"""

ro.py  
A modern, asynchronous wrapper for the Roblox web API.

Copyright 2020-present jmkdev  
License: MIT, see LICENSE

"""

__title__ = "roblox"
__author__ = "jmkdev"
__license__ = "MIT"
__copyright__ = "Copyright 2020-present jmkdev"
__version__ = "2.0.0"

import logging

from .client import Client
from .creatortype import CreatorType
from .thumbnails import ThumbnailState, ThumbnailFormat, ThumbnailReturnPolicy, AvatarThumbnailType
from .universes import UniverseGenre, UniverseAvatarType, UniverseIterator
from .users import UserProvider
from .groups import GroupProvider
from .universes import UniverseProvider
from .places import PlaceProvider
from .assets import AssetProvider
from .plugins import PluginProvider
from .badges import BadgeProvider
from .utilities.exceptions import *
from .utilities.types import *

logging.getLogger(__name__).addHandler(logging.NullHandler())
