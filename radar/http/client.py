from __future__ import annotations

import time
from typing import Any

import requests

from radar.config import settings


class HTTPClientError(Exception):
    pass


class HTTPStatusError(HTTPClientError):
    def __init__(self, status_code: int, url: str) -> None:
        super().__init__(f"HTTP {status_code} for {url}")
        self.status_code = status_code
        self.url = url


class HTTPJSONError(HTTPClientError):
    pass


class HTTPClient:
    retry_statuses = {429, 500, 502, 503, 504}

    def __init__(
        self,
        session: requests.Session | None = None,
        timeout: float | None = None,
        user_agent: str | None = None,
        max_retries: int = 2,
        backoff_seconds: float = 0.5,
    ) -> None:
        self.session = session or requests.Session()
        self.timeout = timeout if timeout is not None else settings.http_timeout_seconds
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.session.headers.update(
            {
                "User-Agent": user_agent or settings.http_user_agent,
                "Accept": "application/json",
            }
        )

    def get_json(self, url: str, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> Any:
        response = self._get(url, params=params, headers=headers)
        return self._response_json(response, url)

    def get_text(self, url: str, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> str:
        response = self.get(url, params=params, headers=headers)
        return response.text

    def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        *,
        allow_redirects: bool = True,
    ) -> requests.Response:
        return self._get(url, params=params, headers=headers, allow_redirects=allow_redirects)

    def post_json(
        self,
        url: str,
        payload: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> Any:
        response = self._post(url, payload=payload, headers=headers)
        return self._response_json(response, url)

    def _response_json(self, response: requests.Response, url: str) -> Any:
        try:
            return response.json()
        except ValueError as exc:
            raise HTTPJSONError(f"Invalid JSON returned by {url}") from exc

    def _post(
        self,
        url: str,
        payload: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> requests.Response:
        return self._request_with_retry("post", url, payload=payload, headers=headers)

    def _get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        *,
        allow_redirects: bool = True,
    ) -> requests.Response:
        return self._request_with_retry(
            "get", url, params=params, headers=headers, allow_redirects=allow_redirects
        )

    def _request_with_retry(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        allow_redirects: bool = True,
    ) -> requests.Response:
        last_response: requests.Response | None = None
        for attempt in range(self.max_retries + 1):
            try:
                request = getattr(self.session, method)
                kwargs: dict[str, Any] = {
                    "headers": headers,
                    "timeout": self.timeout,
                    "allow_redirects": allow_redirects,
                }
                if params is not None:
                    kwargs["params"] = params
                if payload is not None:
                    kwargs["json"] = payload
                response = request(url, **kwargs)
            except requests.RequestException as exc:
                raise HTTPClientError(f"HTTP request failed for {url}") from exc

            if response.status_code < 400:
                return response

            last_response = response
            if response.status_code not in self.retry_statuses or attempt >= self.max_retries:
                raise HTTPStatusError(response.status_code, response.url)

            time.sleep(self._retry_delay(response, attempt))

        raise HTTPStatusError(last_response.status_code, last_response.url)  # pragma: no cover

    def _retry_delay(self, response: requests.Response, attempt: int) -> float:
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return min(float(retry_after), 10.0)
            except ValueError:
                pass
        return self.backoff_seconds * (attempt + 1)
