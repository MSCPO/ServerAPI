from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from app.log import logger
from app.user.crud import get_current_user
from app.user.models import User
from app.user.schemas import User as UserSchema

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.get(
    "/me",
    response_model=UserSchema,
    summary="获取当前用户信息",
    description="获取当前登录用户的详细信息，包括用户名、邮箱、姓名和账户状态。",
    responses={
        200: {
            "description": "成功返回当前用户信息",
            "content": {
                "application/json": {
                    "example": {
                        "username": "john_doe",
                        "email": "john.doe@example.com",
                        "full_name": "John Doe",
                        "is_active": True,
                    }
                }
            },
        },
        401: {
            "description": "未授权，缺少或无效的 Bearer token",
            "content": {
                "application/json": {
                    "example": {"detail": "Authorization token missing or invalid"}
                }
            },
        },
        404: {
            "description": "未找到用户，token 验证通过但未能找到对应的用户",
            "content": {
                "application/json": {
                    "example": {"detail": "Could not validate credentials"}
                }
            },
        },
    },
)
async def get_me(request: Request, token: str = Depends(oauth2_scheme)):
    """
    获取当前登录用户的详细信息
    """
    # 从请求头获取 Bearer token
    authorization: str = request.headers.get("Authorization")

    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token missing or invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 提取 token 字符串
    token = authorization[7:]
    logger.info(f"Token: {token}")

    user = get_current_user(token)

    return UserSchema.model_validate(await User.get(username=user["sub"]))
