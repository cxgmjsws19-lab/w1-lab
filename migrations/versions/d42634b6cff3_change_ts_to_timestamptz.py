"""change ts to timestamptz

Revision ID: d42634b6cff3
Revises: 8632e1838170
Create Date: 2026-11-20 02:55:14.316303

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd42634b6cff3'
down_revision: Union[str, Sequence[str], None] = '8632e1838170'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    旧的 ts 是 timestamp without time zone，同一列里混了两种语义：
      - id=2 那条是裸时间输入的，人工确认它表示北京时间
      - 其余行是 aware 输入，psycopg 已转成 UTC 存的
    所以必须按行指定解释方式，不能用 PG 的默认（默认按会话时区，会静默出错）。
    """
    op.alter_column(
        'log_entries',
        'ts',
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False,
        postgresql_using=(
            "ts AT TIME ZONE CASE WHEN id = 2 THEN 'Asia/Shanghai' ELSE 'UTC' END"
        ),
    )


def downgrade() -> None:
    """Downgrade schema.

    回退会再次丢失时区信息，只能统一按 UTC 落成裸时间。
    """
    op.alter_column(
        'log_entries',
        'ts',
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=False,
        postgresql_using="ts AT TIME ZONE 'UTC'",
    )