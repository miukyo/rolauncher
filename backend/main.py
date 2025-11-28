import os
import sys
import argparse
import webview
import api
import ctypes
import psutil
import threading
import time


from mapping.realtime import Realtime
from updater import Updater
from mapping.utility import Utility
from mapping.auth import Auth
from mapping.user import User
from mapping.friends import Friends
from mapping.games import Games
from mapping.database import initialize_database, get_last_account, get_account


class Api:
    def __init__(self, client):
        self.client = client
        self.auth = Auth(client)
        self.user = User(client)
        self.games = Games(client)
        self.friends = Friends(client)
        self.utility = Utility(client, lambda: self.auth)
        Realtime(client, lambda: self.user)


class Cli_Api:
    def __init__(self, client):
        self.client = client
        self.auth = Auth(client)
        self.utility = Utility(client, lambda: self.auth)


def run_cli(args):
    """Run CLI mode to launch Roblox directly"""
    try:
        initialize_database()
        token = get_account(args.account_id).get(
            'cookie') if get_account(args.account_id) else None
        if token is None:
            raise ValueError(f"No account found with ID: {args.account_id}")
        client = api.Client(token=token, enable_websocket=False)
        cli_api = Cli_Api(client)
        print(f"Launching Roblox with account ID: {args.account_id}")
        cli_api.utility.launch_roblox(
            launch_mode=args.mode,
            place_id=args.place_id,
            follow_user_id=args.follow_user,
            job_id=args.job_id,
            private_id=args.private_id
        )
        print("Roblox launched successfully!")
        sys.exit(0)
    except (Exception, ValueError) as e:
        error_msg = f"Error launching Roblox: {e}"
        print(error_msg)
        ctypes.windll.user32.MessageBoxW(
            0, error_msg, "RoLauncher Error", 0x10)

        sys.exit(1)


def monitor_roblox_process():
    """Monitor Roblox process and show window when it closes"""
    roblox_was_running = False

    while True:
        roblox_running = False
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] == 'RobloxPlayerBeta.exe':
                    roblox_running = True
                    roblox_was_running = True
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        # If Roblox was running but now it's not, show the window
        if roblox_was_running and not roblox_running:
            for window in webview.windows:
                window.restore()
            roblox_was_running = False

        time.sleep(1)


def run_gui():
    """Run GUI mode with webview"""
    # Check if RoLauncher is already running
    current_pid = os.getpid()
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            # Skip current process
            if proc.info['pid'] == current_pid:
                continue

            # Check if it's another RoLauncher process
            if proc.info['name'] and 'RoLauncher' in proc.info['name']:
                # Another instance is running, just exit
                print("RoLauncher is already running")
                sys.exit(0)

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    initialize_database()

    client = api.Client(get_last_account().get('cookie')
                        if get_last_account() else None)

    dev_mode = os.getenv('DEV', 'false').lower() == 'true'
    url = 'localhost:5173' if dev_mode else 'index.html'

    window = webview.create_window('RoLauncher', url, js_api=Api(client
                                                                 ), min_size=(1000, 600), background_color="#171717")

    def bind_events():
        """Bind events after the window is ready"""
        # Start Roblox monitoring in background thread
        monitor_thread = threading.Thread(
            target=monitor_roblox_process, daemon=True)
        monitor_thread.start()

    webview.start(func=bind_events, private_mode=True,
                  debug=dev_mode, http_server=False)

    # Check for updates on exit
    print("\nChecking for updates...")
    try:
        GITHUB_REPO = "miukyo/rolauncher"  # Replace with your actual repo
        updater = Updater(GITHUB_REPO)
        update_info = updater.check_for_updates()

        if update_info:
            print(f"\nUpdate available!", flush=True)
            print(
                f"Current version: {update_info['current_version']}", flush=True)
            print(
                f"Latest version: {update_info['latest_version']}", flush=True)
            print("\nStarting update process...", flush=True)
            updater.perform_update(update_info['download_url'], flush=True)
        else:
            print("You're running the latest version!", flush=True)
    except Exception as e:
        print(f"Update check failed: {e}", flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='RoLauncher - Launch Roblox games')
    parser.add_argument('--cli', action='store_true',
                        help='Run in CLI mode (no GUI)')
    parser.add_argument('--account-id', type=int,
                        help='Account ID to use for launching')
    parser.add_argument(
        '--mode', choices=['Play', 'Edit'], default='Play', help='Launch mode (Play or Edit)')
    parser.add_argument('--place-id', type=int, help='Place ID to join')
    parser.add_argument('--follow-user', type=int, help='User ID to follow')
    parser.add_argument('--job-id', type=str,
                        help='Job ID for specific server')
    parser.add_argument('--private-id', type=str,
                        help='Private server access code')

    args = parser.parse_args()

    if args.cli:
        run_cli(args)
    else:
        run_gui()
