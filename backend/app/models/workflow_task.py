"""
Workflow Task model for compliance workflow management
"""

from sqlalchemy import Column, String, Text, Date, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.models.base import Base, UUIDMixin, TenantScopedMixin, AuditMixin


class WorkflowTask(Base, UUIDMixin, TenantScopedMixin, AuditMixin):
    """Workflow Task - actionable tasks within compliance instances"""

    __tablename__ = "workflow_tasks"

    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Reference to compliance instance
    compliance_instance_id = Column(
        UUID(as_uuid=True),
        ForeignKey("compliance_instances.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Task details
    task_type = Column(
        String(50), nullable=False, index=True
    )  # Prepare, Review, Approve, File, Archive
    task_name = Column(String(255), nullable=False)
    task_description = Column(Text, nullable=True)

    # Assignment - can be assigned to user OR role
    assigned_to_user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    assigned_to_role_id = Column(
        UUID(as_uuid=True), ForeignKey("roles.id", ondelete="SET NULL"), nullable=True
    )

    # Status and dates
    status = Column(
        String(50), nullable=False, default="Pending", index=True
    )  # Pending, In Progress, Completed, Rejected
    due_date = Column(Date, nullable=True, index=True)
    started_at = Column(Date, nullable=True)
    completed_at = Column(Date, nullable=True)

    # Workflow sequencing
    sequence_order = Column(Integer, nullable=False, default=1)  # Order in workflow
    parent_task_id = Column(
        UUID(as_uuid=True), ForeignKey("workflow_tasks.id", ondelete="SET NULL"), nullable=True
    )  # For sub-tasks

    # Completion details
    completion_remarks = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # Metadata
    meta_data = Column(JSONB, nullable=True)

    # Relationships
    compliance_instance = relationship("ComplianceInstance", back_populates="workflow_tasks")
    assigned_user = relationship(
        "User", foreign_keys=[assigned_to_user_id], back_populates="assigned_tasks"
    )
    assigned_role = relationship("Role", foreign_keys=[assigned_to_role_id])

    # Self-referential for sub-tasks
    parent_task = relationship(
        "WorkflowTask",
        remote_side="WorkflowTask.id",
        foreign_keys=[parent_task_id],
        backref="subtasks",
    )

    # Indexes for common queries
    __table_args__ = (
        Index(
            "idx_workflow_tasks_assigned_user_status", "assigned_to_user_id", "status", "due_date"
        ),
        Index("idx_workflow_tasks_instance_sequence", "compliance_instance_id", "sequence_order"),
    )

    def __repr__(self):
        return f"<WorkflowTask {self.task_type} - {self.task_name}: {self.status}>"
