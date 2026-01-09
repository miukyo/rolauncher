"""

This module contains classes used internally by ro.py for sending requests to Roblox endpoints.

"""

from __future__ import annotations

import gc
from typing import Dict
import time
import tempfile
import hashlib
import pickle
from pathlib import Path
import threading

from httpx import AsyncClient, Response, Limits, Timeout, ConnectTimeout, ReadTimeout, ConnectError
import trio

_xcsrf_allowed_methods: Dict[str, bool] = {
    "post": True,
    "put": True,
    "patch": True,
    "delete": True
}


class CleanAsyncClient(AsyncClient):
    """
    This is a clean-on-delete version of httpx.AsyncClient.
    """

    def __init__(self):
        limits = Limits(max_connections=100, max_keepalive_connections=20)
        timeout = Timeout(connect=10.0, read=30.0, write=30.0, pool=5.0)
        super().__init__(limits=limits, timeout=timeout)

    def __del__(self):
        pass


class Requests:

    """
    A special request object that implements special functionality required to connect to some Roblox endpoints.

    Attributes:
        session: Base session object to use when sending requests.
        xcsrf_token_name: The header that will contain the Cross-Site Request Forgery token.
    """

    def __init__(
            self,
            session: CleanAsyncClient = None,
            xcsrf_token_name: str = "X-CSRF-Token"
    ):
        """
        Arguments:
            session: A custom session object to use for sending requests, compatible with httpx.AsyncClient.
            xcsrf_token_name: The header to place X-CSRF-Token data into.
        """
        self.session: CleanAsyncClient
        self._custom_session = session is not None
        self._current_trio_token = None

        if session is None:
            self.session = CleanAsyncClient()
        else:
            self.session = session

        self.xcsrf_token_name: str = xcsrf_token_name
        self._disk_cache_dir = Path(tempfile.gettempdir()) / "rolauncher_cache"
        self._disk_cache_dir.mkdir(exist_ok=True)

        self.session.headers["User-Agent"] = "Roblox/WinInet"
        self.session.headers["Referer"] = "www.roblox.com"

    def _ensure_session_for_context(self):
        """Ensure the session is valid for the current trio context."""
        if self._custom_session:
            return

        try:
            import trio
            current_token = trio.lowlevel.current_trio_token()
            if self._current_trio_token != current_token:
                old_headers = dict(self.session.headers)
                old_cookies = self.session.cookies
                self.session = CleanAsyncClient()
                for key, value in old_headers.items():
                    self.session.headers[key] = value

                self.session.cookies = old_cookies
                self._current_trio_token = current_token
        except RuntimeError:
            pass

    def _get_cache_key(self, method, *args, **kwargs):
        def make_hashable(value):
            if isinstance(value, dict):
                return tuple(sorted((k, make_hashable(v)) for k, v in value.items() if k != "sessionId"))
            if isinstance(value, (list, tuple, set, frozenset)):
                return tuple(sorted(make_hashable(v) for v in value))
            if isinstance(value, str):
                return tuple(sorted(value.split(","))) if "," in value else value.strip()
            if isinstance(value, bool):
                return str(value).lower()
            if value is None:
                return "null"
            return value if isinstance(value, (int, float)) else str(value)

        url = kwargs.get("url", args[0] if args else None)
        if not url:
            raise ValueError("URL must be provided for cache key generation")

        from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
        parsed_url = urlparse(url)
        normalized_url = urlunparse(parsed_url._replace(
            query=urlencode(
                sorted(parse_qsl(parsed_url.query, keep_blank_values=True)))
        ))

        sorted_kwargs = tuple((k, make_hashable(v))
                              for k, v in sorted(kwargs.items()))

        # Include auth cookie in cache key to separate cache per user
        roblosecurity_cookies = [cookie.value for cookie in self.session.cookies.jar if cookie.name == ".ROBLOSECURITY"]
        auth_cookie = roblosecurity_cookies[-1][-12:] if roblosecurity_cookies else ""
        return hashlib.sha256(str((method.lower(), normalized_url, sorted_kwargs, auth_cookie)).encode()).hexdigest()

    def _get_disk_cache_path(self, cache_key) -> Path:
        """Generate a file path for disk cache based on cache key."""
        key_str = str(cache_key)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        return self._disk_cache_dir / f"{key_hash}.cache"

    def _get_from_disk_cache(self, cache_key):
        """Retrieve response from disk cache (permanent, no expiry)."""
        cache_file = self._get_disk_cache_path(cache_key)
        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "rb") as f:
                cached_data = pickle.load(f)
            return cached_data.get("response")
        except (pickle.PickleError, OSError, KeyError, EOFError):
            pass

        return None

    def _is_error_response(self, response) -> bool:
        """Check if response contains error structure."""
        try:
            data = response.json()
            return isinstance(data, dict) and "errors" in data and isinstance(data["errors"], list)
        except:
            return False

    def _set_disk_cache(self, cache_key, response):
        """Save response to disk cache."""
        if self._is_error_response(response):
            return  # Don't cache error responses

        cache_file = self._get_disk_cache_path(cache_key)
        try:
            cached_data = {"response": response}
            with open(cache_file, "wb") as f:
                pickle.dump(cached_data, f)
        except (pickle.PickleError, OSError):
            pass

    async def _make_request(self, method: str, *args, **kwargs) -> Response:
        """Internal method to make HTTP request with retries."""
        for attempt in range(3):
            try:
                return await self.session.request(method, *args, **kwargs)
            except ValueError as e:
                if "list.remove(x): x not in list" in str(e) and attempt < 2:
                    await trio.sleep(0.1 * (attempt + 1))
                    continue
                raise
            except (ConnectTimeout, ReadTimeout, ConnectError):
                if attempt < 2:
                    await trio.sleep(0.5 * (attempt + 1))
                    continue
                raise

    async def request(self, method: str, *args, **kwargs) -> Response:
        """
        Arguments:
            method: The request method.

        Returns:
            An HTTP response.
        """

        # Ensure session is valid for current trio context
        self._ensure_session_for_context()

        handle_xcsrf_token = kwargs.pop("handle_xcsrf_token", True)
        disk_cache = kwargs.pop("disk_cache", None)

        if disk_cache is not None:
            cache_key = self._get_cache_key(method, *args, **kwargs)
            cached_response = self._get_from_disk_cache(cache_key)
            # print(
            #     f"Disk cache {'hit' if cached_response is not None else 'miss'} for {method} {cache_key}", flush=True)
            if cached_response is not None:
                def refresh_cache_thread():
                    import asyncio
                    try:
                        # print(
                        #     f"Refreshing cache for {method} {cache_key}", flush=True)
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        fresh_response = loop.run_until_complete(
                            self._make_request(method, *args, **kwargs))
                        if not self._is_error_response(fresh_response):
                            self._set_disk_cache(cache_key, fresh_response)
                        loop.close()
                    except:
                        pass

                threading.Thread(target=refresh_cache_thread,
                                 daemon=True).start()
                return cached_response

        response = await self._make_request(method, *args, **kwargs)

        if handle_xcsrf_token and self.xcsrf_token_name in response.headers and _xcsrf_allowed_methods.get(method.lower()):
            self.session.headers[self.xcsrf_token_name] = response.headers[self.xcsrf_token_name]
            if response.status_code == 403:
                response = await self.session.request(method, *args, **kwargs)

        gc.collect()  # Aggresive garbage collection every request ehe :P

        if kwargs.get("stream"):
            # Streamed responses should not be cached, so we immediately return the response.
            return response

        if disk_cache:
            cache_key = self._get_cache_key(method, *args, **kwargs)
            self._set_disk_cache(cache_key, response)

        return response

    async def get(self, *args, **kwargs) -> Response:
        """
        Sends a GET request.

        Returns:
            An HTTP response.
        """

        return await self.request("GET", *args, **kwargs)

    async def cache_get(self, *args, **kwargs) -> Response:
        """
        Sends a GET request with disk caching and background refresh.
        Requires running within a trio nursery context.

        Returns:
            An HTTP response.
        """
        try:
            return await self.request("GET", *args, **kwargs, disk_cache=True)
        except (AttributeError, RuntimeError):
            # Fallback without background refresh if no nursery available
            return await self.request("GET", *args, **kwargs, disk_cache=True)

    async def post(self, *args, **kwargs) -> Response:
        """
        Sends a POST request.

        Returns:
            An HTTP response.
        """

        return await self.request("POST", *args, **kwargs)

    async def cache_post(self, *args, **kwargs) -> Response:
        """
        Sends a POST request with disk caching and background refresh.
        Requires running within a trio nursery context.

        Returns:
            An HTTP response.
        """
        try:
            return await self.request("POST", *args, **kwargs, disk_cache=True)
        except (AttributeError, RuntimeError):
            # Fallback without background refresh if no nursery available
            return await self.request("POST", *args, **kwargs, disk_cache=True)

    async def put(self, *args, **kwargs) -> Response:
        """
        Sends a PUT request.

        Returns:
            An HTTP response.
        """

        return await self.request("PUT", *args, **kwargs)

    async def patch(self, *args, **kwargs) -> Response:
        """
        Sends a PATCH request.

        Returns:
            An HTTP response.
        """

        return await self.request("PATCH", *args, **kwargs)

    async def delete(self, *args, **kwargs) -> Response:
        """
        Sends a DELETE request.

        Returns:
            An HTTP response.
        """

        return await self.request("DELETE", *args, **kwargs)
