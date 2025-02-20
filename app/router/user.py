from fastapi import APIRouter, Depends

from app.user.crud import get_current_user
from app.user.models import User
from app.user.schemas import User as UserSchema

router = APIRouter()


@router.get("/me", response_model=UserSchema, summary="获取当前用户信息")
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserSchema.model_validate(await User.get(username=current_user.get("sub")))
