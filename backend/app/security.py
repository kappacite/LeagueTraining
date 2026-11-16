import time
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
CSP = "default-src 'self'; img-src 'self' https://cdn.discordapp.com; frame-ancestors 'none'"


class RateLimiter:
    # ponytail: in-memory, per process; fine for a single uvicorn worker.
    def __init__(self, limit: int = 20, window_s: float = 60):
        self.limit, self.window_s = limit, window_s
        self.hits: dict[str, deque] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        q = self.hits[key]
        while q and now - q[0] > self.window_s:
            q.popleft()
        if len(q) >= self.limit:
            return False
        q.append(now)
        return True


def install(app: FastAPI, public_origin: str) -> None:
    limiter = RateLimiter()

    @app.middleware("http")
    async def guard(request: Request, call_next):
        if request.method not in SAFE_METHODS and request.headers.get("origin") != public_origin:
            response = JSONResponse({"detail": "bad origin"}, status_code=403)
        elif request.url.path.startswith("/api/auth/") and not limiter.allow(
                request.headers.get("cf-connecting-ip") or (request.client.host if request.client else "?")):
            response = JSONResponse({"detail": "too many requests"}, status_code=429)
        else:
            response = await call_next(request)
        response.headers["Content-Security-Policy"] = CSP
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        return response
