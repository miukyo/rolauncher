from mapping.database import initialize_database, get_last_account, get_account
from mapping.games import Games
from mapping.friends import Friends
from mapping.user import User
from mapping.auth import Auth
from mapping.utility import Utility
from updater import Updater
from mapping.realtime import Realtime
import os
import sys
import argparse
import webview
import api
import ctypes
import psutil
import threading
import time
import subprocess


class Api:
    def __init__(self):
        client = api.Client(get_last_account().get('cookie')
                            if get_last_account() else None)
        initialize_database()
        self.client = client
        self.auth = Auth(client)
        self.user = User(client)
        self.games = Games(client)
        self.friends = Friends(client)
        self.utility = Utility(client, lambda: self.auth)
        Realtime(client, lambda: self.user)


class Cli_Api:
    def __init__(self, client):
        initialize_database()
        self.client = client
        self.auth = Auth(client)
        self.utility = Utility(client, lambda: self.auth)


def run_cli(args):
    """Run CLI mode to launch Roblox directly"""
    try:
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


def is_roblox_running():
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == 'RobloxPlayerBeta.exe':
            return True
    return False


def check_for_updates():
    """Check for updates in a background thread."""
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
            updater.perform_update(update_info['download_url'])
        else:
            print("You're running the latest version!", flush=True)
    except Exception as e:
        print(f"Update check failed: {e}", flush=True)


def _start_webview():
    """Start the webview window (Child Process)"""
    dev_mode = os.getenv('DEV', 'false').lower() == 'true'
    url = 'localhost:5173' if dev_mode else 'index.html'

    window = webview.create_window('RoLauncher', url, js_api=Api(
    ), min_size=(1000, 600), background_color="#171717")

    def bind_events():
        """Bind events after the window is ready."""
        # Start update check in background thread
        update_thread = threading.Thread(target=check_for_updates, daemon=True)
        update_thread.start()

    webview.start(func=bind_events,
                  debug=dev_mode, http_server=False)


def run_gui():
    """Run GUI mode supervisor."""
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
                warning_msg = "RoLauncher is already running"
                ctypes.windll.user32.MessageBoxW(
                    0, warning_msg, "RoLauncher Warning", 0x30)
                sys.exit(0)

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    while True:
        if getattr(sys, 'frozen', False):
             cmd = [sys.executable, '--internal-gui']
        else:
             cmd = [sys.executable, sys.argv[0], '--internal-gui']

        subprocess.run(cmd)

        if is_roblox_running():
            while is_roblox_running():
                time.sleep(1)
        else:
            break


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='RoLauncher - Launch Roblox games')
    parser.add_argument('--cli', action='store_true',
                        help='Run in CLI mode (no GUI)')
    parser.add_argument('--internal-gui', action='store_true', help=argparse.SUPPRESS)
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
    elif args.internal_gui:
        _start_webview()
    else:
        run_gui()
