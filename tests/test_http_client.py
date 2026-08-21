from unittest.mock import Mock, patch

import pytest
import requests

from radar.http import HTTPClient, HTTPClientError, HTTPJSONError, HTTPStatusError


def _response(status_code=200, payload=None, json_error=False):
    response = Mock()
    response.status_code = status_code
    response.url = "https://example.com"
    response.headers = {}
    response.text = "response text"
    if json_error:
        response.json.side_effect = ValueError("bad json")
    else:
        response.json.return_value = payload if payload is not None else {}
    return response


def test_http_client_sets_user_agent_and_returns_json():
    session = Mock()
    session.headers = {}
    session.get.return_value = _response(payload={"ok": True})

    client = HTTPClient(session=session, timeout=1, user_agent="RadarTest", max_retries=0)

    assert client.get_json("https://example.com") == {"ok": True}
    assert session.headers["User-Agent"] == "RadarTest"
    session.get.assert_called_once()


def test_http_client_returns_text():
    session = Mock()
    session.headers = {}
    session.get.return_value = _response()
    client = HTTPClient(session=session, max_retries=0)

    assert client.get_text("https://example.com") == "response text"


def test_http_client_can_disable_redirects():
    session = Mock()
    session.headers = {}
    session.get.return_value = _response()
    client = HTTPClient(session=session, max_retries=0)

    client.get("https://example.com", allow_redirects=False)
    assert session.get.call_args.kwargs["allow_redirects"] is False


def test_http_client_raises_on_status_error():
    session = Mock()
    session.headers = {}
    session.get.return_value = _response(status_code=404)
    client = HTTPClient(session=session, max_retries=0)

    with pytest.raises(HTTPStatusError):
        client.get_json("https://example.com")


def test_http_client_raises_on_invalid_json():
    session = Mock()
    session.headers = {}
    session.get.return_value = _response(json_error=True)
    client = HTTPClient(session=session, max_retries=0)

    with pytest.raises(HTTPJSONError):
        client.get_json("https://example.com")


def test_http_client_retries_429_and_respects_retry_after():
    session = Mock()
    session.headers = {}
    limited = _response(status_code=429)
    limited.headers = {"Retry-After": "2"}
    session.get.side_effect = [limited, _response(payload={"ok": True})]
    client = HTTPClient(session=session, max_retries=1)

    with patch("radar.http.client.time.sleep") as sleep:
        assert client.get_json("https://example.com") == {"ok": True}

    sleep.assert_called_once_with(2.0)
    assert session.get.call_count == 2


def test_http_client_posts_json_and_retries_429_once():
    session = Mock()
    session.headers = {}
    limited = _response(status_code=429)
    limited.headers = {"Retry-After": "1"}
    session.post.side_effect = [limited, _response(payload={"results": []})]
    client = HTTPClient(session=session, max_retries=1)

    with patch("radar.http.client.time.sleep") as sleep:
        result = client.post_json(
            "https://api.example/search",
            payload={"query": "Goiânia"},
            headers={"Authorization": "Bearer hidden"},
        )

    assert result == {"results": []}
    sleep.assert_called_once_with(1.0)
    assert session.post.call_count == 2


def test_http_client_wraps_timeout():
    session = Mock()
    session.headers = {}
    session.get.side_effect = requests.Timeout()
    client = HTTPClient(session=session, max_retries=0)

    with pytest.raises(HTTPClientError, match="HTTP request failed"):
        client.get_json("https://example.com")
