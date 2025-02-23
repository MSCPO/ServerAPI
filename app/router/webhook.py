import asyncio
import hashlib
import hmac
import os

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.config import settings
from app.log import logger

router = APIRouter()


async def run_git_pull_and_restart():
    # 异步执行 git pull
    if settings.MIRROR_URL:
        await (
            await asyncio.create_subprocess_exec(
                "git",
                "config",
                "--all",
                "--global",
                rf'url."{settings.MIRROR_URL}https://github.com/".insteadOf "https://github.com/"',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        ).communicate()
    process = await asyncio.create_subprocess_exec(
        "git",
        "fetch",
        "--all",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()

    if process.returncode == 0:
        logger.info(f"Git pull output: {stdout.decode()}")
        process = await asyncio.create_subprocess_exec(
            "git",
            "reset",
            "--hard",
            "origin/main",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            logger.info(f"Git 重置成功: {stdout.decode()}")
            os._exit(0)
        else:
            logger.error(f"Git 重置失败: {stderr.decode()}")
    else:
        logger.error(f"Git pull error: {stderr.decode()}")


class WebhookResponse(BaseModel):
    message: str
    status: str


@router.post(
    "/webhook",
    summary="GitHub Webhook",
    response_model=WebhookResponse,
    tags=["webhook"],
    responses={200: {"description": "Success"}},
    include_in_schema=False,
)
async def handle_webhook(request: Request):
    """
    接收并处理 GitHub Webhook 请求，执行 Git 拉取操作。

    请求体的字段如下：
    - `event`: 事件类型（如 `push` 或 `pull_request`）。
    - `repository`: 触发事件的 Git 仓库名称。
    - `commit_sha`: 最近提交的 SHA。

    响应字段：
    - `message`: 操作的结果信息。
    - `status`: 操作状态（如成功或失败）。
    """
    payload_bytes = await request.body()
    payload = await request.json()

    signature_sha1 = request.headers.get("X-Hub-Signature")
    signature_sha256 = request.headers.get("X-Hub-Signature-256")

    if not signature_sha1 or not signature_sha256:
        raise HTTPException(status_code=400, detail="Missing signatures")

    computed_sha256 = (
        "sha256="
        + hmac.new(
            settings.SECRET.encode("utf-8"), payload_bytes, hashlib.sha256
        ).hexdigest()
    )

    computed_sha1 = (
        "sha1="
        + hmac.new(
            settings.SECRET.encode("utf-8"), payload_bytes, hashlib.sha1
        ).hexdigest()
    )

    if not hmac.compare_digest(computed_sha256, signature_sha256):
        raise HTTPException(status_code=400, detail="Invalid SHA256 signature")

    if not hmac.compare_digest(computed_sha1, signature_sha1):
        raise HTTPException(status_code=400, detail="Invalid SHA1 signature")

    logger.info(
        f"ref: {payload.get('ref')} event: {request.headers.get('X-GitHub-Event').lower()}"
    )

    if (
        payload.get("ref") == "refs/heads/main"
        and request.headers.get("X-GitHub-Event").lower() == "push"
    ):
        await run_git_pull_and_restart()

    return {"status": "success"}
