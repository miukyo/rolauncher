import trio
import api
from .database import get_last_account


class User:
    def __init__(self, client: api.Client):
        self.client = client

    def get_authed_user(self):
        async def fetch():
            id = get_last_account().get("id")
            base = await self.client.users.get_authenticated_user(False)
            robux = await self.client.users.get_base_user(id).get_currency()
            image = await self.client.thumbnails.get_user_avatar_thumbnails(
                [id], api.AvatarThumbnailType.headshot, (48, 48)
            )
            return {
                "id": base.id,
                "name": base.name,
                "displayName": base.display_name,
                "robux": robux,
                "image": image[0].image_url
            }

        return trio.run(fetch)

    def get_followers_count(self, id: int):
        async def fetch():
            try:
                follower_count = await self.client.users.get_base_user(id).get_follower_count()
                following_count = await self.client.users.get_base_user(id).get_following_count()
                friends_count = await self.client.users.get_base_user(id).get_friend_count()
                return {
                    "followersCount": follower_count,
                    "followingCount": following_count,
                    "friendCount": friends_count
                }
            except (KeyError, Exception) as e:
                print(f"Error fetching follower counts for user {id}: {e}")
                return {
                    "followersCount": 0,
                    "followingCount": 0,
                    "friendCount": 0
                }

        return trio.run(fetch)

    def search_users(self, query: str, page_size: int = 50):
        async def fetch():
            iterator = self.client.users.get_user_search(query, page_size)
            users = await iterator.next()
            results = []
            presences = []
            images_headshot = []
            friend_statuses = []

            async def fetch_presences():
                presences.extend(
                    await self.client.presence.get_user_presences([user.id for user in users])
                )

            async def fetch_images_headshot():
                images_headshot.extend(
                    await self.client.thumbnails.get_user_avatar_thumbnails(
                        [user.id for user in users],
                        api.AvatarThumbnailType.headshot,
                        (100, 100),
                        image_format=api.ThumbnailFormat.webp
                    )
                )

            async def fetch_friend_statuses():
                nonlocal friend_statuses
                friend_statuses = await self.client.users.get_friend_status(
                    int(get_last_account().get("id")),
                    [user.id for user in users]
                )
            async with trio.open_nursery() as nursery:
                nursery.start_soon(fetch_presences)
                nursery.start_soon(fetch_images_headshot)
                nursery.start_soon(fetch_friend_statuses)

            for user in users:
                presence = next(
                    (p for p in presences if p.user.id == user.id), None)
                presence_type = "offline"
                root_place_id = None
                universe_id = None
                job_id = None
                last_location = None

                if presence:
                    presence_type = presence.user_presence_type.name
                    place_id = presence.place.id if presence.place else None
                    root_place_id = presence.root_place.id if presence.root_place else None
                    universe_id = presence.universe.id if presence.universe else None
                    job_id = presence.job.id if presence.job else None
                    last_location = presence.last_location

                results.append({
                    "id": user.id,
                    "name": user.name,
                    "displayName": user.display_name,
                    "presence": {
                        "type": presence_type,
                        "place": root_place_id,
                        "universe": universe_id,
                        "job": job_id,
                        "lastLocation": last_location
                    },
                    "friendStatus": next(
                        (status.status for status in friend_statuses if status.user_id ==
                         user.id), "NotFriends"
                    ),
                    "image": next((image.image_url for image in images_headshot if image.target_id == user.id), None)
                })
            return results

        return trio.run(fetch)

    def get_users_presence(self, user_ids: list):
        async def fetch():
            presences = await self.client.presence.get_user_presences(user_ids)
            results = []

            for presence in presences:
                presence_type = "offline"
                root_place_id = None
                universe_id = None
                job_id = None
                last_location = None

                if presence:
                    presence_type = presence.user_presence_type.name
                    place_id = presence.place.id if presence.place else None
                    root_place_id = presence.root_place.id if presence.root_place else None
                    universe_id = presence.universe.id if presence.universe else None
                    job_id = presence.job.id if presence.job else None
                    last_location = presence.last_location

                results.append({
                    "id": presence.user.id,
                    "presence": {
                        "type": presence_type,
                        "place": root_place_id,
                        "universe": universe_id,
                        "job": job_id,
                        "lastLocation": last_location
                    }
                })
            return results

        return trio.run(fetch)
