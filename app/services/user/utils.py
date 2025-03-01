from app.services.user.models import User


async def get_user_avatar_url(user_data: User) -> str | None:
    """
    获取用户头像 URL
    """
    if user_data.avatar_hash is None:
        return None
    file_instance = await user_data.avatar_hash
    return file_instance.file_path
