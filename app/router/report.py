from fastapi import APIRouter, Depends

from app.services.auth.schemas import JWTData
from app.services.report.crud import TicketCRUD
from app.services.report.schemas import TicketCreateReport
from app.services.user.crud import get_current_user

router = APIRouter()


@router.post(
    "/report/create",
    response_model=TicketCreateReport,
    summary="创建举报工单",
    description="该接口用于创建举报类型的工单，用户可以提交对其他用户或内容的举报。",
    responses={
        201: {
            "description": "成功创建举报工单",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "title": "举报恶意用户",
                        "description": "该用户发布不良内容。",
                        "creator_id": 1001,
                        "reported_user_id": 2002,
                        "report_reason": "发布恶意广告",
                        "priority": 2,
                        "status": 1,  # PENDING
                        "created_at": "2025-03-09T00:00:00",
                        "updated_at": "2025-03-09T00:00:00",
                    }
                }
            },
        },
        400: {
            "description": "无效的请求参数",
            "content": {
                "application/json": {"example": {"detail": "报告理由不能为空"}}
            },
        },
    },
)
async def create_report(
    ticket: TicketCreateReport, current_user: JWTData = Depends(get_current_user)
):
    ticket.creator_id = current_user.id
    return await TicketCRUD.create_report_ticket(ticket, ticket.creator_id)
