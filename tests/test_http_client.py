from unittest.mock import Mock

import pytest

from radar.http import HTTPClient, HTTPJSONError, HTTPStatusError


def _response(status_code=200, payload=None, json_error=False):
    response = Mock()
    response.status_code = status_code
    response.url = "https://example.com"
    response.headers = {}
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

