import trio
import api
from .database import get_last_account
from .games import Games


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
            try:
                iterator = self.client.users.get_user_search(query, page_size)
                users = await iterator.next()
                return await self._transform_users(users)
            except Exception as e:
                print(f"Error searching users: {e}")
                return []
        return trio.run(fetch)

    async def _transform_users(self, users: list, fetch_friend_status: bool = True):
        results = []
        if not users:
            return results

        # Normalize input to list of dicts/objects with accessable attributes
        # We need IDs.
        user_ids = []
        for u in users:
            if hasattr(u, "id"):
                user_ids.append(u.id)
            elif isinstance(u, dict) and "id" in u:
                user_ids.append(u["id"])

        if not user_ids:
            return []

        presences = []
        images_headshot = []
        friend_statuses = []

        async def fetch_presences():
            try:
                presences.extend(
                    await self.client.presence.get_user_presences(user_ids)
                )
            except Exception as e:
                print(f"Error fetching presences: {e}")

        async def fetch_images_headshot():
            try:
                images_headshot.extend(
                    await self.client.thumbnails.get_user_avatar_thumbnails(
                        user_ids,
                        api.AvatarThumbnailType.headshot,
                        (150, 150),
                        image_format=api.ThumbnailFormat.webp
                    )
                )
            except Exception as e:
                print(f"Error fetching thumbnails: {e}")

        async def fetch_friend_statuses():
            nonlocal friend_statuses
            if fetch_friend_status:
                try:
                    current_user_id = int(get_last_account().get("id"))
                    friend_statuses = await self.client.users.get_friend_status(
                        current_user_id,
                        user_ids
                    )
                except Exception as e:
                    print(f"Error fetching friend statuses: {e}")

        async with trio.open_nursery() as nursery:
            nursery.start_soon(fetch_presences)
            nursery.start_soon(fetch_images_headshot)
            nursery.start_soon(fetch_friend_statuses)

        status_map = {s.user_id: str(s.status).split(
            '.')[-1] for s in friend_statuses} if friend_statuses else {}

        for user in users:
            # Handle both object and dict
            uid = user.id
            name = user.name
            display_name = user.displayName if hasattr(
                user, "displayName") else user.display_name

            # Fallback if names missing (e.g. from ID-only BaseUser)
            if not name:
                name = str(uid)
            if not display_name:
                display_name = str(uid)

            presence = next(
                (p for p in presences if p.user.id == uid), None)

            image = next(
                (i.image_url for i in images_headshot if i.target_id == uid), "")

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
                "id": uid,
                "name": name,
                "displayName": display_name,
                "image": image,
                "friendStatus": status_map.get(uid, "NotFriends"),
                "presence": {
                    "type": presence_type,
                    "place": root_place_id,
                    "universe": universe_id,
                    "job": job_id,
                    "lastLocation": last_location
                }
            })
        return results

    def get_user_friends(self, user_id: int):
        async def fetch():
            friends_raw = await self.client.users.get_base_user(user_id).get_friendsv2()
            return await self._transform_users(friends_raw)
        return trio.run(fetch)

    def get_user_followers(self, user_id: int):
        async def fetch():
            # Manually fetch since BaseUser iterator loses name data
            url = self.client.url_generator.get_url(
                "friends", f"v1/users/{user_id}/followers")
            response = await self.client.requests.get(url, params={"limit": 50, "sortOrder": "Desc"})
            data = response.json().get("data", [])
            users = await self.client.users.get_users([user["id"] for user in data])
            return await self._transform_users(users)
        return trio.run(fetch)

    def get_user_following(self, user_id: int):
        async def fetch():
            # Manually fetch since BaseUser iterator loses name data
            url = self.client.url_generator.get_url(
                "friends", f"v1/users/{user_id}/followings")
            response = await self.client.requests.get(url, params={"limit": 50, "sortOrder": "Desc"})
            data = response.json().get("data", [])
            users = await self.client.users.get_users([user["id"] for user in data])
            return await self._transform_users(users)
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

    def get_user_info(self, user_id: int = None):
        async def fetch():
            current_user_id = int(get_last_account().get("id"))
            target_id = user_id if user_id else current_user_id

            base = await self.client.users.get_user(target_id)

            image = await self.client.thumbnails.get_user_avatar_thumbnails(
                [target_id], api.AvatarThumbnailType.headshot, (420, 420)
            )

            # Fetch presence and friend status
            presence = None
            friend_status = "NotFriends"

            presences = await self.client.presence.get_user_presences([target_id])
            if presences:
                presence = presences[0]

            if target_id != current_user_id:
                try:
                    statuses = await self.client.users.get_friend_status(current_user_id, [target_id])
                    if statuses:
                        friend_status = str(statuses[0].status).split('.')[-1]
                except:
                    pass
            else:
                friend_status = "Self"

            presence_dict = None
            if presence:
                presence_dict = {
                    "type": presence.user_presence_type.name,
                    "place": presence.place.id if presence.place else None,
                    "universe": presence.universe.id if presence.universe else None,
                    "job": presence.job.id if presence.job else None,
                    "lastLocation": presence.last_location
                }

            return {
                "id": base.id,
                "name": base.name,
                "displayName": base.display_name,
                "image": image[0].image_url,
                "presence": presence_dict,
                "friendStatus": friend_status
            }
        return trio.run(fetch)

    def get_user_groups(self, user_id: int = None):
        async def fetch():
            id = user_id if user_id else get_last_account().get("id")
            user = self.client.users.get_base_user(id)
            roles = await user.get_group_roles()
            groups = []

            group_ids = list(set([role.group.id for role in roles]))

            thumbnails = []
            if group_ids:
                thumbnails = await self.client.thumbnails.get_group_icons(
                    group_ids, (150, 150)
                )

            for role in roles:
                image = next(
                    (t.image_url for t in thumbnails if t.target_id == role.group.id), None)
                groups.append({
                    "id": role.group.id,
                    "name": role.group.name,
                    "memberCount": role.group.member_count,
                    "rank": role.rank,
                    "role": role.name,
                    "image": image
                })
            return groups

        return trio.run(fetch)

    def get_user_badges(self, user_id: int = None):
        async def fetch():
            id = user_id if user_id else get_last_account().get("id")
            user = self.client.users.get_base_user(id)
            badges = await user.get_roblox_badges()
            return [{
                "id": badge.id,
                "name": badge.name,
                "description": badge.description,
                "imageUrl": badge.image_url
            } for badge in badges]

        return trio.run(fetch)

    def get_user_social_links(self, user_id: int = None):
        async def fetch():
            id = user_id if user_id else get_last_account().get("id")
            user = self.client.users.get_base_user(id)
            try:
                channels = await user.get_promotion_channels()
                return {
                    "facebook": channels.facebook,
                    "twitter": channels.twitter,
                    "youtube": channels.youtube,
                    "twitch": channels.twitch,
                    "guilded": channels.guilded
                }
            except:
                return {}

        return trio.run(fetch)

    def get_user_creations(self, user_id: int = None):
        async def fetch():
            id = user_id if user_id else get_last_account().get("id")
            response = await self.client.requests.cache_get(
                url=self.client.url_generator.get_url(
                    "games", f"v2/users/{id}/games"),
                params={"accessFilter": 2, "limit": 50, "sortOrder": "Asc"}
            )
            data = response.json().get("data", [])
            game_ids = [g.get("id") for g in data]

            if not game_ids:
                return []

            universes = await self.client.universes.get_universes(game_ids)
            games_mapping = Games(self.client)
            items = await games_mapping._get_page_items(universes)
            del games_mapping
            return items

        return trio.run(fetch)

    def get_user_favorites(self, user_id: int = None):
        async def fetch():
            id = user_id if user_id else get_last_account().get("id")
            # Using v2 endpoint for user favorites
            response = await self.client.requests.cache_get(
                url=self.client.url_generator.get_url(
                    "games", f"v2/users/{id}/favorite/games"),
                params={"accessFilter": 2, "limit": 50}
            )
            data = response.json().get("data", [])
            game_ids = [g.get("id") for g in data]

            if not game_ids:
                return []

            universes = await self.client.universes.get_universes(game_ids)
            games_mapping = Games(self.client)
            items = await games_mapping._get_page_items(universes)
            del games_mapping
            return items

        return trio.run(fetch)

    def get_user_3d_avatar(self, user_id: int):
        async def fetch():
            try:
                thumbnail = await self.client.thumbnails.get_user_avatar_thumbnail_3d(user_id)

                response = await self.client.requests.cache_get(
                    url=self.client.url_generator.get_url(
                        "avatar", f"v2/avatar/users/{user_id}/avatar"),
                )
                render = response.json()

                data = await thumbnail.get_3d_data()
                return {
                    "obj": data.obj.get_url(),
                    "mtl": data.mtl.get_url(),
                    "textures": [t.get_url() for t in data.textures],
                    "camera": {
                        "position": {"x": data.camera.position.x, "y": data.camera.position.y, "z": data.camera.position.z},
                        "direction": {"x": data.camera.direction.x, "y": data.camera.direction.y, "z": data.camera.direction.z},
                        "fov": data.camera.fov
                    },
                    "aabb": {
                        "min": {"x": data.aabb.min.x, "y": data.aabb.min.y, "z": data.aabb.min.z},
                        "max": {"x": data.aabb.max.x, "y": data.aabb.max.y, "z": data.aabb.max.z}
                    },
                    "bodyColors": render.get("bodyColor3s", {})
                }
            except Exception as e:
                print(f"Error fetching 3D avatar for user {user_id}: {e}")
                return None

        return trio.run(fetch)
