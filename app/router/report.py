from fastapi import APIRouter

from app.services.report.crud import TicketCreateReport, TicketCRUD
from app.services.report.models import TicketStatus, TicketType

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
async def create_report(ticket: TicketCreateReport):
    """
    创建举报工单接口

    **请求体字段说明：**
    - `title`: 工单标题，字符串类型，最大长度 255 字符
    - `description`: 工单描述，可选，最长 1000 字符
    - `creator_id`: 提交工单的用户 ID
    - `reported_user_id`: 被举报用户的 ID
    - `reported_content_id`: 被举报内容的 ID（如果有的话）
    - `report_reason`: 举报理由，字符串类型，不能为空
    - `priority`: 工单的优先级，取值为 1、2、3，分别表示低、中、高，默认为中等优先级

    **返回说明：**
    - 返回创建的举报工单数据，包括 `id`, `status`, `creator_id`, `created_at` 等字段。

    - **成功响应代码**: `201 Created`
    - **失败响应代码**: `400 Bad Request`（如果请求体字段不完整）

    :param ticket: 创建举报工单所需的字段
    :return: 返回创建的举报工单数据
    """
    ticket_data = ticket.model_dump()
    ticket_data["creator_id"] = (
        ticket.creator_id
    )  # 创建工单时，creator_id 为提交者的 ID
    ticket_data["status"] = TicketStatus.PENDING  # 默认设置为待处理
    ticket_data["type"] = TicketType.REPORT  # 设置为举报工单类型

    return await TicketCRUD.create_report_ticket(ticket_data, ticket.creator_id)
