"""
Workflow Task management endpoints
"""

from datetime import date
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_tenant_id
from app.models import (
    WorkflowTask,
    ComplianceInstance,
    User,
    Role,
)
from app.models.entity import entity_access
from app.schemas import (
    WorkflowTaskCreate,
    WorkflowTaskUpdate,
    WorkflowTaskActionRequest,
    WorkflowTaskRejectRequest,
    WorkflowTaskResponse,
    WorkflowTaskListResponse,
)
from app.services import log_action

router = APIRouter()


def _check_entity_access(db: Session, user: dict, entity_id: UUID, tenant_id: UUID) -> bool:
    """Check if user has access to an entity."""
    # Admins have access to all entities
    if "admin" in user.get("roles", []):
        return True

    # Check entity_access table
    user_id = UUID(user["user_id"])
    result = db.execute(
        entity_access.select().where(
            entity_access.c.user_id == user_id,
            entity_access.c.entity_id == entity_id,
            entity_access.c.tenant_id == tenant_id,
        )
    ).first()

    return result is not None


def _build_task_response(task: WorkflowTask, db: Session) -> dict:
    """Build task response with related entity information."""
    response = {
        "id": str(task.id),
        "tenant_id": str(task.tenant_id),
        "compliance_instance_id": str(task.compliance_instance_id),
        "task_type": task.task_type,
        "task_name": task.task_name,
        "task_description": task.task_description,
        "assigned_to_user_id": str(task.assigned_to_user_id) if task.assigned_to_user_id else None,
        "assigned_to_role_id": str(task.assigned_to_role_id) if task.assigned_to_role_id else None,
        "status": task.status,
        "due_date": task.due_date,
        "started_at": task.started_at,
        "completed_at": task.completed_at,
        "sequence_order": task.sequence_order,
        "parent_task_id": str(task.parent_task_id) if task.parent_task_id else None,
        "completion_remarks": task.completion_remarks,
        "rejection_reason": task.rejection_reason,
        "meta_data": task.meta_data,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "created_by": str(task.created_by) if task.created_by else None,
        "updated_by": str(task.updated_by) if task.updated_by else None,
    }

    # Get compliance instance info
    instance = task.compliance_instance
    if instance:
        response["entity_id"] = str(instance.entity_id) if instance.entity_id else None
        if instance.entity:
            response["entity_name"] = instance.entity.entity_name
        else:
            response["entity_name"] = None

        if instance.compliance_master:
            response["compliance_code"] = instance.compliance_master.compliance_code
            response["compliance_name"] = instance.compliance_master.compliance_name
        else:
            response["compliance_code"] = None
            response["compliance_name"] = None
    else:
        response["entity_id"] = None
        response["entity_name"] = None
        response["compliance_code"] = None
        response["compliance_name"] = None

    # Get assigned user name
    if task.assigned_user:
        response["assigned_user_name"] = (
            f"{task.assigned_user.first_name} {task.assigned_user.last_name}"
        )
    else:
        response["assigned_user_name"] = None

    # Get assigned role name
    if task.assigned_role:
        response["assigned_role_name"] = task.assigned_role.role_name
    else:
        response["assigned_role_name"] = None

    return response


@router.get("/", response_model=WorkflowTaskListResponse)
async def list_workflow_tasks(
    compliance_instance_id: Optional[str] = Query(
        None, description="Filter by compliance instance"
    ),
    assigned_to_user_id: Optional[str] = Query(None, description="Filter by assigned user"),
    status: Optional[str] = Query(None, description="Filter by status"),
    task_type: Optional[str] = Query(None, description="Filter by task type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    List workflow tasks for current tenant.
    Non-admin users only see tasks for entities they have access to.
    """
    tenant_uuid = UUID(tenant_id)
    is_admin = "admin" in current_user.get("roles", [])
    user_id = UUID(current_user["user_id"])

    # Base query with eager loading
    query = (
        db.query(WorkflowTask)
        .options(
            joinedload(WorkflowTask.compliance_instance).joinedload(ComplianceInstance.entity),
            joinedload(WorkflowTask.compliance_instance).joinedload(
                ComplianceInstance.compliance_master
            ),
            joinedload(WorkflowTask.assigned_user),
            joinedload(WorkflowTask.assigned_role),
        )
        .filter(WorkflowTask.tenant_id == tenant_uuid)
    )

    # Non-admin users: filter by entity access
    if not is_admin:
        # Get accessible entity IDs
        accessible_entity_ids = db.execute(
            entity_access.select().where(
                entity_access.c.user_id == user_id,
                entity_access.c.tenant_id == tenant_uuid,
            )
        ).fetchall()
        accessible_ids = [row.entity_id for row in accessible_entity_ids]

        # Filter tasks by instance entity
        query = query.join(
            ComplianceInstance, WorkflowTask.compliance_instance_id == ComplianceInstance.id
        ).filter(ComplianceInstance.entity_id.in_(accessible_ids))

    # Apply filters
    if compliance_instance_id:
        query = query.filter(WorkflowTask.compliance_instance_id == UUID(compliance_instance_id))
    if assigned_to_user_id:
        query = query.filter(WorkflowTask.assigned_to_user_id == UUID(assigned_to_user_id))
    if status:
        query = query.filter(WorkflowTask.status == status)
    if task_type:
        query = query.filter(WorkflowTask.task_type == task_type)

    # Get total count
    total = query.count()

    # Apply pagination and ordering
    tasks = (
        query.order_by(WorkflowTask.sequence_order, WorkflowTask.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "items": [_build_task_response(task, db) for task in tasks],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/{task_id}", response_model=WorkflowTaskResponse)
async def get_workflow_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    Get workflow task by ID.
    """
    tenant_uuid = UUID(tenant_id)
    task_uuid = UUID(task_id)

    task = (
        db.query(WorkflowTask)
        .options(
            joinedload(WorkflowTask.compliance_instance).joinedload(ComplianceInstance.entity),
            joinedload(WorkflowTask.compliance_instance).joinedload(
                ComplianceInstance.compliance_master
            ),
            joinedload(WorkflowTask.assigned_user),
            joinedload(WorkflowTask.assigned_role),
        )
        .filter(WorkflowTask.id == task_uuid, WorkflowTask.tenant_id == tenant_uuid)
        .first()
    )

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow task not found")

    # Check entity access
    instance = task.compliance_instance
    if instance and not _check_entity_access(db, current_user, instance.entity_id, tenant_uuid):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this task's entity",
        )

    return _build_task_response(task, db)


@router.post("/", response_model=WorkflowTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow_task(
    task_data: WorkflowTaskCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    Create a new workflow task.
    """
    tenant_uuid = UUID(tenant_id)
    user_id = UUID(current_user["user_id"])

    # Validate compliance instance exists
    instance_uuid = UUID(task_data.compliance_instance_id)
    instance = (
        db.query(ComplianceInstance)
        .options(joinedload(ComplianceInstance.entity))
        .filter(
            ComplianceInstance.id == instance_uuid,
            ComplianceInstance.tenant_id == tenant_uuid,
        )
        .first()
    )

    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compliance instance not found",
        )

    # Check entity access
    if not _check_entity_access(db, current_user, instance.entity_id, tenant_uuid):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this instance's entity",
        )

    # Validate assigned user if provided
    if task_data.assigned_to_user_id:
        assigned_user = (
            db.query(User)
            .filter(
                User.id == UUID(task_data.assigned_to_user_id),
                User.tenant_id == tenant_uuid,
            )
            .first()
        )
        if not assigned_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assigned user not found",
            )

    # Validate assigned role if provided
    if task_data.assigned_to_role_id:
        assigned_role = (
            db.query(Role).filter(Role.id == UUID(task_data.assigned_to_role_id)).first()
        )
        if not assigned_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assigned role not found",
            )

    # Validate parent task if provided
    if task_data.parent_task_id:
        parent_task = (
            db.query(WorkflowTask)
            .filter(
                WorkflowTask.id == UUID(task_data.parent_task_id),
                WorkflowTask.tenant_id == tenant_uuid,
                WorkflowTask.compliance_instance_id == instance_uuid,
            )
            .first()
        )
        if not parent_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent task not found",
            )

    # Create task
    task = WorkflowTask(
        tenant_id=tenant_uuid,
        compliance_instance_id=instance_uuid,
        task_type=task_data.task_type,
        task_name=task_data.task_name,
        task_description=task_data.task_description,
        assigned_to_user_id=(
            UUID(task_data.assigned_to_user_id) if task_data.assigned_to_user_id else None
        ),
        assigned_to_role_id=(
            UUID(task_data.assigned_to_role_id) if task_data.assigned_to_role_id else None
        ),
        sequence_order=task_data.sequence_order,
        parent_task_id=UUID(task_data.parent_task_id) if task_data.parent_task_id else None,
        due_date=task_data.due_date,
        meta_data=task_data.meta_data,
        status="Pending",
        created_by=user_id,
        updated_by=user_id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    # Log action
    await log_action(
        db=db,
        tenant_id=tenant_uuid,
        user_id=user_id,
        action_type="CREATE",
        resource_type="workflow_task",
        resource_id=task.id,
        new_values={
            "task_type": task.task_type,
            "task_name": task.task_name,
            "compliance_instance_id": str(instance_uuid),
        },
    )

    # Reload with relationships
    task = (
        db.query(WorkflowTask)
        .options(
            joinedload(WorkflowTask.compliance_instance).joinedload(ComplianceInstance.entity),
            joinedload(WorkflowTask.compliance_instance).joinedload(
                ComplianceInstance.compliance_master
            ),
            joinedload(WorkflowTask.assigned_user),
            joinedload(WorkflowTask.assigned_role),
        )
        .filter(WorkflowTask.id == task.id)
        .first()
    )

    return _build_task_response(task, db)


@router.put("/{task_id}", response_model=WorkflowTaskResponse)
async def update_workflow_task(
    task_id: str,
    task_data: WorkflowTaskUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    Update workflow task (assignment, due date, etc.).
    """
    tenant_uuid = UUID(tenant_id)
    task_uuid = UUID(task_id)
    user_id = UUID(current_user["user_id"])

    task = (
        db.query(WorkflowTask)
        .options(joinedload(WorkflowTask.compliance_instance))
        .filter(WorkflowTask.id == task_uuid, WorkflowTask.tenant_id == tenant_uuid)
        .first()
    )

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow task not found")

    # Check entity access
    instance = task.compliance_instance
    if instance and not _check_entity_access(db, current_user, instance.entity_id, tenant_uuid):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this task's entity",
        )

    # Store old values for audit
    old_values = {
        "task_name": task.task_name,
        "task_description": task.task_description,
        "assigned_to_user_id": str(task.assigned_to_user_id) if task.assigned_to_user_id else None,
        "assigned_to_role_id": str(task.assigned_to_role_id) if task.assigned_to_role_id else None,
        "status": task.status,
        "due_date": str(task.due_date) if task.due_date else None,
        "sequence_order": task.sequence_order,
    }

    # Validate assigned user if provided
    if task_data.assigned_to_user_id:
        assigned_user = (
            db.query(User)
            .filter(
                User.id == UUID(task_data.assigned_to_user_id),
                User.tenant_id == tenant_uuid,
            )
            .first()
        )
        if not assigned_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assigned user not found",
            )

    # Apply updates
    update_data = task_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "assigned_to_user_id" and value:
            setattr(task, field, UUID(value))
        elif field == "assigned_to_role_id" and value:
            setattr(task, field, UUID(value))
        else:
            setattr(task, field, value)

    task.updated_by = user_id
    db.commit()
    db.refresh(task)

    # Log action
    new_values = {
        "task_name": task.task_name,
        "task_description": task.task_description,
        "assigned_to_user_id": str(task.assigned_to_user_id) if task.assigned_to_user_id else None,
        "assigned_to_role_id": str(task.assigned_to_role_id) if task.assigned_to_role_id else None,
        "status": task.status,
        "due_date": str(task.due_date) if task.due_date else None,
        "sequence_order": task.sequence_order,
    }

    await log_action(
        db=db,
        tenant_id=tenant_uuid,
        user_id=user_id,
        action_type="UPDATE",
        resource_type="workflow_task",
        resource_id=task.id,
        old_values=old_values,
        new_values=new_values,
    )

    # Reload with relationships
    task = (
        db.query(WorkflowTask)
        .options(
            joinedload(WorkflowTask.compliance_instance).joinedload(ComplianceInstance.entity),
            joinedload(WorkflowTask.compliance_instance).joinedload(
                ComplianceInstance.compliance_master
            ),
            joinedload(WorkflowTask.assigned_user),
            joinedload(WorkflowTask.assigned_role),
        )
        .filter(WorkflowTask.id == task.id)
        .first()
    )

    return _build_task_response(task, db)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    Delete a workflow task. Only pending tasks can be deleted.
    """
    tenant_uuid = UUID(tenant_id)
    task_uuid = UUID(task_id)
    user_id = UUID(current_user["user_id"])

    task = (
        db.query(WorkflowTask)
        .options(joinedload(WorkflowTask.compliance_instance))
        .filter(WorkflowTask.id == task_uuid, WorkflowTask.tenant_id == tenant_uuid)
        .first()
    )

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow task not found")

    # Check entity access
    instance = task.compliance_instance
    if instance and not _check_entity_access(db, current_user, instance.entity_id, tenant_uuid):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this task's entity",
        )

    # Only allow deletion of pending tasks
    if task.status != "Pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only delete tasks in Pending status",
        )

    # Log action before deletion
    await log_action(
        db=db,
        tenant_id=tenant_uuid,
        user_id=user_id,
        action_type="DELETE",
        resource_type="workflow_task",
        resource_id=task.id,
        old_values={
            "task_type": task.task_type,
            "task_name": task.task_name,
        },
    )

    db.delete(task)
    db.commit()

    return None


@router.post("/{task_id}/start", response_model=WorkflowTaskResponse)
async def start_task(
    task_id: str,
    action_data: WorkflowTaskActionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    Start a workflow task (transitions from Pending to In Progress).
    """
    tenant_uuid = UUID(tenant_id)
    task_uuid = UUID(task_id)
    user_id = UUID(current_user["user_id"])

    task = (
        db.query(WorkflowTask)
        .options(
            joinedload(WorkflowTask.compliance_instance),
            joinedload(WorkflowTask.parent_task),
        )
        .filter(WorkflowTask.id == task_uuid, WorkflowTask.tenant_id == tenant_uuid)
        .first()
    )

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow task not found")

    # Check entity access
    instance = task.compliance_instance
    if instance and not _check_entity_access(db, current_user, instance.entity_id, tenant_uuid):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this task's entity",
        )

    # Check current status
    if task.status != "Pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only start tasks in Pending status",
        )

    # Check parent task is completed
    if task.parent_task and task.parent_task.status != "Completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parent task must be completed first",
        )

    old_status = task.status

    # Update status
    task.status = "In Progress"
    task.started_at = date.today()
    task.updated_by = user_id
    db.commit()
    db.refresh(task)

    # Log action
    await log_action(
        db=db,
        tenant_id=tenant_uuid,
        user_id=user_id,
        action_type="START",
        resource_type="workflow_task",
        resource_id=task.id,
        old_values={"status": old_status},
        new_values={"status": task.status, "remarks": action_data.remarks},
    )

    # Reload with relationships
    task = (
        db.query(WorkflowTask)
        .options(
            joinedload(WorkflowTask.compliance_instance).joinedload(ComplianceInstance.entity),
            joinedload(WorkflowTask.compliance_instance).joinedload(
                ComplianceInstance.compliance_master
            ),
            joinedload(WorkflowTask.assigned_user),
            joinedload(WorkflowTask.assigned_role),
        )
        .filter(WorkflowTask.id == task.id)
        .first()
    )

    return _build_task_response(task, db)


@router.post("/{task_id}/complete", response_model=WorkflowTaskResponse)
async def complete_task(
    task_id: str,
    action_data: WorkflowTaskActionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    Mark task as completed.
    """
    tenant_uuid = UUID(tenant_id)
    task_uuid = UUID(task_id)
    user_id = UUID(current_user["user_id"])

    task = (
        db.query(WorkflowTask)
        .options(joinedload(WorkflowTask.compliance_instance))
        .filter(WorkflowTask.id == task_uuid, WorkflowTask.tenant_id == tenant_uuid)
        .first()
    )

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow task not found")

    # Check entity access
    instance = task.compliance_instance
    if instance and not _check_entity_access(db, current_user, instance.entity_id, tenant_uuid):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this task's entity",
        )

    # Check current status
    if task.status == "Completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task is already completed",
        )

    if task.status not in ["Pending", "In Progress"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only complete tasks in Pending or In Progress status",
        )

    old_status = task.status

    # Update status
    task.status = "Completed"
    task.completed_at = date.today()
    task.completion_remarks = action_data.remarks
    task.updated_by = user_id
    db.commit()
    db.refresh(task)

    # Log action
    await log_action(
        db=db,
        tenant_id=tenant_uuid,
        user_id=user_id,
        action_type="COMPLETE",
        resource_type="workflow_task",
        resource_id=task.id,
        old_values={"status": old_status},
        new_values={"status": task.status, "remarks": action_data.remarks},
    )

    # Reload with relationships
    task = (
        db.query(WorkflowTask)
        .options(
            joinedload(WorkflowTask.compliance_instance).joinedload(ComplianceInstance.entity),
            joinedload(WorkflowTask.compliance_instance).joinedload(
                ComplianceInstance.compliance_master
            ),
            joinedload(WorkflowTask.assigned_user),
            joinedload(WorkflowTask.assigned_role),
        )
        .filter(WorkflowTask.id == task.id)
        .first()
    )

    return _build_task_response(task, db)


@router.post("/{task_id}/reject", response_model=WorkflowTaskResponse)
async def reject_task(
    task_id: str,
    reject_data: WorkflowTaskRejectRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    Reject a workflow task.
    """
    tenant_uuid = UUID(tenant_id)
    task_uuid = UUID(task_id)
    user_id = UUID(current_user["user_id"])

    task = (
        db.query(WorkflowTask)
        .options(joinedload(WorkflowTask.compliance_instance))
        .filter(WorkflowTask.id == task_uuid, WorkflowTask.tenant_id == tenant_uuid)
        .first()
    )

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow task not found")

    # Check entity access
    instance = task.compliance_instance
    if instance and not _check_entity_access(db, current_user, instance.entity_id, tenant_uuid):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this task's entity",
        )

    # Check current status
    if task.status == "Completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task is already completed and cannot be rejected",
        )

    if task.status == "Rejected":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task is already rejected",
        )

    old_status = task.status

    # Update status
    task.status = "Rejected"
    task.rejection_reason = reject_data.rejection_reason
    task.updated_by = user_id
    db.commit()
    db.refresh(task)

    # Log action
    await log_action(
        db=db,
        tenant_id=tenant_uuid,
        user_id=user_id,
        action_type="REJECT",
        resource_type="workflow_task",
        resource_id=task.id,
        old_values={"status": old_status},
        new_values={"status": task.status, "rejection_reason": reject_data.rejection_reason},
    )

    # Reload with relationships
    task = (
        db.query(WorkflowTask)
        .options(
            joinedload(WorkflowTask.compliance_instance).joinedload(ComplianceInstance.entity),
            joinedload(WorkflowTask.compliance_instance).joinedload(
                ComplianceInstance.compliance_master
            ),
            joinedload(WorkflowTask.assigned_user),
            joinedload(WorkflowTask.assigned_role),
        )
        .filter(WorkflowTask.id == task.id)
        .first()
    )

    return _build_task_response(task, db)
