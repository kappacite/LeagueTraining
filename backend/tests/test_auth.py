from urllib.parse import parse_qs, urlparse

from app.repositories import allowlist
from conftest import ORIGIN, T0, login


def start_login(client):
    r = client.get("/api/auth/login", follow_redirects=False)
    assert r.status_code in (302, 307)
    q = parse_qs(urlparse(r.headers["location"]).query)
    return r, q


def test_login_redirects_to_discord_with_pkce(client):
    r, q = start_login(client)
    assert r.headers["location"].startswith("https://discord.com/oauth2/authorize")
    assert q["client_id"] == ["cid"] and q["scope"] == ["identify"]
    assert q["redirect_uri"] == [f"{ORIGIN}/api/auth/callback"]
    assert q["code_challenge_method"] == ["S256"] and q["code_challenge"][0]
    assert "oauth" in r.cookies or client.cookies.get("oauth")


def test_me_requires_session(client):
    assert client.get("/api/me").status_code == 401


def test_callback_rejects_bad_state(client):
    start_login(client)
    r = client.get("/api/auth/callback?code=c&state=forged", follow_redirects=False)
    assert r.status_code == 400


def test_callback_not_allowed_redirects(client, discord):
    _, q = start_login(client)
    r = client.get(f"/api/auth/callback?code=c&state={q['state'][0]}", follow_redirects=False)
    assert "not-allowed" in r.headers["location"]
    assert client.get("/api/me").status_code == 401


def test_callback_allowed_sets_session(client, conn, discord):
    allowlist.add(conn, "1001", T0)
    _, q = start_login(client)
    r = client.get(f"/api/auth/callback?code=c&state={q['state'][0]}", follow_redirects=False)
    assert r.headers["location"] == "/#/"
    assert discord.token_requests[0]["code_verifier"]
    me = client.get("/api/me").json()
    assert me["name"] == "Faker"
    assert me["avatar_url"] == "https://cdn.discordapp.com/avatars/1001/abc.png"


def test_session_token_stored_hashed(client, conn):
    login(client, conn)
    token = client.cookies.get("session")
    stored = [r["token_hash"] for r in conn.execute("select token_hash from sessions")]
    assert stored and token not in stored


def test_logout(client, conn):
    login(client, conn)
    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/me").status_code == 401


def test_post_without_origin_forbidden(client, conn):
    login(client, conn)
    del client.headers["origin"]
    assert client.post("/api/auth/logout").status_code == 403
    assert client.post("/api/auth/logout", headers={"Origin": "https://evil.test"}).status_code == 403


def test_security_headers_present(client):
    h = client.get("/api/me").headers
    assert "default-src 'self'" in h["content-security-policy"]
    assert "frame-ancestors 'none'" in h["content-security-policy"]
    assert h["x-content-type-options"] == "nosniff"
    assert h["referrer-policy"] == "same-origin"


def test_auth_rate_limited(client):
    codes = [client.get("/api/auth/login", follow_redirects=False).status_code for _ in range(21)]
    assert codes[:20].count(429) == 0 and codes[20] == 429
    assert client.get("/api/me").status_code == 401  # non-auth routes unaffected
