from typing import ClassVar

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.services.user.crud import get_current_user


class AuthMiddleware(BaseHTTPMiddleware):
    # 允许匿名访问的路径白名单（支持部分通配）
    ANONYMOUS_PATHS: ClassVar[list[str]] = [
        "/servers/",
    ]

    def is_anonymous_path(self, path: str, method: str) -> bool:
        # 只允许GET方法匿名
        if method != "GET":
            return False
        return any(path.startswith(prefix) for prefix in self.ANONYMOUS_PATHS)

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method
        if self.is_anonymous_path(path, method):
            request.state.user = None
            return await call_next(request)
        # 只对带有 Authorization 的请求做处理
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
            try:
                user = await get_current_user(token)
                request.state.user = user
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token",
                )
        else:
            request.state.user = None
        return await call_next(request)
