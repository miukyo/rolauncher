from io import BytesIO
import time
from PIL import Image
import urllib.parse
import uuid
import os
import psutil
from typing import Literal

import trio
import api
import mapping.auth
import webview
import winshell
from pathlib import Path


class Utility:
    def __init__(self, client: api.Client, auth_client):
        self.client = client
        self.auth_client: mapping.auth.Auth = auth_client()

    def launch_roblox(self, launch_mode: Literal["Play", "Edit"], ticket: str = None, place_id: int = None, follow_user_id: int = None, job_id: str = None, private_id: str = None) -> str:
        """
        Generates a Roblox URI for launching the Roblox Player or Studio.
        """
        timestamp = str(int(time.time() * 1000))  # time in milliseconds
        base_uri = "roblox-player:1"
        attempt_id = str(uuid.uuid4())
        ticket = self.auth_client.get_authentication_ticket() if ticket is None else ticket
        print("Creating Roblox URI with params:", {
            "launch_mode": launch_mode,
            "place_id": place_id,
            "follow_user_id": follow_user_id,
            "job_id": job_id,
            "private_id": private_id
        })

        place_launcher_url = "https://www.roblox.com/Game/PlaceLauncher.ashx"

        if launch_mode == "Play":

            # Build the placeLauncherURL query string
            if follow_user_id:
                place_launcher_url += (
                    f"?request=RequestFollowUser&userId={follow_user_id}"
                    f"&joinAttemptOrigin=JoinUser+joinAttemptId:{attempt_id}"
                )
            elif job_id and place_id:
                place_launcher_url += (
                    f"?request=RequestGameJob&placeId={place_id}"
                    f"&gameId={job_id}"
                    f"&joinAttemptOrigin=publicServerListJoin+joinAttemptId:{attempt_id}"
                )
            elif private_id and place_id:
                # Note: Spelling matches original JS 'pirvateId'
                place_launcher_url += (
                    f"?request=RequestPrivateGame&placeId={place_id}"
                    f"&accessCode={private_id}"
                    f"&joinAttemptOrigin=privateServerListJoin+joinAttemptId:{attempt_id}"
                )
            elif place_id:
                place_launcher_url += (
                    f"?request=RequestGame&placeId={place_id}"
                    f"&joinAttemptOrigin=PlayButton+joinAttemptId:{attempt_id}"
                )
            else:
                # Handle case where no specific parameters are provided for Play
                # This branch is implicit in the original JS but good to have
                raise ValueError("Insufficient parameters for 'Play' mode.")

            encoded_url = urllib.parse.quote(place_launcher_url)

            if not ticket:
                raise Exception("Failed to get authentication ticket")

            final_uri = (
                f"{base_uri}+launchmode:play+launchtime:{timestamp}+"
                f"gameinfo:{ticket}+placelauncherurl:{encoded_url}"
            )

            os.startfile(final_uri)

            # Wait for RobloxPlayerBeta.exe to start
            timeout = 5  # seconds
            start_time = time.time()
            while time.time() - start_time < timeout:
                for proc in psutil.process_iter(['name']):
                    if proc.info['name'] == 'RobloxPlayerBeta.exe':
                        for window in webview.windows:
                            window.minimize()
                        return True
                time.sleep(0.5)
            return False

        # elif launch_mode == "Edit":

        #     # This part requires access to the UserStore structure.
        #     # We assume MockUserStore.get_current_user() is the equivalent of UserStore.user[0]()
        #     user = UserStore.get_current_user()
        #     user_id = user.id if user else 0

        #     # Check for 'universeId' which is guaranteed by the EditParams type
        #     if 'universeId' in props:
        #         return (
        #             f"{base_uri}launchmode:edit+task:EditPlace+"
        #             f"placeId:{props['placeId']}+universeId:{props['universeId']}+"
        #             f"userId:{user_id}"
        #         )

        raise ValueError("Invalid parameters for CreateRobloxURI")

    def launch_roblox_with_id(self, launch_mode: Literal["Play", "Edit"], account_id: int, place_id: int = None, follow_user_id: int = None, job_id: str = None, private_id: str = None) -> str:
        account = self.auth_client.get_account(account_id)
        ticket = self.auth_client.get_authentication_ticket_from_token(
            account['cookie'])
        return self.launch_roblox(
            launch_mode=launch_mode,
            ticket=ticket,
            place_id=place_id,
            follow_user_id=follow_user_id,
            job_id=job_id,
            private_id=private_id
        )

    def create_shortcut(self, game_name: str, place_id: int, account_name: str, account_id: int, image_url: str):
        print(
            f"Creating shortcut for account ID {account_id} with place ID {place_id}...,{image_url}")

        async def create():
            icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128)]
            local_app_data = Path(os.getenv('LOCALAPPDATA'))
            img_path = local_app_data / 'RoLauncher' / \
                'game_icons' / f"{game_name}.ico"
            img_path.parent.mkdir(parents=True, exist_ok=True)

            if not img_path.exists():
                try:
                    response = await self.client.requests.get(url=image_url)
                    response.raise_for_status()

                    image_data = BytesIO(response.content)
                    img = Image.open(image_data)

                    if img.mode not in ('RGB', 'RGBA'):
                        img = img.convert('RGBA')

                    img.save(str(img_path), format='ICO', sizes=icon_sizes)

                except Exception:
                    return False

            desktop = winshell.desktop()
            path = os.path.join(desktop, f"{game_name} - {account_name}.lnk")
            with winshell.Shortcut(path) as link:
                link.path = os.path.join(os.getcwd(), "RoLauncher.exe")
                link.arguments = f'--cli --account-id {account_id} --mode Play --place-id {place_id}'
                link.description = f"Launch {game_name} with {account_name} account on Roblox"
                link.icon_location = (str(img_path), 0)

            return True

        return trio.run(create)
