from enum import IntEnum

from tortoise import fields
from tortoise.fields.relational import ForeignKeyFieldInstance
from tortoise.models import Model

from app.services.conn.db import add_model
from app.services.servers.models import Server
from app.services.user.models import User

add_model(__name__)


# === 定义工单状态 ===
class TicketStatus(IntEnum):
    """
    枚举类，定义工单的状态
    """

    CANCELED = 0  # 取消
    PENDING = 1  # 待处理
    UNDER_REVIEW = 2  # 审核中
    RESOLVED = 3  # 已处理
    ACCEPTED = 4  # 受理成功
    INVALID = 5  # 无效工单


class TicketType(IntEnum):
    """
    枚举类，定义工单的类型
    """

    BUG = 1  # BUG 反馈
    CONSULT = 2  # 咨询
    FEATURE_REQUEST = 3  # 功能请求
    REPORT = 4  # 举报
    SERVER_ISSUE = 5  # 服务器故障
    SERVER_CONFIG = 6  # 服务器配置申请
    OTHER = 7  # 其他


class TicketPriority(IntEnum):
    """
    枚举类，定义工单的优先级
    """

    LOW = 1  # 低优先级
    MEDIUM = 2  # 中优先级
    HIGH = 3  # 高优先级


# === 工单表（重写 save 方法）===
class Ticket(Model):
    """
    工单模型，用于存储工单的信息，包括状态、优先级、处理人等
    """

    id = fields.IntField(pk=True, generated=True)  # 自增 ID
    title = fields.CharField(max_length=255)  # 工单标题
    description = fields.TextField(null=True)  # 工单详细描述
    status: TicketStatus = fields.IntEnumField(
        enum_type=TicketStatus, default=TicketStatus.PENDING
    )  # 工单状态，默认是待处理
    priority: TicketPriority = fields.IntEnumField(
        enum_type=TicketPriority, default=TicketPriority.MEDIUM
    )  # 工单优先级，默认是中优先级
    creator: ForeignKeyFieldInstance[User] | None = fields.ForeignKeyField(
        "default.User", related_name="created_tickets", on_delete=fields.CASCADE
    )  # 创建者
    assignee: ForeignKeyFieldInstance[User] | None = fields.ForeignKeyField(
        "default.User",
        related_name="assigned_tickets",
        null=True,
        on_delete=fields.SET_NULL,
    )  # 受理人（可为空）
    created_at = fields.DatetimeField(auto_now_add=True)  # 创建时间
    updated_at = fields.DatetimeField(auto_now=True)  # 更新时间

    # 关联服务器（适用于服务器相关工单）
    server: ForeignKeyFieldInstance[Server] | None = fields.ForeignKeyField(
        "default.Server", related_name="tickets", null=True, on_delete=fields.SET_NULL
    )  # 服务器

    # 举报相关字段
    reported_user: ForeignKeyFieldInstance[User] | None = fields.ForeignKeyField(
        "default.User", related_name="reports", null=True, on_delete=fields.SET_NULL
    )  # 被举报用户
    reported_content_id = fields.IntField(null=True, index=True)  # 被举报内容 ID
    report_reason = fields.TextField(null=True)  # 举报理由

    admin_remark = fields.TextField(null=True)  # 处理备注
    created_at = fields.DatetimeField(auto_now_add=True)  # 创建时间
    updated_at = fields.DatetimeField(auto_now=True)  # 更新时间

    class TicketMeta:
        table = "ticket"  # 数据表名


# === 工单日志表 ===
class TicketLog(Model):
    """
    工单日志模型，用于记录工单状态变更的日志
    """

    id = fields.IntField(pk=True, generated=True)  # 自增 ID
    ticket: fields.ForeignKeyRelation[Ticket] = fields.ForeignKeyField(
        "default.Ticket", related_name="logs", on_delete=fields.CASCADE
    )  # 关联工单
    old_status: TicketStatus = fields.IntEnumField(enum_type=TicketStatus)  # 旧状态
    new_status: TicketStatus = fields.IntEnumField(enum_type=TicketStatus)  # 新状态
    changed_by: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "default.User", related_name="ticket_logs", on_delete=fields.CASCADE
    )  # 操作人
    changed_at = fields.DatetimeField(auto_now_add=True)  # 变更时间

    class TicketLogMeta:
        table = "ticket_log"  # 数据表名
