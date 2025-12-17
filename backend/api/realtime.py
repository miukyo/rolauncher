from signalrcore import hub_connection_builder
import json


class WebSocketBuilder:
    def __init__(self, url: str, token: str):
        self.url = url
        self.token = token
        self._event_handlers = {}
        self.hub_connection = None
        self._start()

    def _build_connection(self, url: str, token: str):
        return hub_connection_builder.HubConnectionBuilder()\
            .with_url(
            url,
            options={
                "skip_negotiation": True,
                "headers": {
                    "Cookie": f".ROBLOSECURITY={token}"
                }
            }
        ).build()

    def _start(self):
        if self.hub_connection:
            try:
                self.hub_connection.stop()
            except:
                pass

        self.hub_connection = self._build_connection(self.url, self.token)
        self.hub_connection.on_open(
            lambda: print("Connection opened", flush=True))
        self.hub_connection.on("notification", self._on_notification)
        self.hub_connection.on("subscriptionStatus",
                               self._on_subscription_status)
        self.hub_connection.on_error(self._start)
        self.hub_connection.on_close(self._start)
        self.hub_connection.start()

    def set_token(self, new_token: str):
        self.token = new_token
        self._start()

    def _on_notification(self, data):
        print(f"Notification received: {json.dumps(data)}", flush=True)

        # Data format: [notification_type, json_payload, sequence]
        if isinstance(data, list) and len(data) >= 2:
            notification_type = data[0]
            payload_str = data[1]

            # Parse the JSON payload
            try:
                payload = json.loads(payload_str)
            except json.JSONDecodeError:
                print(f"Failed to parse payload: {payload_str}", flush=True)
                return

            # Call the appropriate handler callback if set
            handler = self._event_handlers.get(notification_type)
            if handler and callable(handler):
                handler(payload)

    def _on_subscription_status(self, data):
        print(f"Subscription status received: {json.dumps(data)}", flush=True)

    # Event registration methods
    def on_game_close_notifications(self, handler):
        self._event_handlers["GameCloseNotifications"] = handler
        return self

    def on_friendship_notifications(self, handler):
        self._event_handlers["FriendshipNotifications"] = handler
        return self

    def on_notification_stream(self, handler):
        self._event_handlers["NotificationStream"] = handler
        return self

    def on_chat_notifications(self, handler):
        self._event_handlers["ChatNotifications"] = handler
        return self

    def on_display_name_notifications(self, handler):
        self._event_handlers["DisplayNameNotifications"] = handler
        return self

    def on_avatar_outfit_ownership_notifications(self, handler):
        self._event_handlers["AvatarOutfitOwnershipNotifications"] = handler
        return self

    def on_avatar_asset_ownership_notifications(self, handler):
        self._event_handlers["AvatarAssetOwnershipNotifications"] = handler
        return self

    def on_presence_bulk_notifications(self, handler):
        self._event_handlers["PresenceBulkNotifications"] = handler
        return self

    def on_toast_in_app_and_experience_notifications(self, handler):
        self._event_handlers["toast-in-app-and-experience-notifications"] = handler
        return self

    def on_cloud_edit_chat_notifications(self, handler):
        self._event_handlers["CloudEditChatNotifications"] = handler
        return self

    def on_communication_channels(self, handler):
        self._event_handlers["CommunicationChannels"] = handler
        return self

    def on_activity_history_event(self, handler):
        self._event_handlers["ActivityHistoryEvent"] = handler
        return self

    def on_user_tag_change_notification(self, handler):
        self._event_handlers["UserTagChangeNotification"] = handler
        return self

    def on_user_profile_notifications(self, handler):
        self._event_handlers["UserProfileNotifications"] = handler
        return self

    def on_game_favorite_notifications(self, handler):
        self._event_handlers["GameFavoriteNotifications"] = handler
        return self

    def on_toast_in_experience_notifications(self, handler):
        self._event_handlers["toast-in-experience-notifications"] = handler
        return self

    def on_chat_moderation_type_eligibility(self, handler):
        self._event_handlers["ChatModerationTypeEligibility"] = handler
        return self

    def on_message_notification(self, handler):
        self._event_handlers["MessageNotification"] = handler
        return self

    def on_asset_dependency_grant_event(self, handler):
        self._event_handlers["AssetDependencyGrantEvent"] = handler
        return self

    def on_authentication_notifications(self, handler):
        self._event_handlers["AuthenticationNotifications"] = handler
        return self

    def on_voice_notifications(self, handler):
        self._event_handlers["VoiceNotifications"] = handler
        return self

    def on_experience_invite_update(self, handler):
        self._event_handlers["ExperienceInviteUpdate"] = handler
        return self

    def on_party_nudge_updated(self, handler):
        self._event_handlers["PartyNudgeUpdated"] = handler
        return self

    def on_challenge_dialog_notification(self, handler):
        self._event_handlers["ChallengeDialogNotification"] = handler
        return self
