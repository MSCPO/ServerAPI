from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.services.user.crud import get_current_user


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
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
        response = await call_next(request)
        return response
