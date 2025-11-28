import trio
import webview
import api
import mapping.database as database


class Auth:
    def __init__(self, client: api.Client):
        self.client = client

    def _login_prompt(self):
        loginwindow: webview.Window = webview.create_window(
            'Login', 'https://www.roblox.com/login', min_size=(400, 600), frameless=False)

        async def check_cookie():
            while True:
                cookies = loginwindow.get_cookies()
                if not cookies:
                    await trio.sleep(1)
                    continue
                for c in cookies:
                    roblosecurity = c.get('.ROBLOSECURITY')
                    if roblosecurity:
                        cookie_value = roblosecurity.value
                        user_info = await self.client.users.get_authenticated_user_from_token(cookie_value)
                        loginwindow.destroy()
                        return {
                            'id': user_info.id,
                            'name': user_info.name,
                            'displayName': user_info.display_name,
                            'cookie': cookie_value
                        }
                await trio.sleep(1)

        return trio.run(check_cookie)

    def login(self):
        account = self._login_prompt()
        database.save_user_info({
            'id': account['id'],
            'name': account['name'],
            'displayName': account['displayName'],
        }, account['cookie'])
        self.switch_account(account['id'])

        return {
            'id': account['id'],
            'name': account['name'],
            'displayName': account['displayName'],
        }

    def switch_account(self, account_id):
        account = self.get_account(account_id)
        self.client.set_token(account['cookie'])
        database.set_last_account(account_id)
        return {
            'id': account['id'],
            'name': account['name'],
            'displayName': account['display_name'],
        }

    def get_last_account(self):
        return database.get_last_account()

    def purge_database(self):
        database.purge_database()

    def get_all_accounts(self):
        async def fetch():
            accounts = database.get_all_accounts()
            accounts_ids = [account['id'] for account in accounts]
            image = await self.client.thumbnails.get_user_avatar_thumbnails(
                accounts_ids, api.AvatarThumbnailType.headshot, (48, 48)
            )
            return [
                {
                    'id': account['id'],
                    'name': account['name'],
                    'displayName': account['display_name'],
                    'image': next(
                        (img.image_url for img in image if img.target_id ==
                         account['id']), None
                    )
                }
                for account in accounts
            ]

        return trio.run(fetch)

    def get_account(self, account_id):
        return database.get_account(account_id)

    def delete_account(self, account_id):
        database.delete_account(account_id)

    def get_authentication_ticket(self):
        return trio.run(self.client.get_authentication_ticket)

    def get_authentication_ticket_from_token(self, token: str):
        async def fetch_ticket():
            return await self.client.get_authentication_ticket_from_token(token)
        return trio.run(fetch_ticket)
