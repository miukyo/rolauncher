
import api
import webview
import json
from .user import User


class Realtime:
    def __init__(self, client: api.Client, user_client=None):
        self.client = client
        self.user_client = user_client()
        self.websocket = client.websocket
        if self.websocket:
            self.websocket.on_presence_bulk_notifications(
                self._handle_presence_bulk_notifications)

    def _dispatch_event(self, event_name: str, detail: dict):
        detail_json = json.dumps(detail)
        for main_window in webview.windows:
            try:
                main_window.evaluate_js(
                    f"window.dispatchEvent(new CustomEvent('{event_name}', {{detail: {detail_json}}}))")
            except webview.JavascriptException as e:
                print(
                    f"Error dispatching {event_name} event: {e}", flush=True)

    def _handle_presence_bulk_notifications(self, data: list[dict]):
        ids = [entry["UserId"] for entry in data]
        if not self.user_client:
            return
        presences = self.user_client.get_users_presence(ids)

        self._dispatch_event("presencesUpdate", presences)
