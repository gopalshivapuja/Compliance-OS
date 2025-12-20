"""
Workflow Engine Service
Handles task lifecycle, assignments, and escalations
"""

from datetime import date, timedelta
from typing import Optional
from uuid import UUID


from sqlalchemy.orm import Session

from app.models import (
    WorkflowTask,
    ComplianceInstance,
    User,
    Role,
)
from app.models.entity import entity_access
from app.models.role import user_roles


# Standard workflow configuration (used when no custom workflow defined)
STANDARD_WORKFLOW = [
    {
        "step": "Prepare",
        "task_type": "Prepare",
        "description": "Prepare compliance documents and data",
        "sequence": 1,
    },
    {
        "step": "Review",
        "task_type": "Review",
        "description": "Review prepared documents for accuracy",
        "sequence": 2,
    },
    {
        "step": "CFO Approval",
        "task_type": "Approve",
        "description": "CFO/Approver sign-off on compliance",
        "sequence": 3,
        "role": "CFO",
    },
    {
        "step": "File",
        "task_type": "File",
        "description": "Submit/file the compliance with authority",
        "sequence": 4,
    },
    {
        "step": "Archive",
        "task_type": "Archive",
        "description": "Archive documents and close compliance",
        "sequence": 5,
    },
]


def resolve_role_to_user(db: Session, tenant_id: UUID, entity_id: UUID, role_code: str) -> Optional[User]:
    """
    Find a user with the given role who has access to the entity.

    Args:
        db: Database session
        tenant_id: Tenant UUID
        entity_id: Entity UUID
        role_code: Role code to match (e.g., "TAX_LEAD", "CFO")

    Returns:
        User with matching role and entity access, or None
    """
    # Find the role
    role = db.query(Role).filter(Role.role_code == role_code).first()
    if not role:
        return None

    # Find users with this role who have access to the entity
    user = (
        db.query(User)
        .join(user_roles, User.id == user_roles.c.user_id)
        .join(entity_access, User.id == entity_access.c.user_id)
        .filter(user_roles.c.role_id == role.id, entity_access.c.entity_id == entity_id, User.status == "active")
        .first()
    )

    return user


def get_role_by_code(db: Session, role_code: str) -> Optional[Role]:
    """Get a role by its code."""
    return db.query(Role).filter(Role.role_code == role_code).first()


def create_workflow_tasks(
    db: Session,
    instance: ComplianceInstance,
    workflow_config: Optional[list[dict]] = None,
    created_by: Optional[UUID] = None,
) -> list[WorkflowTask]:
    """
    Generate workflow tasks for a compliance instance.

    Args:
        db: Database session
        instance: ComplianceInstance to create tasks for
        workflow_config: Custom workflow config, or None for standard
        created_by: User UUID who triggered creation

    Returns:
        List of created WorkflowTask objects
    """
    created_tasks = []

    # Use custom workflow from master if defined, otherwise standard
    if workflow_config is None:
        if instance.compliance_master and instance.compliance_master.workflow_config:
            workflow_config = instance.compliance_master.workflow_config
        else:
            workflow_config = STANDARD_WORKFLOW

    # Get default owner role from master
    default_owner_role = None
    default_approver_role = None
    if instance.compliance_master:
        default_owner_role = instance.compliance_master.owner_role_code
        default_approver_role = instance.compliance_master.approver_role_code

    # Calculate task due dates based on instance due date
    # Tasks should complete before the instance due date
    total_tasks = len(workflow_config)
    days_before_due = 5  # Last task should be 5 days before due
    days_per_task = (
        max(2, (instance.due_date - date.today() - timedelta(days=days_before_due)).days // total_tasks)
        if total_tasks > 0
        else 2
    )

    previous_task = None

    for i, step in enumerate(workflow_config):
        task_type = step.get("task_type", step.get("step", "Task"))
        compliance_name = instance.compliance_master.compliance_name if instance.compliance_master else "Compliance"
        task_name = f"{step.get('step', task_type)} - {compliance_name}"
        task_description = step.get("description", f"Complete {task_type} step")
        sequence = step.get("sequence", i + 1)

        # Determine role for assignment
        role_code = step.get("role")
        if not role_code:
            # Use default roles based on task type
            if task_type in ["Approve"]:
                role_code = default_approver_role or "CFO"
            else:
                role_code = default_owner_role or "TAX_LEAD"

        # Try to resolve role to specific user
        assigned_user = resolve_role_to_user(db, instance.tenant_id, instance.entity_id, role_code)
        assigned_role = get_role_by_code(db, role_code) if not assigned_user else None

        # Calculate due date for this task
        task_due_date = instance.due_date - timedelta(days=(total_tasks - i) * days_per_task)
        if task_due_date < date.today():
            task_due_date = date.today() + timedelta(days=1)

        task = WorkflowTask(
            tenant_id=instance.tenant_id,
            compliance_instance_id=instance.id,
            task_type=task_type,
            task_name=task_name,
            task_description=task_description,
            assigned_to_user_id=assigned_user.id if assigned_user else None,
            assigned_to_role_id=assigned_role.id if assigned_role else None,
            status="Pending",
            due_date=task_due_date,
            sequence_order=sequence,
            parent_task_id=previous_task.id if previous_task else None,
            created_by=created_by,
            updated_by=created_by,
        )

        db.add(task)
        db.flush()  # Get the ID for next task's parent_task_id

        created_tasks.append(task)
        previous_task = task

    db.commit()

    # Refresh to get all relationships
    for task in created_tasks:
        db.refresh(task)

    return created_tasks


def get_tasks_for_instance(db: Session, compliance_instance_id: UUID) -> list[WorkflowTask]:
    """
    Get all workflow tasks for a compliance instance, ordered by sequence.

    Args:
        db: Database session
        compliance_instance_id: Instance UUID

    Returns:
        List of WorkflowTask objects ordered by sequence_order
    """
    return (
        db.query(WorkflowTask)
        .filter(WorkflowTask.compliance_instance_id == compliance_instance_id)
        .order_by(WorkflowTask.sequence_order)
        .all()
    )


def get_current_task(db: Session, compliance_instance_id: UUID) -> Optional[WorkflowTask]:
    """
    Get the current active task for an instance.

    Returns the first non-completed task in sequence order.

    Args:
        db: Database session
        compliance_instance_id: Instance UUID

    Returns:
        Current WorkflowTask or None if all completed
    """
    return (
        db.query(WorkflowTask)
        .filter(
            WorkflowTask.compliance_instance_id == compliance_instance_id,
            WorkflowTask.status.in_(["Pending", "In Progress"]),
        )
        .order_by(WorkflowTask.sequence_order)
        .first()
    )


def get_next_pending_task(db: Session, compliance_instance_id: UUID) -> Optional[WorkflowTask]:
    """
    Get the next pending task that can be started.

    Args:
        db: Database session
        compliance_instance_id: Instance UUID

    Returns:
        Next WorkflowTask or None
    """
    # Get all tasks ordered by sequence
    tasks = get_tasks_for_instance(db, compliance_instance_id)

    for task in tasks:
        if task.status == "Pending":
            # Check if parent task (if any) is completed
            if task.parent_task_id:
                parent = db.query(WorkflowTask).filter(WorkflowTask.id == task.parent_task_id).first()
                if parent and parent.status != "Completed":
                    return None  # Can't start until parent completes
            return task

    return None


def start_task(db: Session, task: WorkflowTask, user_id: UUID) -> WorkflowTask:
    """
    Start a workflow task (Pending -> In Progress).

    Args:
        db: Database session
        task: WorkflowTask to start
        user_id: User starting the task

    Returns:
        Updated WorkflowTask

    Raises:
        ValueError: If task cannot be started
    """
    if task.status != "Pending":
        raise ValueError(f"Cannot start task with status '{task.status}'")

    # Check parent task is completed
    if task.parent_task_id:
        parent = db.query(WorkflowTask).filter(WorkflowTask.id == task.parent_task_id).first()
        if parent and parent.status != "Completed":
            raise ValueError("Cannot start task: parent task not completed")

    task.status = "In Progress"
    task.started_at = date.today()
    task.updated_by = user_id

    db.commit()
    db.refresh(task)

    return task


def complete_task(
    db: Session, task: WorkflowTask, user_id: UUID, completion_remarks: Optional[str] = None
) -> WorkflowTask:
    """
    Complete a workflow task.

    Args:
        db: Database session
        task: WorkflowTask to complete
        user_id: User completing the task
        completion_remarks: Optional remarks

    Returns:
        Updated WorkflowTask

    Raises:
        ValueError: If task cannot be completed
    """
    if task.status not in ["Pending", "In Progress"]:
        raise ValueError(f"Cannot complete task with status '{task.status}'")

    task.status = "Completed"
    task.completed_at = date.today()
    task.completion_remarks = completion_remarks
    task.updated_by = user_id

    db.commit()
    db.refresh(task)

    # Check if all tasks are completed to update instance status
    check_instance_completion(db, task.compliance_instance)

    return task


def reject_task(db: Session, task: WorkflowTask, user_id: UUID, rejection_reason: str) -> WorkflowTask:
    """
    Reject a workflow task.

    Args:
        db: Database session
        task: WorkflowTask to reject
        user_id: User rejecting the task
        rejection_reason: Reason for rejection (required)

    Returns:
        Updated WorkflowTask

    Raises:
        ValueError: If task cannot be rejected
    """
    if task.status not in ["Pending", "In Progress"]:
        raise ValueError(f"Cannot reject task with status '{task.status}'")

    if not rejection_reason:
        raise ValueError("Rejection reason is required")

    task.status = "Rejected"
    task.rejection_reason = rejection_reason
    task.updated_by = user_id

    db.commit()
    db.refresh(task)

    return task


def reassign_task(
    db: Session,
    task: WorkflowTask,
    user_id: Optional[UUID] = None,
    role_id: Optional[UUID] = None,
    updated_by: Optional[UUID] = None,
) -> WorkflowTask:
    """
    Reassign a task to a different user or role.

    Args:
        db: Database session
        task: WorkflowTask to reassign
        user_id: User UUID to assign to (or None)
        role_id: Role UUID to assign to (or None)
        updated_by: User making the change

    Returns:
        Updated WorkflowTask
    """
    task.assigned_to_user_id = user_id
    task.assigned_to_role_id = role_id
    task.updated_by = updated_by

    db.commit()
    db.refresh(task)

    return task


def check_instance_completion(db: Session, instance: ComplianceInstance) -> bool:
    """
    Check if all workflow tasks are completed and update instance status.

    Args:
        db: Database session
        instance: ComplianceInstance to check

    Returns:
        True if instance is now completed, False otherwise
    """
    # Get all tasks for instance
    tasks = get_tasks_for_instance(db, instance.id)

    if not tasks:
        return False

    # Check if all tasks are completed
    all_completed = all(task.status == "Completed" for task in tasks)

    if all_completed and instance.status != "Completed":
        instance.status = "Completed"
        instance.completion_date = date.today()
        instance.rag_status = "Green"
        db.commit()
        return True

    return False


def get_user_assigned_tasks(
    db: Session,
    user_id: UUID,
    tenant_id: UUID,
    status_filter: Optional[list[str]] = None,
    include_role_tasks: bool = True,
) -> list[WorkflowTask]:
    """
    Get tasks assigned to a user (directly or via role).

    Args:
        db: Database session
        user_id: User UUID
        tenant_id: Tenant UUID
        status_filter: Optional list of statuses to filter by
        include_role_tasks: Whether to include role-assigned tasks

    Returns:
        List of WorkflowTask objects
    """
    from sqlalchemy import or_

    query = db.query(WorkflowTask).filter(WorkflowTask.tenant_id == tenant_id)

    if include_role_tasks:
        # Get user's role IDs
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            role_ids = [role.id for role in user.roles]
            query = query.filter(
                or_(
                    WorkflowTask.assigned_to_user_id == user_id,
                    WorkflowTask.assigned_to_role_id.in_(role_ids) if role_ids else False,
                )
            )
        else:
            query = query.filter(WorkflowTask.assigned_to_user_id == user_id)
    else:
        query = query.filter(WorkflowTask.assigned_to_user_id == user_id)

    if status_filter:
        query = query.filter(WorkflowTask.status.in_(status_filter))

    return query.order_by(WorkflowTask.due_date).all()


def get_overdue_tasks(db: Session, tenant_id: UUID, today: Optional[date] = None) -> list[WorkflowTask]:
    """
    Get all overdue tasks for a tenant.

    Args:
        db: Database session
        tenant_id: Tenant UUID
        today: Reference date (defaults to today)

    Returns:
        List of overdue WorkflowTask objects
    """
    if today is None:
        today = date.today()

    return (
        db.query(WorkflowTask)
        .filter(
            WorkflowTask.tenant_id == tenant_id,
            WorkflowTask.status.in_(["Pending", "In Progress"]),
            WorkflowTask.due_date < today,
        )
        .order_by(WorkflowTask.due_date)
        .all()
    )


def get_tasks_due_soon(db: Session, tenant_id: UUID, days: int = 3, today: Optional[date] = None) -> list[WorkflowTask]:
    """
    Get tasks due within the next X days.

    Args:
        db: Database session
        tenant_id: Tenant UUID
        days: Number of days to look ahead
        today: Reference date (defaults to today)

    Returns:
        List of upcoming WorkflowTask objects
    """
    if today is None:
        today = date.today()

    end_date = today + timedelta(days=days)

    return (
        db.query(WorkflowTask)
        .filter(
            WorkflowTask.tenant_id == tenant_id,
            WorkflowTask.status.in_(["Pending", "In Progress"]),
            WorkflowTask.due_date >= today,
            WorkflowTask.due_date <= end_date,
        )
        .order_by(WorkflowTask.due_date)
        .all()
    )


def update_instance_status_from_tasks(db: Session, instance: ComplianceInstance) -> str:
    """
    Update instance status based on workflow task states.

    Args:
        db: Database session
        instance: ComplianceInstance to update

    Returns:
        New status string
    """
    tasks = get_tasks_for_instance(db, instance.id)

    if not tasks:
        return instance.status

    # Count task statuses
    completed_count = sum(1 for t in tasks if t.status == "Completed")
    in_progress_count = sum(1 for t in tasks if t.status == "In Progress")
    rejected_count = sum(1 for t in tasks if t.status == "Rejected")

    total = len(tasks)

    if completed_count == total:
        new_status = "Completed"
    elif rejected_count > 0:
        new_status = "Blocked"
    elif in_progress_count > 0 or completed_count > 0:
        new_status = "In Progress"
    else:
        new_status = "Not Started"

    if instance.status != new_status:
        instance.status = new_status
        db.commit()

    return new_status
