import api
import trio
from api.users import User
from .database import get_last_account


class Friends:
    def __init__(self, client: api.Client):
        self.client = client
        self.current_user_id = None
        self.friends_raw = None

    def get_authed_friends(self, iterate: tuple = (0, 15)):
        async def fetch():
            id = int(get_last_account().get("id"))
            if self.current_user_id != id or not self.friends_raw:
                self.current_user_id = id
                self.friends_raw = await self.client.users.get_base_user(id).get_friendsv2()
            friends_data = self.friends_raw[iterate[0]:min(
                iterate[1], len(self.friends_raw))]
            friends_ids = [friend.id for friend in friends_data]

            friends = []
            images_headshot = []
            images_bust = []

            async def fetch_images_headshot():
                nonlocal images_headshot
                images_headshot = await self.client.thumbnails.get_user_avatar_thumbnails(
                    friends_ids, api.AvatarThumbnailType.headshot, (100, 100), image_format=api.ThumbnailFormat.webp)

            async def fetch_images_bust():
                nonlocal images_bust
                images_bust = await self.client.thumbnails.get_user_avatar_thumbnails(
                    friends_ids, api.AvatarThumbnailType.full_body, (420, 420), image_format=api.ThumbnailFormat.webp)

            async with trio.open_nursery() as nursery:
                nursery.start_soon(fetch_images_headshot)
                nursery.start_soon(fetch_images_bust)

            for friend in friends_data:
                # Safely extract presence data
                presence_type = "offline"
                root_place_id = None
                universe_id = None
                job_id = None
                last_location = None

                if friend.presence:
                    presence_type = friend.presence.user_presence_type.name
                    place_id = friend.presence.place.id if friend.presence.place else None
                    root_place_id = friend.presence.root_place.id if friend.presence.root_place else None
                    universe_id = friend.presence.universe.id if friend.presence.universe else None
                    job_id = friend.presence.job.id if friend.presence.job else None
                    last_location = friend.presence.last_location

                friends.append({
                    "id": friend.id,
                    "name": friend.name,
                    "displayName": friend.displayName,
                    "presence": {
                        "type": presence_type,
                        "place": root_place_id,
                        "universe": universe_id,
                        "job": job_id,
                        "lastLocation": last_location
                    },
                    "friendStatus": "Friends",
                    "image": next(image.image_url for image in images_headshot if image.target_id == friend.id),
                    "imageBust": next(image.image_url for image in images_bust if image.target_id == friend.id)
                })
            return friends

        return trio.run(fetch)

    def send_friend_request(self, user_id: int):
        async def fetch():
            return await self.client.users.get_base_user(user_id).send_friend_request()

        return trio.run(fetch)

    def remove_friend(self, user_id: int):
        async def fetch():
            return await self.client.users.get_base_user(user_id).remove_friend()
        return trio.run(fetch)

    def accept_friend_request(self, user_id: int):
        async def fetch():
            return await self.client.users.get_base_user(user_id).accept_friend_request()

        return trio.run(fetch)

    def decline_friend_request(self, user_id: int):
        async def fetch():
            return await self.client.users.get_base_user(user_id).decline_friend_request()

        return trio.run(fetch)
