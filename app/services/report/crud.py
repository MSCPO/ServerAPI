from .models import Ticket, TicketLog, TicketPriority, TicketStatus, TicketType
from pydantic import BaseModel, Field
from tortoise.exceptions import DoesNotExist


class TicketCRUD:
    """
    用于工单（Ticket）相关的 CRUD 操作
    """

    @staticmethod
    async def create_ticket(ticket_data: dict, changed_by_id: int) -> Ticket:
        """
        创建一个新的工单，并记录状态变更日志

        :param ticket_data: 创建工单所需的字段数据
        :param changed_by_id: 操作人 ID，用于记录在日志中
        :return: 创建的工单实例
        """
        # 创建工单
        ticket: Ticket = await Ticket.create(**ticket_data)

        # 如果是状态变更，记录 TicketLog
        if ticket.status != TicketStatus.PENDING:  # 如果状态不是默认的待处理状态
            await TicketLog.create(
                ticket=ticket,
                old_status=TicketStatus.PENDING,
                new_status=ticket.status,
                changed_by_id=changed_by_id,
            )
        return ticket

    @staticmethod
    async def create_report_ticket(ticket_data: dict, changed_by_id: int) -> Ticket:
        """
        创建一个举报类型的工单，并记录状态变更日志

        :param ticket_data: 创建举报工单所需的字段数据
        :param changed_by_id: 操作人 ID，用于记录在日志中
        :return: 创建的举报工单实例
        """
        # 强制设置工单类型为举报（REPORT）
        ticket_data["type"] = TicketType.REPORT
        ticket_data["status"] = TicketStatus.PENDING  # 默认状态是待处理

        # 创建举报工单
        ticket: Ticket = await Ticket.create(**ticket_data)

        # 如果举报工单的状态不是默认的待处理状态，则记录日志
        if ticket.status != TicketStatus.PENDING:
            await TicketLog.create(
                ticket=ticket,
                old_status=TicketStatus.PENDING,
                new_status=ticket.status,
                changed_by_id=changed_by_id,
            )

        return ticket

    @staticmethod
    async def get_ticket(ticket_id: int) -> Ticket | None:
        """
        获取指定 ID 的工单

        :param ticket_id: 工单 ID
        :return: 工单实例，如果不存在则返回 None
        """
        try:
            return await Ticket.get(id=ticket_id)
        except DoesNotExist:
            return None

    @staticmethod
    async def get_all_tickets(status: TicketStatus | None = None) -> list[Ticket]:
        """
        获取所有工单，可以选择按照状态过滤

        :param status: 工单状态
        :return: 工单列表
        """
        if status:
            return await Ticket.filter(status=status).all()
        return await Ticket.all()

    @staticmethod
    async def update_ticket(
        ticket_id: int, ticket_data: dict, changed_by_id: int
    ) -> Ticket | None:
        """
        更新工单信息，并记录状态变更日志

        :param ticket_id: 工单 ID
        :param ticket_data: 更新的数据
        :param changed_by_id: 操作人 ID，用于记录在日志中
        :return: 更新后的工单实例
        """
        try:
            ticket = await Ticket.get(id=ticket_id)
            old_status = ticket.status
            # 更新字段
            for key, value in ticket_data.items():
                setattr(ticket, key, value)
            await ticket.save()

            # 如果状态发生了变化，记录状态变更日志
            if ticket.status != old_status:
                await TicketLog.create(
                    ticket=ticket,
                    old_status=old_status,
                    new_status=ticket.status,
                    changed_by_id=changed_by_id,
                )

            return ticket
        except DoesNotExist:
            return None

    @staticmethod
    async def delete_ticket(ticket_id: int) -> bool:
        """
        删除工单

        :param ticket_id: 工单 ID
        :return: 删除成功返回 True，失败返回 False
        """
        try:
            ticket = await Ticket.get(id=ticket_id)
            await ticket.delete()
            return True
        except DoesNotExist:
            return False


# 用 Pydantic 模型来验证请求体数据
class TicketCreateReport(BaseModel):
    title: str = Field(..., title="工单标题", description="工单的简短描述")
    description: str | None = Field(
        None, title="工单描述", description="工单的详细描述，可以为空"
    )
    creator_id: int = Field(..., title="创建者 ID", description="提交举报工单的用户 ID")
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
