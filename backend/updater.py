import requests
import zipfile
import tempfile
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple


class Updater:
    def __init__(self, github_repo: str, current_version_file: str = "VERSION"):
        """
        Initialize the updater.

        Args:
            github_repo: GitHub repository in format "owner/repo"
            current_version_file: Path to the VERSION file (default: "VERSION")
        """
        self.github_repo = github_repo
        self.current_version_file = current_version_file
        self.app_dir = Path(__file__).parent.parent.absolute()
        self.version_file_path = self.app_dir / current_version_file

    def get_current_version(self) -> str:
        """Read the current version of app."""
        return "0.0.3"

    def get_latest_version_from_github(self) -> Optional[Tuple[str, str]]:
        """
        Fetch the latest version from GitHub repository's VERSION file.

        Returns:
            Tuple of (version, download_url) or None if failed
        """
        try:
            # Get the VERSION file from the main branch
            version_url = f"https://raw.githubusercontent.com/{self.github_repo}/main/VERSION"
            print(f"Checking for updates at: {version_url}")

            response = requests.get(version_url, timeout=10)
            response.raise_for_status()

            latest_version = response.text.strip()
            print(f"Latest version on GitHub: {latest_version}")

            # Get the latest release download URL
            release_url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
            release_response = requests.get(release_url, timeout=10)
            release_response.raise_for_status()

            release_data = release_response.json()

            # Find the release asset (ZIP file)
            download_url = None
            for asset in release_data.get('assets', []):
                if asset['name'].endswith('.zip'):
                    download_url = asset['browser_download_url']
                    break

            if not download_url:
                print("No ZIP file found in latest release")
                return None

            print(f"Download URL: {download_url}")
            return (latest_version, download_url)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching version from GitHub: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

    def compare_versions(self, current: str, latest: str) -> bool:
        """
        Compare two version strings.

        Returns:
            True if latest > current, False otherwise
        """
        try:
            current_parts = [int(x) for x in current.split('.')]
            latest_parts = [int(x) for x in latest.split('.')]

            # Pad with zeros if lengths differ
            max_len = max(len(current_parts), len(latest_parts))
            current_parts.extend([0] * (max_len - len(current_parts)))
            latest_parts.extend([0] * (max_len - len(latest_parts)))

            return latest_parts > current_parts
        except Exception as e:
            print(f"Error comparing versions: {e}")
            return False

    def download_update(self, download_url: str, temp_dir: Path) -> Optional[Path]:
        """
        Download the update ZIP file.

        Args:
            download_url: URL to download from
            temp_dir: Temporary directory to save to

        Returns:
            Path to downloaded file or None if failed
        """
        try:
            print(f"Downloading update from: {download_url}")

            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()

            zip_path = temp_dir / "update.zip"
            total_size = int(response.headers.get('content-length', 0))

            with open(zip_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"Download progress: {progress:.1f}%")

            print(f"Download completed: {zip_path}")
            return zip_path

        except Exception as e:
            print(f"Error downloading update: {e}")
            return None

    def extract_update(self, zip_path: Path, extract_dir: Path) -> bool:
        """
        Extract the downloaded ZIP file.

        Args:
            zip_path: Path to ZIP file
            extract_dir: Directory to extract to

        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"Extracting update to: {extract_dir}")

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

            print("Extraction completed")
            return True

        except Exception as e:
            print(f"Error extracting update: {e}")
            return False

    def create_update_script(self, temp_extract_dir: Path) -> Path:
        """
        Create a batch script to replace files.

        Args:
            temp_extract_dir: Directory containing extracted update files

        Returns:
            Path to the created batch script
        """
        script_path = self.app_dir / "update.bat"

        batch_content = f"""@echo off
            timeout /t 2 /nobreak > nul

            xcopy /E /I /Y /Q "{temp_extract_dir}\\*" "{self.app_dir}\\" > nul 2>&1

            rmdir /S /Q "{temp_extract_dir}" > nul 2>&1

            del "%~f0"
            """

        try:
            with open(script_path, 'w') as f:
                f.write(batch_content)

            print(f"Update script created: {script_path}")
            return script_path

        except Exception as e:
            print(f"Error creating update script: {e}")
            return None

    def check_for_updates(self) -> Optional[dict]:
        """
        Check if updates are available.

        Returns:
            Dictionary with update info or None if no update available
        """
        current_version = self.get_current_version()
        github_data = self.get_latest_version_from_github()

        if not github_data:
            print("Could not fetch update information")
            return None

        latest_version, download_url = github_data

        if self.compare_versions(current_version, latest_version):
            print(f"Update available: {current_version} -> {latest_version}")
            return {
                'current_version': current_version,
                'latest_version': latest_version,
                'download_url': download_url
            }
        else:
            print("Application is up to date")
            return None

    def perform_update(self, download_url: str) -> bool:
        """
        Perform the complete update process.

        Args:
            download_url: URL to download the update from

        Returns:
            True if update process initiated successfully
        """
        try:
            # Create temporary directory
            temp_dir = Path(tempfile.mkdtemp(prefix="rolauncher_update_"))
            print(f"Created temp directory: {temp_dir}")

            # Download update
            zip_path = self.download_update(download_url, temp_dir)
            if not zip_path:
                shutil.rmtree(temp_dir, ignore_errors=True)
                return False

            # Extract update
            extract_dir = temp_dir / "extracted"
            extract_dir.mkdir(exist_ok=True)

            if not self.extract_update(zip_path, extract_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
                return False

            # Create update script
            script_path = self.create_update_script(extract_dir)
            if not script_path:
                shutil.rmtree(temp_dir, ignore_errors=True)
                return False

            # Schedule the update script to run after the application exits
            print("Update script will run after application exits.")

            def launch_update_script():
                subprocess.Popen(['cmd.exe', '/c', str(script_path)],
                                 creationflags=subprocess.CREATE_NO_WINDOW)

            # Register the script to run on exit
            import atexit
            atexit.register(launch_update_script)

            return True

        except Exception as e:
            print(f"Error performing update: {e}")
            return False
