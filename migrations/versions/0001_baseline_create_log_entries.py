"""baseline: create log_entries

#主键约束是关系型数据库里最重要、最基础的一种约束。它本质上是给一张表指定"每一行数据的唯一身份证"。

补这一步是因为：Day 8 用 create_all 建的表，没进迁移历史。
没有它，全新数据库跑 alembic upgrade head 会失败。

Revision ID: 0001
Revises:
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None   #down_revision：父迁移的版本号。None 表示这是根迁移（链表的起点，没有前置迁移）。
branch_labels: Union[str, Sequence[str], None] = None   #branch_labels：分支标签，用于多分支（branching）迁移场景。这里为 None，表示不属于任何命名分支。
depends_on: Union[str, Sequence[str], None] = None     #depends_on：声明本迁移依赖的其它迁移（不构成父子链，只是执行顺序依赖）。这里为 None，无额外依赖。




def upgrade() -> None:
    op.create_table(
        "log_entries",
        sa.Column("id", sa.Integer(), nullable=False),#定义列 id：sa.Column(...)：声明一列。"id"：列名。sa.Integer()：类型为整数。nullable=False：不允许为 NULL（即 NOT NULL）。
        sa.Column("ip", sa.String(length=64), nullable=False),
        sa.Column("ts", sa.DateTime(), nullable=False),
        sa.Column("method", sa.String(length=16), nullable=False),
        sa.Column("path", sa.String(length=256), nullable=False),
        sa.Column("status", sa.Integer(), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("latency", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("log_entries")