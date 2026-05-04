import types
from typing import cast

from backend.odds_scraping import http_client


class _FakeUserAgentProvider:
    random = 'Agent/1.0'


class _FakeResponse:
    def __init__(self, content: bytes = b'{}'):
        self.content = content

    def raise_for_status(self) -> None:
        pass


class _FakeCurlResponse(_FakeResponse):
    pass


def test_fallback_user_agent_returns_default_browser_string():
    assert 'Mozilla/5.0' in http_client._FallbackUserAgent().random


def test_build_headers_uses_current_user_agent(monkeypatch):
    monkeypatch.setattr(http_client, '_ua_generator', _FakeUserAgentProvider())

    headers = http_client.HttpClient._build_headers()

    assert headers == {
        'User-Agent': 'Agent/1.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
    }


def test_get_merges_headers_and_tracks_domain(monkeypatch):
    client = http_client.HttpClient(min_delay=0)
    seen: dict[str, object] = {}
    waited_on: list[str] = []

    def capture_get_args(
        url: str,
        *,
        params: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
    ):
        seen['url'] = url
        seen['params'] = params
        seen['headers'] = headers
        return _FakeResponse()

    monkeypatch.setattr(client, '_wait_for_domain', lambda domain: waited_on.append(domain))
    monkeypatch.setattr(client._client, 'get', capture_get_args)

    response = client.get(
        'https://site.api.espn.com/apis/v2/sports/basketball/nba',
        params={'limit': 1},
        headers={'X-Test': '1'},
    )

    assert response.content == b'{}'
    assert waited_on == ['espn.com']
    assert seen['url'] == 'https://site.api.espn.com/apis/v2/sports/basketball/nba'
    assert seen['params'] == {'limit': 1}
    headers = cast(dict[str, str], seen['headers'])
    assert headers['X-Test'] == '1'
    assert headers['User-Agent']
    assert 'espn.com' in client._domain_timestamps


def test_get_json_uses_curl_when_impersonation_is_enabled(monkeypatch):
    client = http_client.HttpClient(min_delay=0)
    seen: dict[str, object] = {}

    def capture_curl_get_args(
        url: str,
        *,
        params: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
        impersonate: str | None = None,
        timeout: float | None = None,
    ) -> _FakeCurlResponse:
        seen['url'] = url
        seen['params'] = params
        seen['headers'] = headers
        seen['impersonate'] = impersonate
        seen['timeout'] = timeout
        return _FakeCurlResponse(b'{"games": 2}')

    monkeypatch.setattr(http_client, '_CURL_AVAILABLE', True)
    monkeypatch.setattr(http_client, '_curl_get', capture_curl_get_args)
    monkeypatch.setattr(http_client, '_CURL_TRANSIENT_EXCEPTIONS', (Exception,))

    result = client.get_json(
        'https://sportsbook.draftkings.com/leagues/basketball/nba',
        params={'category': 'games'},
        headers={'X-Test': '1'},
        impersonate='chrome',
    )

    assert result == {'games': 2}
    assert seen['url'] == 'https://sportsbook.draftkings.com/leagues/basketball/nba'
    assert seen['params'] == {'category': 'games'}
    headers = cast(dict[str, str], seen['headers'])
    assert headers['X-Test'] == '1'
    assert seen['impersonate'] == 'chrome'
    assert seen['timeout'] == client._default_timeout
    assert 'draftkings.com' in client._domain_timestamps


def test_get_json_falls_back_to_httpx_get(monkeypatch):
    client = http_client.HttpClient(min_delay=0)
    monkeypatch.setattr(client, 'get', lambda *_args, **_kwargs: _FakeResponse(b'{"ok": true}'))

    assert client.get_json('https://example.com/data') == {'ok': True}


def test_close_closes_underlying_client(monkeypatch):
    client = http_client.HttpClient(min_delay=0)
    closed: list[bool] = []
    monkeypatch.setattr(client._client, 'close', lambda: closed.append(True))

    client.close()

    assert closed == [True]


def test_resolve_domain_uses_urlparse_when_hostinfo_is_missing(monkeypatch):
    client = http_client.HttpClient(min_delay=0)
    monkeypatch.setattr(http_client, 'get_hostinfo', lambda _url: None)

    assert client._resolve_domain('https://example.com/path?q=1') == 'example.com'


def test_wait_for_domain_returns_immediately_for_new_domain(monkeypatch):
    client = http_client.HttpClient(min_delay=5)
    sleeps: list[float] = []
    monkeypatch.setattr(http_client.time, 'sleep', lambda seconds: sleeps.append(seconds))

    client._wait_for_domain('example.com')

    assert sleeps == []


def test_wait_for_domain_sleeps_for_remaining_delay(monkeypatch):
    client = http_client.HttpClient(min_delay=5)
    client._domain_timestamps['example.com'] = 10.0
    sleeps: list[float] = []
    monkeypatch.setattr(http_client.time, 'monotonic', lambda: 12.0)
    monkeypatch.setattr(http_client.time, 'sleep', lambda seconds: sleeps.append(seconds))

    client._wait_for_domain('example.com')

    assert sleeps == [3.0]


def test_log_retry_attempt_logs_warning(caplog):
    exception = RuntimeError('boom')
    retry_state = types.SimpleNamespace(
        attempt_number=2,
        outcome=types.SimpleNamespace(exception=lambda: exception),
        retry_object=types.SimpleNamespace(stop=types.SimpleNamespace(max_attempt_number=3)),
    )

    with caplog.at_level('WARNING'):
        http_client.HttpClient._log_retry_attempt(retry_state)

    assert 'HTTP retry 2/3' in caplog.text
    assert 'RuntimeError' in caplog.text
    assert 'boom' in caplog.text
