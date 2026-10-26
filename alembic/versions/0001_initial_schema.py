"""Create users, jobs and applications tables.

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-26
"""
import sqlalchemy as sa

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(length=150), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=9), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("employer_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("job_type", sa.String(length=10), nullable=False),
        sa.Column("salary_min", sa.Integer(), nullable=False),
        sa.Column("salary_max", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=6), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("salary_min >= 0", name="ck_jobs_salary_min_nonnegative"),
        sa.CheckConstraint("salary_max >= 0", name="ck_jobs_salary_max_nonnegative"),
        sa.CheckConstraint("salary_min <= salary_max", name="ck_jobs_salary_order"),
    )
    op.create_index("ix_jobs_employer_id", "jobs", ["employer_id"])
    op.create_index("ix_jobs_title", "jobs", ["title"])
    op.create_index("ix_jobs_job_type", "jobs", ["job_type"])
    op.create_index("ix_jobs_status", "jobs", ["status"])
    op.create_index("ix_jobs_status_created_at", "jobs", ["status", "created_at"])
    op.create_table(
        "applications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("jobs.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("candidate_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("cover_letter", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=9), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("job_id", "candidate_id", name="uq_application_job_candidate"),
    )
    op.create_index("ix_applications_candidate_created", "applications", ["candidate_id", "created_at"])
    op.create_index("ix_applications_job_created", "applications", ["job_id", "created_at"])


def downgrade() -> None:
    op.drop_table("applications")
    op.drop_table("jobs")
    op.drop_table("users")
