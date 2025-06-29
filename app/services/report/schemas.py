from pydantic import BaseModel, Field

from app.models import TicketPriority, TicketStatus, TicketType


class TicketCreateReport(BaseModel):
    title: str = Field(..., title="工单标题", description="工单的简短描述")
    status: TicketStatus = Field(
        default=TicketStatus.PENDING,
        title="工单状态",
        description="工单的当前状态，默认待处理",
    )
    type: TicketType = Field(
        default=TicketType.REPORT,
        title="工单类型",
        description="工单的类型，默认举报类型",
    )
    description: str | None = Field(
        None, title="工单描述", description="工单的详细描述，可以为空"
    )
    creator_id: int = Field(
        default=0, title="创建者 ID", description="提交举报工单的用户 ID"
    )
    reported_user_id: int = Field(
        ..., title="被举报用户 ID", description="举报的目标用户 ID"
    )
    reported_content_id: int | None = Field(
        None, title="被举报内容 ID", description="举报的内容 ID，可选"
    )
    report_reason: str = Field(..., title="举报理由", description="举报的具体原因")
    priority: TicketPriority | None = Field(
        TicketPriority.MEDIUM,
        title="优先级",
        description="工单的优先级，1=低，2=中，3=高。默认中等优先级",
    )
