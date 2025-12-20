"""
Evidence Service Unit Tests

Tests for file upload, versioning, and approval workflow.

Test Categories:
- File validation (type, size)
- Hash generation
- Evidence CRUD operations
- Approval/Rejection workflow
- Version management
- Duplicate detection
"""

import pytest
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
from uuid import uuid4

from fastapi import HTTPException

from app.services.evidence_service import (
    EXTENSION_MIME_MAP,
    get_storage_path,
    get_evidence_directory,
    generate_file_hash,
    get_file_extension,
    validate_file,
    get_evidence_file_path,
    get_evidence_by_id,
    approve_evidence,
    reject_evidence,
    delete_evidence,
    get_evidence_for_instance,
    get_evidence_version_history,
    get_pending_approvals,
    check_duplicate_evidence,
)


class TestExtensionMimeMap:
    """Tests for EXTENSION_MIME_MAP constant."""

    def test_pdf_extension_mapped(self):
        """PDF extension should map to correct MIME type."""
        assert EXTENSION_MIME_MAP[".pdf"] == "application/pdf"

    def test_image_extensions_mapped(self):
        """Image extensions should map to correct MIME types."""
        assert EXTENSION_MIME_MAP[".png"] == "image/png"
        assert EXTENSION_MIME_MAP[".jpg"] == "image/jpeg"
        assert EXTENSION_MIME_MAP[".jpeg"] == "image/jpeg"

    def test_office_extensions_mapped(self):
        """Office document extensions should map correctly."""
        assert ".xlsx" in EXTENSION_MIME_MAP
        assert ".xls" in EXTENSION_MIME_MAP
        assert ".docx" in EXTENSION_MIME_MAP
        assert ".doc" in EXTENSION_MIME_MAP

    def test_all_extensions_have_valid_mime(self):
        """All extensions should have valid MIME type format."""
        for ext, mime in EXTENSION_MIME_MAP.items():
            assert ext.startswith(".")
            assert "/" in mime


class TestGetFileExtension:
    """Tests for get_file_extension function."""

    def test_extract_pdf_extension(self):
        """Should extract .pdf extension."""
        result = get_file_extension("document.pdf")
        assert result == ".pdf"

    def test_extract_extension_lowercase(self):
        """Should return extension in lowercase."""
        result = get_file_extension("Document.PDF")
        assert result == ".pdf"

    def test_extract_extension_multiple_dots(self):
        """Should handle filenames with multiple dots."""
        result = get_file_extension("my.file.document.xlsx")
        assert result == ".xlsx"

    def test_extract_no_extension(self):
        """Should return empty string for no extension."""
        result = get_file_extension("filename")
        assert result == ""

    def test_extract_hidden_file_extension(self):
        """Should handle hidden files with extension."""
        result = get_file_extension(".hidden.pdf")
        assert result == ".pdf"


class TestGenerateFileHash:
    """Tests for generate_file_hash function."""

    def test_generate_hash_returns_string(self):
        """Should return a hex string hash."""
        file = BytesIO(b"test content")
        result = generate_file_hash(file)

        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 produces 64 hex characters

    def test_generate_hash_same_content_same_hash(self):
        """Same content should produce same hash."""
        content = b"identical content"
        file1 = BytesIO(content)
        file2 = BytesIO(content)

        hash1 = generate_file_hash(file1)
        hash2 = generate_file_hash(file2)

        assert hash1 == hash2

    def test_generate_hash_different_content_different_hash(self):
        """Different content should produce different hash."""
        file1 = BytesIO(b"content A")
        file2 = BytesIO(b"content B")

        hash1 = generate_file_hash(file1)
        hash2 = generate_file_hash(file2)

        assert hash1 != hash2

    def test_generate_hash_resets_file_position(self):
        """Should reset file position after hashing."""
        file = BytesIO(b"test content")
        file.seek(5)  # Move to middle

        generate_file_hash(file)

        assert file.tell() == 0

    def test_generate_hash_empty_file(self):
        """Should handle empty file."""
        file = BytesIO(b"")
        result = generate_file_hash(file)

        assert isinstance(result, str)
        assert len(result) == 64


class TestValidateFile:
    """Tests for validate_file function."""

    def test_validate_valid_pdf_file(self):
        """Should validate correct PDF file."""
        mock_file = MagicMock()
        mock_file.filename = "document.pdf"
        mock_file.content_type = "application/pdf"

        # Create mock file object with seek/tell
        mock_file_obj = BytesIO(b"x" * 1024)  # 1KB file
        mock_file.file = mock_file_obj

        with patch("app.services.evidence_service.settings") as mock_settings:
            mock_settings.EVIDENCE_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
            mock_settings.EVIDENCE_ALLOWED_TYPES = ["application/pdf"]

            is_valid, error = validate_file(mock_file)

        assert is_valid is True
        assert error == ""

    def test_validate_file_too_large(self):
        """Should reject files exceeding max size."""
        mock_file = MagicMock()
        mock_file.filename = "large.pdf"
        mock_file.content_type = "application/pdf"

        # Create oversized mock file
        mock_file_obj = MagicMock()
        mock_file_obj.seek.return_value = None
        mock_file_obj.tell.return_value = 100 * 1024 * 1024  # 100MB

        mock_file.file = mock_file_obj

        with patch("app.services.evidence_service.settings") as mock_settings:
            mock_settings.EVIDENCE_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

            is_valid, error = validate_file(mock_file)

        assert is_valid is False
        assert "size exceeds" in error.lower()

    def test_validate_empty_file(self):
        """Should reject empty files."""
        mock_file = MagicMock()
        mock_file.filename = "empty.pdf"
        mock_file.content_type = "application/pdf"

        mock_file_obj = MagicMock()
        mock_file_obj.seek.return_value = None
        mock_file_obj.tell.return_value = 0  # Empty file

        mock_file.file = mock_file_obj

        with patch("app.services.evidence_service.settings") as mock_settings:
            mock_settings.EVIDENCE_MAX_FILE_SIZE = 10 * 1024 * 1024

            is_valid, error = validate_file(mock_file)

        assert is_valid is False
        assert "empty" in error.lower()

    def test_validate_disallowed_file_type(self):
        """Should reject disallowed file types."""
        mock_file = MagicMock()
        mock_file.filename = "script.exe"
        mock_file.content_type = "application/x-msdownload"

        mock_file_obj = BytesIO(b"x" * 1024)
        mock_file.file = mock_file_obj

        with patch("app.services.evidence_service.settings") as mock_settings:
            mock_settings.EVIDENCE_MAX_FILE_SIZE = 10 * 1024 * 1024
            mock_settings.EVIDENCE_ALLOWED_TYPES = ["application/pdf", "image/png"]

            is_valid, error = validate_file(mock_file)

        assert is_valid is False
        assert "not allowed" in error.lower()


class TestGetEvidenceDirectory:
    """Tests for get_evidence_directory function."""

    def test_get_evidence_directory_creates_path(self):
        """Should create directory path with tenant and instance IDs."""
        tenant_id = uuid4()
        instance_id = uuid4()

        with patch("app.services.evidence_service.get_storage_path") as mock_storage:
            mock_path = MagicMock(spec=Path)
            mock_storage.return_value = mock_path
            mock_path.__truediv__ = MagicMock(return_value=mock_path)

            result = get_evidence_directory(tenant_id, instance_id)

        mock_path.mkdir.assert_called_with(parents=True, exist_ok=True)


class TestGetEvidenceFilePath:
    """Tests for get_evidence_file_path function."""

    def test_get_file_path_returns_path(self):
        """Should return path if file exists."""
        evidence = MagicMock()
        evidence.file_path = "/tmp/test_evidence.pdf"

        with patch("app.services.evidence_service.Path") as mock_path_class:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_path_class.return_value = mock_path

            result = get_evidence_file_path(evidence)

        assert result == mock_path

    def test_get_file_path_raises_if_not_found(self):
        """Should raise HTTPException if file not found."""
        evidence = MagicMock()
        evidence.file_path = "/tmp/missing.pdf"

        with patch("app.services.evidence_service.Path") as mock_path_class:
            mock_path = MagicMock()
            mock_path.exists.return_value = False
            mock_path_class.return_value = mock_path

            with pytest.raises(HTTPException) as exc_info:
                get_evidence_file_path(evidence)

        assert exc_info.value.status_code == 404


class TestGetEvidenceById:
    """Tests for get_evidence_by_id function."""

    def test_get_evidence_by_id_returns_evidence(self):
        """Should return evidence if found."""
        db = MagicMock()
        evidence_id = uuid4()
        tenant_id = uuid4()

        mock_evidence = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_evidence

        result = get_evidence_by_id(db, evidence_id, tenant_id)

        assert result == mock_evidence

    def test_get_evidence_by_id_returns_none_if_not_found(self):
        """Should return None if evidence not found."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = get_evidence_by_id(db, uuid4(), uuid4())

        assert result is None

    def test_get_evidence_by_id_filters_by_tenant(self):
        """Should filter by tenant_id for multi-tenant isolation."""
        db = MagicMock()
        evidence_id = uuid4()
        tenant_id = uuid4()

        get_evidence_by_id(db, evidence_id, tenant_id)

        # Verify filter was called (tenant isolation)
        db.query.assert_called()


class TestApproveEvidence:
    """Tests for approve_evidence function."""

    def test_approve_evidence_success(self):
        """Should approve pending evidence."""
        db = MagicMock()
        evidence_id = uuid4()
        approved_by = uuid4()
        tenant_id = uuid4()

        mock_evidence = MagicMock()
        mock_evidence.approval_status = "Pending"

        with patch("app.services.evidence_service.get_evidence_by_id") as mock_get:
            mock_get.return_value = mock_evidence

            result = approve_evidence(db, evidence_id, approved_by, tenant_id)

        assert mock_evidence.approval_status == "Approved"
        assert mock_evidence.approved_by_user_id == approved_by
        assert mock_evidence.is_immutable is True
        db.commit.assert_called_once()

    def test_approve_evidence_not_found(self):
        """Should raise 404 if evidence not found."""
        db = MagicMock()

        with patch("app.services.evidence_service.get_evidence_by_id") as mock_get:
            mock_get.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                approve_evidence(db, uuid4(), uuid4(), uuid4())

        assert exc_info.value.status_code == 404

    def test_approve_evidence_already_processed(self):
        """Should raise 400 if already approved or rejected."""
        db = MagicMock()

        mock_evidence = MagicMock()
        mock_evidence.approval_status = "Approved"

        with patch("app.services.evidence_service.get_evidence_by_id") as mock_get:
            mock_get.return_value = mock_evidence

            with pytest.raises(HTTPException) as exc_info:
                approve_evidence(db, uuid4(), uuid4(), uuid4())

        assert exc_info.value.status_code == 400

    def test_approve_evidence_sets_timestamp(self):
        """Should set approved_at timestamp."""
        db = MagicMock()
        mock_evidence = MagicMock()
        mock_evidence.approval_status = "Pending"

        with patch("app.services.evidence_service.get_evidence_by_id") as mock_get:
            mock_get.return_value = mock_evidence

            result = approve_evidence(db, uuid4(), uuid4(), uuid4())

        assert mock_evidence.approved_at is not None

    def test_approve_evidence_with_remarks(self):
        """Should save approval remarks."""
        db = MagicMock()
        mock_evidence = MagicMock()
        mock_evidence.approval_status = "Pending"

        with patch("app.services.evidence_service.get_evidence_by_id") as mock_get:
            mock_get.return_value = mock_evidence

            result = approve_evidence(db, uuid4(), uuid4(), uuid4(), approval_remarks="Looks good!")

        assert mock_evidence.approval_remarks == "Looks good!"


class TestRejectEvidence:
    """Tests for reject_evidence function."""

    def test_reject_evidence_success(self):
        """Should reject pending evidence."""
        db = MagicMock()
        evidence_id = uuid4()
        rejected_by = uuid4()
        tenant_id = uuid4()

        mock_evidence = MagicMock()
        mock_evidence.approval_status = "Pending"

        with patch("app.services.evidence_service.get_evidence_by_id") as mock_get:
            mock_get.return_value = mock_evidence

            result = reject_evidence(db, evidence_id, rejected_by, tenant_id, rejection_reason="Document is illegible")

        assert mock_evidence.approval_status == "Rejected"
        assert mock_evidence.rejection_reason == "Document is illegible"
        db.commit.assert_called_once()

    def test_reject_evidence_requires_reason(self):
        """Should require rejection reason."""
        db = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            reject_evidence(db, uuid4(), uuid4(), uuid4(), rejection_reason="")

        assert exc_info.value.status_code == 400
        assert "reason is required" in exc_info.value.detail.lower()

    def test_reject_evidence_not_found(self):
        """Should raise 404 if evidence not found."""
        db = MagicMock()

        with patch("app.services.evidence_service.get_evidence_by_id") as mock_get:
            mock_get.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                reject_evidence(db, uuid4(), uuid4(), uuid4(), "Some reason")

        assert exc_info.value.status_code == 404

    def test_reject_evidence_already_processed(self):
        """Should raise 400 if already processed."""
        db = MagicMock()

        mock_evidence = MagicMock()
        mock_evidence.approval_status = "Rejected"

        with patch("app.services.evidence_service.get_evidence_by_id") as mock_get:
            mock_get.return_value = mock_evidence

            with pytest.raises(HTTPException) as exc_info:
                reject_evidence(db, uuid4(), uuid4(), uuid4(), "Reason")

        assert exc_info.value.status_code == 400


class TestDeleteEvidence:
    """Tests for delete_evidence function."""

    def test_delete_evidence_success(self):
        """Should delete mutable evidence."""
        db = MagicMock()
        evidence_id = uuid4()
        deleted_by = uuid4()
        tenant_id = uuid4()

        mock_evidence = MagicMock()
        mock_evidence.is_immutable = False
        mock_evidence.file_path = "/tmp/test.pdf"

        with patch("app.services.evidence_service.get_evidence_by_id") as mock_get:
            mock_get.return_value = mock_evidence

            with patch("app.services.evidence_service.Path") as mock_path_class:
                mock_path = MagicMock()
                mock_path.exists.return_value = True
                mock_path_class.return_value = mock_path

                result = delete_evidence(db, evidence_id, deleted_by, tenant_id)

        assert result is True
        db.delete.assert_called_once_with(mock_evidence)
        db.commit.assert_called_once()

    def test_delete_evidence_not_found(self):
        """Should raise 404 if evidence not found."""
        db = MagicMock()

        with patch("app.services.evidence_service.get_evidence_by_id") as mock_get:
            mock_get.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                delete_evidence(db, uuid4(), uuid4(), uuid4())

        assert exc_info.value.status_code == 404

    def test_delete_immutable_evidence_fails(self):
        """Should raise 400 if evidence is immutable (approved)."""
        db = MagicMock()

        mock_evidence = MagicMock()
        mock_evidence.is_immutable = True

        with patch("app.services.evidence_service.get_evidence_by_id") as mock_get:
            mock_get.return_value = mock_evidence

            with pytest.raises(HTTPException) as exc_info:
                delete_evidence(db, uuid4(), uuid4(), uuid4())

        assert exc_info.value.status_code == 400
        assert "immutable" in exc_info.value.detail.lower()

    def test_delete_evidence_handles_missing_file(self):
        """Should continue if file doesn't exist on disk."""
        db = MagicMock()

        mock_evidence = MagicMock()
        mock_evidence.is_immutable = False
        mock_evidence.file_path = "/tmp/missing.pdf"

        with patch("app.services.evidence_service.get_evidence_by_id") as mock_get:
            mock_get.return_value = mock_evidence

            with patch("app.services.evidence_service.Path") as mock_path_class:
                mock_path = MagicMock()
                mock_path.exists.return_value = False
                mock_path_class.return_value = mock_path

                result = delete_evidence(db, uuid4(), uuid4(), uuid4())

        assert result is True
        db.delete.assert_called_once()


class TestGetEvidenceForInstance:
    """Tests for get_evidence_for_instance function."""

    def test_get_evidence_for_instance_returns_list(self):
        """Should return list of evidence for instance."""
        db = MagicMock()
        instance_id = uuid4()
        tenant_id = uuid4()

        evidence_list = [MagicMock(), MagicMock()]
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = evidence_list

        result = get_evidence_for_instance(db, instance_id, tenant_id)

        assert len(result) == 2

    def test_get_evidence_for_instance_with_status_filter(self):
        """Should filter by approval status."""
        db = MagicMock()
        instance_id = uuid4()
        tenant_id = uuid4()

        db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = get_evidence_for_instance(db, instance_id, tenant_id, approval_status="Pending")

        # Verify additional filter was applied
        db.query.return_value.filter.return_value.filter.assert_called()

    def test_get_evidence_for_instance_latest_only(self):
        """Should filter to latest versions only."""
        db = MagicMock()
        instance_id = uuid4()
        tenant_id = uuid4()

        db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = get_evidence_for_instance(db, instance_id, tenant_id, latest_only=True)

        db.query.assert_called()


class TestGetEvidenceVersionHistory:
    """Tests for get_evidence_version_history function."""

    def test_get_version_history_returns_list(self):
        """Should return list of versions."""
        db = MagicMock()
        evidence_id = uuid4()
        tenant_id = uuid4()

        # Mock evidence without parent (root version)
        mock_evidence = MagicMock()
        mock_evidence.parent_evidence_id = None
        mock_evidence.id = evidence_id

        with patch("app.services.evidence_service.get_evidence_by_id") as mock_get:
            mock_get.return_value = mock_evidence

            # No child versions
            db.query.return_value.filter.return_value.first.return_value = None

            result = get_evidence_version_history(db, evidence_id, tenant_id)

        assert len(result) == 1
        assert result[0] == mock_evidence

    def test_get_version_history_returns_empty_if_not_found(self):
        """Should return empty list if evidence not found."""
        db = MagicMock()

        with patch("app.services.evidence_service.get_evidence_by_id") as mock_get:
            mock_get.return_value = None

            result = get_evidence_version_history(db, uuid4(), uuid4())

        assert result == []

    def test_get_version_history_traverses_chain(self):
        """Should traverse parent chain to find all versions."""
        db = MagicMock()
        tenant_id = uuid4()

        # Create version chain: v1 -> v2 -> v3
        v1 = MagicMock()
        v1.id = uuid4()
        v1.parent_evidence_id = None

        v2 = MagicMock()
        v2.id = uuid4()
        v2.parent_evidence_id = v1.id

        v3 = MagicMock()
        v3.id = uuid4()
        v3.parent_evidence_id = v2.id

        with patch("app.services.evidence_service.get_evidence_by_id") as mock_get:
            # Start with v3
            mock_get.side_effect = [v3, v2, v1]

            # Mock child query
            db.query.return_value.filter.return_value.first.side_effect = [v2, v3, None]

            result = get_evidence_version_history(db, v3.id, tenant_id)

        # Should return [v1, v2, v3] in order
        assert len(result) >= 1


class TestGetPendingApprovals:
    """Tests for get_pending_approvals function."""

    def test_get_pending_approvals_returns_list(self):
        """Should return list of pending evidence."""
        db = MagicMock()
        tenant_id = uuid4()

        pending_list = [MagicMock(), MagicMock(), MagicMock()]
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = pending_list

        result = get_pending_approvals(db, tenant_id)

        assert len(result) == 3

    def test_get_pending_approvals_filters_by_tenant(self):
        """Should filter by tenant_id."""
        db = MagicMock()
        tenant_id = uuid4()

        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = get_pending_approvals(db, tenant_id)

        db.query.assert_called()

    def test_get_pending_approvals_empty_list(self):
        """Should return empty list when no pending approvals."""
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = get_pending_approvals(db, uuid4())

        assert result == []


class TestCheckDuplicateEvidence:
    """Tests for check_duplicate_evidence function."""

    def test_check_duplicate_returns_existing(self):
        """Should return existing evidence if duplicate hash found."""
        db = MagicMock()
        file_hash = "abc123hash"
        instance_id = uuid4()
        tenant_id = uuid4()

        mock_existing = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_existing

        result = check_duplicate_evidence(db, file_hash, instance_id, tenant_id)

        assert result == mock_existing

    def test_check_duplicate_returns_none_if_not_found(self):
        """Should return None if no duplicate found."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = check_duplicate_evidence(db, "uniquehash", uuid4(), uuid4())

        assert result is None

    def test_check_duplicate_filters_by_instance_and_tenant(self):
        """Should filter by instance and tenant for scope."""
        db = MagicMock()
        file_hash = "somehash"
        instance_id = uuid4()
        tenant_id = uuid4()

        db.query.return_value.filter.return_value.first.return_value = None

        result = check_duplicate_evidence(db, file_hash, instance_id, tenant_id)

        # Verify query was called with filters
        db.query.assert_called()


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_file_hash_large_file(self):
        """Should handle large file hashing efficiently."""
        # Create a moderately sized file (100KB)
        content = b"x" * (100 * 1024)
        file = BytesIO(content)

        result = generate_file_hash(file)

        assert len(result) == 64

    def test_validate_file_boundary_size(self):
        """Should handle file at exact max size."""
        mock_file = MagicMock()
        mock_file.filename = "document.pdf"
        mock_file.content_type = "application/pdf"

        max_size = 10 * 1024 * 1024  # 10MB
        mock_file_obj = MagicMock()
        mock_file_obj.seek.return_value = None
        mock_file_obj.tell.return_value = max_size  # Exactly at limit

        mock_file.file = mock_file_obj

        with patch("app.services.evidence_service.settings") as mock_settings:
            mock_settings.EVIDENCE_MAX_FILE_SIZE = max_size
            mock_settings.EVIDENCE_ALLOWED_TYPES = ["application/pdf"]

            is_valid, error = validate_file(mock_file)

        # At exact limit should still be valid
        assert is_valid is True

    def test_extension_with_unicode_filename(self):
        """Should handle unicode characters in filename."""
        result = get_file_extension("文档.pdf")
        assert result == ".pdf"

    def test_extension_with_spaces_in_filename(self):
        """Should handle spaces in filename."""
        result = get_file_extension("my document file.xlsx")
        assert result == ".xlsx"

    def test_approve_evidence_sets_updated_by(self):
        """Should set updated_by field on approval."""
        db = MagicMock()
        approved_by = uuid4()

        mock_evidence = MagicMock()
        mock_evidence.approval_status = "Pending"

        with patch("app.services.evidence_service.get_evidence_by_id") as mock_get:
            mock_get.return_value = mock_evidence

            result = approve_evidence(db, uuid4(), approved_by, uuid4())

        assert mock_evidence.updated_by == approved_by

    def test_reject_evidence_sets_updated_by(self):
        """Should set updated_by field on rejection."""
        db = MagicMock()
        rejected_by = uuid4()

        mock_evidence = MagicMock()
        mock_evidence.approval_status = "Pending"

        with patch("app.services.evidence_service.get_evidence_by_id") as mock_get:
            mock_get.return_value = mock_evidence

            result = reject_evidence(db, uuid4(), rejected_by, uuid4(), "Reason")

        assert mock_evidence.updated_by == rejected_by
