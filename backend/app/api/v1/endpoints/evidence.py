"""
Evidence management endpoints
"""

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_tenant_id
from app.models import (
    Evidence,
    ComplianceInstance,
)
from app.models.entity import entity_access
from app.schemas import (
    EvidenceApprovalRequest,
    EvidenceRejectionRequest,
    EvidenceResponse,
    EvidenceListResponse,
    EvidenceDownloadResponse,
)
from app.services import log_action

router = APIRouter()

# Configuration
ALLOWED_FILE_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # xlsx
    "application/vnd.ms-excel",  # xls
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # docx
    "application/msword",  # doc
    "text/csv",
    "application/zip",
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
STORAGE_PATH = Path("storage/evidence")


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


def _build_evidence_response(evidence: Evidence, db: Session) -> dict:
    """Build evidence response with related entity information."""
    response = {
        "id": str(evidence.id),
        "tenant_id": str(evidence.tenant_id),
        "compliance_instance_id": str(evidence.compliance_instance_id),
        "evidence_name": evidence.evidence_name,
        "file_path": evidence.file_path,
        "file_type": evidence.file_type,
        "file_size": evidence.file_size,
        "file_hash": evidence.file_hash,
        "version": evidence.version,
        "parent_evidence_id": (
            str(evidence.parent_evidence_id) if evidence.parent_evidence_id else None
        ),
        "approval_status": evidence.approval_status,
        "approved_by_user_id": (
            str(evidence.approved_by_user_id) if evidence.approved_by_user_id else None
        ),
        "approved_at": evidence.approved_at,
        "approval_remarks": evidence.approval_remarks,
        "rejection_reason": evidence.rejection_reason,
        "is_immutable": evidence.is_immutable,
        "description": evidence.description,
        "meta_data": evidence.meta_data,
        "created_at": evidence.created_at,
        "updated_at": evidence.updated_at,
        "created_by": str(evidence.created_by) if evidence.created_by else None,
        "updated_by": str(evidence.updated_by) if evidence.updated_by else None,
    }

    # Get compliance instance info
    instance = evidence.compliance_instance
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

    # Get approved by user name
    if evidence.approved_by:
        response["approved_by_name"] = (
            f"{evidence.approved_by.first_name} {evidence.approved_by.last_name}"
        )
    else:
        response["approved_by_name"] = None

    return response


def _compute_file_hash(file_content: bytes) -> str:
    """Compute SHA-256 hash of file content."""
    return hashlib.sha256(file_content).hexdigest()


def _save_file(tenant_id: str, instance_id: str, filename: str, file_content: bytes) -> str:
    """Save file to local storage and return the path."""
    # Create directory structure: storage/evidence/{tenant_id}/{year}/{month}/
    now = datetime.now()
    dir_path = STORAGE_PATH / tenant_id / str(now.year) / f"{now.month:02d}"
    dir_path.mkdir(parents=True, exist_ok=True)

    # Generate unique filename to avoid collisions
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    unique_filename = f"{timestamp}_{instance_id[:8]}_{filename}"
    file_path = dir_path / unique_filename

    # Save file
    with open(file_path, "wb") as f:
        f.write(file_content)

    return str(file_path)


@router.get("/", response_model=EvidenceListResponse)
async def list_evidence(
    compliance_instance_id: Optional[str] = Query(None, description="Filter by instance"),
    entity_id: Optional[str] = Query(None, description="Filter by entity"),
    approval_status: Optional[str] = Query(None, description="Filter by approval status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    List evidence files for current tenant.
    Non-admin users only see evidence for entities they have access to.
    """
    tenant_uuid = UUID(tenant_id)
    is_admin = "admin" in current_user.get("roles", [])
    user_id = UUID(current_user["user_id"])

    # Base query with eager loading
    query = (
        db.query(Evidence)
        .options(
            joinedload(Evidence.compliance_instance).joinedload(ComplianceInstance.entity),
            joinedload(Evidence.compliance_instance).joinedload(
                ComplianceInstance.compliance_master
            ),
            joinedload(Evidence.approved_by),
        )
        .filter(Evidence.tenant_id == tenant_uuid)
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

        # Filter evidence by instance entity
        query = query.join(
            ComplianceInstance, Evidence.compliance_instance_id == ComplianceInstance.id
        ).filter(ComplianceInstance.entity_id.in_(accessible_ids))

    # Apply filters
    if compliance_instance_id:
        query = query.filter(Evidence.compliance_instance_id == UUID(compliance_instance_id))
    if entity_id:
        # Need to join if not already joined
        if is_admin:
            query = query.join(
                ComplianceInstance, Evidence.compliance_instance_id == ComplianceInstance.id
            )
        query = query.filter(ComplianceInstance.entity_id == UUID(entity_id))
    if approval_status:
        query = query.filter(Evidence.approval_status == approval_status)

    # Get total count
    total = query.count()

    # Apply pagination and ordering
    evidence_items = query.order_by(Evidence.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "items": [_build_evidence_response(ev, db) for ev in evidence_items],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(
    evidence_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    Get evidence metadata by ID.
    """
    tenant_uuid = UUID(tenant_id)
    evidence_uuid = UUID(evidence_id)

    evidence = (
        db.query(Evidence)
        .options(
            joinedload(Evidence.compliance_instance).joinedload(ComplianceInstance.entity),
            joinedload(Evidence.compliance_instance).joinedload(
                ComplianceInstance.compliance_master
            ),
            joinedload(Evidence.approved_by),
        )
        .filter(Evidence.id == evidence_uuid, Evidence.tenant_id == tenant_uuid)
        .first()
    )

    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")

    # Check entity access
    instance = evidence.compliance_instance
    if instance and not _check_entity_access(db, current_user, instance.entity_id, tenant_uuid):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this evidence's entity",
        )

    return _build_evidence_response(evidence, db)


@router.post("/upload", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    file: UploadFile = File(...),
    compliance_instance_id: str = Form(...),
    evidence_name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    Upload evidence file.
    """
    tenant_uuid = UUID(tenant_id)
    user_id = UUID(current_user["user_id"])
    instance_uuid = UUID(compliance_instance_id)

    # Validate compliance instance exists
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

    # Validate file type
    content_type = file.content_type
    if content_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid file type: {content_type}. "
                "Allowed types: PDF, PNG, JPEG, XLSX, XLS, DOCX, DOC, CSV, ZIP"
            ),
        )

    # Read file content
    file_content = await file.read()

    # Validate file size
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE // (1024 * 1024)}MB",
        )

    # Compute file hash
    file_hash = _compute_file_hash(file_content)

    # Use filename if evidence_name not provided
    final_name = evidence_name or file.filename

    # Save file
    file_path = _save_file(tenant_id, compliance_instance_id, file.filename, file_content)

    # Create evidence record
    evidence = Evidence(
        tenant_id=tenant_uuid,
        compliance_instance_id=instance_uuid,
        evidence_name=final_name,
        file_path=file_path,
        file_type=content_type,
        file_size=len(file_content),
        file_hash=file_hash,
        version=1,
        approval_status="Pending",
        is_immutable=False,
        description=description,
        created_by=user_id,
        updated_by=user_id,
    )

    db.add(evidence)
    db.commit()
    db.refresh(evidence)

    # Log action
    await log_action(
        db=db,
        tenant_id=tenant_uuid,
        user_id=user_id,
        action_type="CREATE",
        resource_type="evidence",
        resource_id=evidence.id,
        new_values={
            "evidence_name": evidence.evidence_name,
            "file_hash": evidence.file_hash,
            "compliance_instance_id": str(instance_uuid),
        },
    )

    # Reload with relationships
    evidence = (
        db.query(Evidence)
        .options(
            joinedload(Evidence.compliance_instance).joinedload(ComplianceInstance.entity),
            joinedload(Evidence.compliance_instance).joinedload(
                ComplianceInstance.compliance_master
            ),
            joinedload(Evidence.approved_by),
        )
        .filter(Evidence.id == evidence.id)
        .first()
    )

    return _build_evidence_response(evidence, db)


@router.get("/{evidence_id}/download", response_model=EvidenceDownloadResponse)
async def download_evidence(
    evidence_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    Download evidence file (returns signed URL or file path).
    """
    tenant_uuid = UUID(tenant_id)
    evidence_uuid = UUID(evidence_id)

    evidence = (
        db.query(Evidence)
        .options(joinedload(Evidence.compliance_instance))
        .filter(Evidence.id == evidence_uuid, Evidence.tenant_id == tenant_uuid)
        .first()
    )

    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")

    # Check entity access
    instance = evidence.compliance_instance
    if instance and not _check_entity_access(db, current_user, instance.entity_id, tenant_uuid):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this evidence's entity",
        )

    # For local storage, return file path as URL
    # In production, this would be a signed S3 URL
    download_url = f"file://{os.path.abspath(evidence.file_path)}"

    # Log download action
    await log_action(
        db=db,
        tenant_id=tenant_uuid,
        user_id=UUID(current_user["user_id"]),
        action_type="DOWNLOAD",
        resource_type="evidence",
        resource_id=evidence.id,
        new_values={"evidence_name": evidence.evidence_name},
    )

    return {
        "evidence_id": str(evidence.id),
        "evidence_name": evidence.evidence_name,
        "download_url": download_url,
        "expires_in_seconds": 300,
    }


@router.post("/{evidence_id}/approve", response_model=EvidenceResponse)
async def approve_evidence(
    evidence_id: str,
    approval_data: EvidenceApprovalRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    Approve evidence file.
    Sets is_immutable = true to prevent deletion.
    """
    tenant_uuid = UUID(tenant_id)
    evidence_uuid = UUID(evidence_id)
    user_id = UUID(current_user["user_id"])

    evidence = (
        db.query(Evidence)
        .options(joinedload(Evidence.compliance_instance))
        .filter(Evidence.id == evidence_uuid, Evidence.tenant_id == tenant_uuid)
        .first()
    )

    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")

    # Check entity access
    instance = evidence.compliance_instance
    if instance and not _check_entity_access(db, current_user, instance.entity_id, tenant_uuid):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this evidence's entity",
        )

    # Check if already approved
    if evidence.approval_status != "Pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Cannot approve evidence with status '{evidence.approval_status}'. "
                "Only pending evidence can be approved."
            ),
        )

    old_status = evidence.approval_status

    # Update approval
    evidence.approval_status = "Approved"
    evidence.approved_by_user_id = user_id
    evidence.approved_at = datetime.now(timezone.utc)
    evidence.approval_remarks = approval_data.remarks
    evidence.is_immutable = True
    evidence.updated_by = user_id
    db.commit()
    db.refresh(evidence)

    # Log action
    await log_action(
        db=db,
        tenant_id=tenant_uuid,
        user_id=user_id,
        action_type="APPROVE",
        resource_type="evidence",
        resource_id=evidence.id,
        old_values={"status": old_status},
        new_values={
            "status": evidence.approval_status,
            "is_immutable": True,
            "remarks": approval_data.remarks,
        },
    )

    # Reload with relationships
    evidence = (
        db.query(Evidence)
        .options(
            joinedload(Evidence.compliance_instance).joinedload(ComplianceInstance.entity),
            joinedload(Evidence.compliance_instance).joinedload(
                ComplianceInstance.compliance_master
            ),
            joinedload(Evidence.approved_by),
        )
        .filter(Evidence.id == evidence.id)
        .first()
    )

    return _build_evidence_response(evidence, db)


@router.post("/{evidence_id}/reject", response_model=EvidenceResponse)
async def reject_evidence(
    evidence_id: str,
    reject_data: EvidenceRejectionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    Reject evidence file.
    """
    tenant_uuid = UUID(tenant_id)
    evidence_uuid = UUID(evidence_id)
    user_id = UUID(current_user["user_id"])

    evidence = (
        db.query(Evidence)
        .options(joinedload(Evidence.compliance_instance))
        .filter(Evidence.id == evidence_uuid, Evidence.tenant_id == tenant_uuid)
        .first()
    )

    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")

    # Check entity access
    instance = evidence.compliance_instance
    if instance and not _check_entity_access(db, current_user, instance.entity_id, tenant_uuid):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this evidence's entity",
        )

    # Check if approved (immutable)
    if evidence.approval_status == "Approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reject approved evidence. Approved evidence is immutable.",
        )

    if evidence.approval_status == "Rejected":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Evidence is already rejected.",
        )

    old_status = evidence.approval_status

    # Update rejection
    evidence.approval_status = "Rejected"
    evidence.rejection_reason = reject_data.rejection_reason
    evidence.updated_by = user_id
    db.commit()
    db.refresh(evidence)

    # Log action
    await log_action(
        db=db,
        tenant_id=tenant_uuid,
        user_id=user_id,
        action_type="REJECT",
        resource_type="evidence",
        resource_id=evidence.id,
        old_values={"status": old_status},
        new_values={
            "status": evidence.approval_status,
            "rejection_reason": reject_data.rejection_reason,
        },
    )

    # Reload with relationships
    evidence = (
        db.query(Evidence)
        .options(
            joinedload(Evidence.compliance_instance).joinedload(ComplianceInstance.entity),
            joinedload(Evidence.compliance_instance).joinedload(
                ComplianceInstance.compliance_master
            ),
            joinedload(Evidence.approved_by),
        )
        .filter(Evidence.id == evidence.id)
        .first()
    )

    return _build_evidence_response(evidence, db)


@router.delete("/{evidence_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_evidence(
    evidence_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    Delete evidence file. Only pending/rejected evidence can be deleted.
    Approved evidence is immutable.
    """
    tenant_uuid = UUID(tenant_id)
    evidence_uuid = UUID(evidence_id)
    user_id = UUID(current_user["user_id"])

    evidence = (
        db.query(Evidence)
        .options(joinedload(Evidence.compliance_instance))
        .filter(Evidence.id == evidence_uuid, Evidence.tenant_id == tenant_uuid)
        .first()
    )

    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")

    # Check entity access
    instance = evidence.compliance_instance
    if instance and not _check_entity_access(db, current_user, instance.entity_id, tenant_uuid):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this evidence's entity",
        )

    # Check if immutable (approved)
    if evidence.is_immutable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Cannot delete approved evidence. "
                "Approved evidence is immutable for audit purposes."
            ),
        )

    # Log action before deletion
    await log_action(
        db=db,
        tenant_id=tenant_uuid,
        user_id=user_id,
        action_type="DELETE",
        resource_type="evidence",
        resource_id=evidence.id,
        old_values={
            "evidence_name": evidence.evidence_name,
            "file_hash": evidence.file_hash,
        },
    )

    # Delete file from storage (optional - could also just mark as deleted)
    if os.path.exists(evidence.file_path):
        os.remove(evidence.file_path)

    db.delete(evidence)
    db.commit()

    return None
