"""
Evidence Service
Handles file upload, versioning, and approval workflow using Render Persistent Disk
"""

import hashlib
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, BinaryIO
from uuid import UUID, uuid4

from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Evidence, ComplianceInstance, Tag


# File extension to MIME type mapping
EXTENSION_MIME_MAP = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xls": "application/vnd.ms-excel",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".doc": "application/msword",
}


def get_storage_path() -> Path:
    """Get the base storage path, creating it if it doesn't exist."""
    path = Path(settings.EVIDENCE_STORAGE_PATH)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_evidence_directory(tenant_id: UUID, compliance_instance_id: UUID) -> Path:
    """
    Get the directory for storing evidence files.

    Structure: {base_path}/{tenant_id}/{compliance_instance_id}/
    """
    path = get_storage_path() / str(tenant_id) / str(compliance_instance_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def generate_file_hash(file: BinaryIO) -> str:
    """Generate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    for chunk in iter(lambda: file.read(8192), b""):
        sha256_hash.update(chunk)
    file.seek(0)  # Reset file position
    return sha256_hash.hexdigest()


def get_file_extension(filename: str) -> str:
    """Extract file extension from filename."""
    return Path(filename).suffix.lower()


def validate_file(file: UploadFile) -> tuple[bool, str]:
    """
    Validate file type and size.

    Args:
        file: UploadFile to validate

    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    # Check file size
    file.file.seek(0, 2)  # Seek to end
    size = file.file.tell()
    file.file.seek(0)  # Reset

    if size > settings.EVIDENCE_MAX_FILE_SIZE:
        max_mb = settings.EVIDENCE_MAX_FILE_SIZE // (1024 * 1024)
        return False, f"File size exceeds maximum allowed ({max_mb}MB)"

    if size == 0:
        return False, "File is empty"

    # Check file type
    extension = get_file_extension(file.filename or "")
    mime_type = EXTENSION_MIME_MAP.get(extension, file.content_type)

    if mime_type not in settings.EVIDENCE_ALLOWED_TYPES:
        allowed = ", ".join([ext for ext in EXTENSION_MIME_MAP.keys()])
        return False, f"File type not allowed. Allowed types: {allowed}"

    return True, ""


async def upload_evidence_file(
    db: Session,
    file: UploadFile,
    compliance_instance_id: UUID,
    uploaded_by: UUID,
    tenant_id: UUID,
    evidence_name: Optional[str] = None,
    description: Optional[str] = None,
    tag_ids: Optional[list[UUID]] = None,
) -> Evidence:
    """
    Upload an evidence file and create the database record.

    Args:
        db: Database session
        file: UploadFile to upload
        compliance_instance_id: Instance this evidence belongs to
        uploaded_by: User UUID uploading the file
        tenant_id: Tenant UUID
        evidence_name: Optional custom name (defaults to filename)
        description: Optional description
        tag_ids: Optional list of tag UUIDs to attach

    Returns:
        Created Evidence object

    Raises:
        HTTPException: If validation fails or instance not found
    """
    # Validate file
    is_valid, error_msg = validate_file(file)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    # Verify compliance instance exists and belongs to tenant
    instance = (
        db.query(ComplianceInstance)
        .filter(ComplianceInstance.id == compliance_instance_id, ComplianceInstance.tenant_id == tenant_id)
        .first()
    )

    if not instance:
        raise HTTPException(status_code=404, detail="Compliance instance not found")

    # Generate file hash
    file_hash = generate_file_hash(file.file)

    # Get file details
    extension = get_file_extension(file.filename or ".bin")
    file_size = file.file.seek(0, 2)
    file.file.seek(0)
    file_type = EXTENSION_MIME_MAP.get(extension, file.content_type)

    # Generate unique filename
    evidence_id = uuid4()
    stored_filename = f"{evidence_id}_v1{extension}"

    # Get storage directory
    storage_dir = get_evidence_directory(tenant_id, compliance_instance_id)
    file_path = storage_dir / stored_filename

    # Save file to disk
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Create Evidence record
    evidence = Evidence(
        id=evidence_id,
        tenant_id=tenant_id,
        compliance_instance_id=compliance_instance_id,
        evidence_name=evidence_name or file.filename or "Unnamed evidence",
        file_path=str(file_path),
        file_type=file_type,
        file_size=file_size,
        file_hash=file_hash,
        version=1,
        approval_status="Pending",
        is_immutable=False,
        description=description,
        created_by=uploaded_by,
        updated_by=uploaded_by,
    )

    # Add tags if provided
    if tag_ids:
        tags = db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
        evidence.tags = tags

    db.add(evidence)
    db.commit()
    db.refresh(evidence)

    return evidence


def get_evidence_file_path(evidence: Evidence) -> Path:
    """
    Get the file path for an evidence record.

    Args:
        evidence: Evidence object

    Returns:
        Path to the file

    Raises:
        HTTPException: If file not found
    """
    path = Path(evidence.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Evidence file not found on disk")
    return path


def get_evidence_by_id(db: Session, evidence_id: UUID, tenant_id: UUID) -> Optional[Evidence]:
    """
    Get evidence by ID with tenant check.

    Args:
        db: Database session
        evidence_id: Evidence UUID
        tenant_id: Tenant UUID

    Returns:
        Evidence object or None
    """
    return db.query(Evidence).filter(Evidence.id == evidence_id, Evidence.tenant_id == tenant_id).first()


def approve_evidence(
    db: Session, evidence_id: UUID, approved_by: UUID, tenant_id: UUID, approval_remarks: Optional[str] = None
) -> Evidence:
    """
    Approve an evidence file (CFO/Approver action).

    Args:
        db: Database session
        evidence_id: Evidence UUID to approve
        approved_by: User UUID approving
        tenant_id: Tenant UUID
        approval_remarks: Optional remarks

    Returns:
        Updated Evidence object

    Raises:
        HTTPException: If evidence not found or already processed
    """
    evidence = get_evidence_by_id(db, evidence_id, tenant_id)

    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    if evidence.approval_status != "Pending":
        raise HTTPException(status_code=400, detail=f"Evidence already {evidence.approval_status.lower()}")

    evidence.approval_status = "Approved"
    evidence.approved_by_user_id = approved_by
    evidence.approved_at = datetime.utcnow()
    evidence.approval_remarks = approval_remarks
    evidence.is_immutable = True  # Cannot be deleted after approval
    evidence.updated_by = approved_by

    db.commit()
    db.refresh(evidence)

    return evidence


def reject_evidence(
    db: Session, evidence_id: UUID, rejected_by: UUID, tenant_id: UUID, rejection_reason: str
) -> Evidence:
    """
    Reject an evidence file.

    Args:
        db: Database session
        evidence_id: Evidence UUID to reject
        rejected_by: User UUID rejecting
        tenant_id: Tenant UUID
        rejection_reason: Reason for rejection (required)

    Returns:
        Updated Evidence object

    Raises:
        HTTPException: If evidence not found or already processed
    """
    if not rejection_reason:
        raise HTTPException(status_code=400, detail="Rejection reason is required")

    evidence = get_evidence_by_id(db, evidence_id, tenant_id)

    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    if evidence.approval_status != "Pending":
        raise HTTPException(status_code=400, detail=f"Evidence already {evidence.approval_status.lower()}")

    evidence.approval_status = "Rejected"
    evidence.rejection_reason = rejection_reason
    evidence.updated_by = rejected_by

    db.commit()
    db.refresh(evidence)

    return evidence


async def create_evidence_version(
    db: Session,
    parent_evidence_id: UUID,
    file: UploadFile,
    uploaded_by: UUID,
    tenant_id: UUID,
    description: Optional[str] = None,
) -> Evidence:
    """
    Create a new version of an existing evidence file.

    Args:
        db: Database session
        parent_evidence_id: UUID of the evidence to create new version for
        file: New file to upload
        uploaded_by: User UUID uploading
        tenant_id: Tenant UUID
        description: Optional description for new version

    Returns:
        New Evidence object (incremented version)

    Raises:
        HTTPException: If parent not found or validation fails
    """
    # Get parent evidence
    parent = get_evidence_by_id(db, parent_evidence_id, tenant_id)
    if not parent:
        raise HTTPException(status_code=404, detail="Parent evidence not found")

    # Validate file
    is_valid, error_msg = validate_file(file)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    # Generate file hash
    file_hash = generate_file_hash(file.file)

    # Get file details
    extension = get_file_extension(file.filename or ".bin")
    file_size = file.file.seek(0, 2)
    file.file.seek(0)
    file_type = EXTENSION_MIME_MAP.get(extension, file.content_type)

    # Calculate new version number
    new_version = parent.version + 1

    # Generate unique filename with version
    evidence_id = uuid4()
    stored_filename = f"{evidence_id}_v{new_version}{extension}"

    # Get storage directory (same as parent)
    storage_dir = get_evidence_directory(tenant_id, parent.compliance_instance_id)
    file_path = storage_dir / stored_filename

    # Save file to disk
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Create new Evidence record
    new_evidence = Evidence(
        id=evidence_id,
        tenant_id=tenant_id,
        compliance_instance_id=parent.compliance_instance_id,
        evidence_name=parent.evidence_name,
        file_path=str(file_path),
        file_type=file_type,
        file_size=file_size,
        file_hash=file_hash,
        version=new_version,
        parent_evidence_id=parent.id,
        approval_status="Pending",
        is_immutable=False,
        description=description or parent.description,
        created_by=uploaded_by,
        updated_by=uploaded_by,
    )

    # Copy tags from parent
    new_evidence.tags = parent.tags

    db.add(new_evidence)
    db.commit()
    db.refresh(new_evidence)

    return new_evidence


def delete_evidence(db: Session, evidence_id: UUID, deleted_by: UUID, tenant_id: UUID) -> bool:
    """
    Delete an evidence file (only if not immutable).

    Args:
        db: Database session
        evidence_id: Evidence UUID to delete
        deleted_by: User UUID deleting
        tenant_id: Tenant UUID

    Returns:
        True if deleted successfully

    Raises:
        HTTPException: If evidence not found or is immutable
    """
    evidence = get_evidence_by_id(db, evidence_id, tenant_id)

    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    if evidence.is_immutable:
        raise HTTPException(status_code=400, detail="Cannot delete approved evidence (immutable)")

    # Delete file from disk
    file_path = Path(evidence.file_path)
    if file_path.exists():
        try:
            file_path.unlink()
        except Exception:
            pass  # Continue even if file deletion fails

    # Delete database record
    db.delete(evidence)
    db.commit()

    return True


def get_evidence_for_instance(
    db: Session,
    compliance_instance_id: UUID,
    tenant_id: UUID,
    approval_status: Optional[str] = None,
    latest_only: bool = False,
) -> list[Evidence]:
    """
    Get all evidence for a compliance instance.

    Args:
        db: Database session
        compliance_instance_id: Instance UUID
        tenant_id: Tenant UUID
        approval_status: Optional filter by status (Pending, Approved, Rejected)
        latest_only: If True, only return latest version of each evidence chain

    Returns:
        List of Evidence objects
    """
    query = db.query(Evidence).filter(
        Evidence.compliance_instance_id == compliance_instance_id, Evidence.tenant_id == tenant_id
    )

    if approval_status:
        query = query.filter(Evidence.approval_status == approval_status)

    if latest_only:
        # Only get evidence that has no newer versions
        subquery = db.query(Evidence.parent_evidence_id).filter(Evidence.parent_evidence_id.isnot(None))
        query = query.filter(~Evidence.id.in_(subquery))

    return query.order_by(Evidence.created_at.desc()).all()


def get_evidence_version_history(db: Session, evidence_id: UUID, tenant_id: UUID) -> list[Evidence]:
    """
    Get the complete version history for an evidence file.

    Args:
        db: Database session
        evidence_id: Any version's UUID in the chain
        tenant_id: Tenant UUID

    Returns:
        List of Evidence objects (all versions, oldest first)
    """
    # Start with the given evidence
    evidence = get_evidence_by_id(db, evidence_id, tenant_id)
    if not evidence:
        return []

    # Find the root (oldest version)
    root = evidence
    while root.parent_evidence_id:
        parent = get_evidence_by_id(db, root.parent_evidence_id, tenant_id)
        if parent:
            root = parent
        else:
            break

    # Now get all versions from root
    versions = [root]
    current = root
    while True:
        # Find child version
        child = (
            db.query(Evidence)
            .filter(Evidence.parent_evidence_id == current.id, Evidence.tenant_id == tenant_id)
            .first()
        )
        if child:
            versions.append(child)
            current = child
        else:
            break

    return versions


def get_pending_approvals(db: Session, tenant_id: UUID) -> list[Evidence]:
    """
    Get all evidence pending approval for a tenant.

    Args:
        db: Database session
        tenant_id: Tenant UUID

    Returns:
        List of pending Evidence objects
    """
    return (
        db.query(Evidence)
        .filter(Evidence.tenant_id == tenant_id, Evidence.approval_status == "Pending")
        .order_by(Evidence.created_at.desc())
        .all()
    )


def check_duplicate_evidence(
    db: Session, file_hash: str, compliance_instance_id: UUID, tenant_id: UUID
) -> Optional[Evidence]:
    """
    Check if evidence with same hash already exists for this instance.

    Args:
        db: Database session
        file_hash: SHA-256 hash of the file
        compliance_instance_id: Instance UUID
        tenant_id: Tenant UUID

    Returns:
        Existing Evidence if duplicate found, None otherwise
    """
    return (
        db.query(Evidence)
        .filter(
            Evidence.file_hash == file_hash,
            Evidence.compliance_instance_id == compliance_instance_id,
            Evidence.tenant_id == tenant_id,
        )
        .first()
    )
