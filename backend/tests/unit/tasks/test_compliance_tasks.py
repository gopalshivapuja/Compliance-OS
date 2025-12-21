"""
Unit tests for compliance background tasks.

Tests cover:
- Daily instance generation
- RAG status recalculation
- Quarterly instance generation
- Annual instance generation
- Overdue status updates
"""

import pytest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock
from uuid import uuid4

from app.models import Tenant, ComplianceInstance, ComplianceMaster, Entity


class TestGenerateComplianceInstancesDaily:
    """Tests for generate_compliance_instances_daily task."""

    @patch("app.tasks.compliance_tasks.SessionLocal")
    @patch("app.tasks.compliance_tasks.generate_instances_for_period")
    @patch("app.tasks.compliance_tasks.calculate_period_for_frequency")
    def test_generates_instances_for_all_tenants(self, mock_calc_period, mock_generate, mock_session):
        """Test that instances are generated for all active tenants."""
        from app.tasks.compliance_tasks import generate_compliance_instances_daily

        # Setup mock tenants
        tenant1 = MagicMock(spec=Tenant)
        tenant1.id = uuid4()
        tenant1.tenant_name = "Tenant 1"
        tenant1.status = "active"

        tenant2 = MagicMock(spec=Tenant)
        tenant2.id = uuid4()
        tenant2.tenant_name = "Tenant 2"
        tenant2.status = "active"

        # Mock database session
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [tenant1, tenant2]
        mock_session.return_value = mock_db

        # Mock period calculation
        mock_calc_period.return_value = (date(2025, 12, 1), date(2025, 12, 31))

        # Mock instance generation
        mock_generate.return_value = [MagicMock(), MagicMock()]

        # Execute task
        result = generate_compliance_instances_daily()

        # Verify
        assert result["status"] == "success"
        assert result["total_created"] == 4  # 2 tenants x 2 instances each
        assert len(result["tenants"]) == 2
        assert mock_generate.call_count == 2

    @patch("app.tasks.compliance_tasks.SessionLocal")
    def test_skips_when_no_active_tenants(self, mock_session):
        """Test task handles no active tenants gracefully."""
        from app.tasks.compliance_tasks import generate_compliance_instances_daily

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_session.return_value = mock_db

        result = generate_compliance_instances_daily()

        assert result["status"] == "no_tenants"
        assert result["created"] == 0

    @patch("app.tasks.compliance_tasks.SessionLocal")
    @patch("app.tasks.compliance_tasks.generate_instances_for_period")
    @patch("app.tasks.compliance_tasks.calculate_period_for_frequency")
    def test_handles_tenant_error_gracefully(self, mock_calc_period, mock_generate, mock_session):
        """Test task continues when one tenant fails."""
        from app.tasks.compliance_tasks import generate_compliance_instances_daily

        tenant1 = MagicMock(spec=Tenant)
        tenant1.id = uuid4()
        tenant1.tenant_name = "Tenant 1"

        tenant2 = MagicMock(spec=Tenant)
        tenant2.id = uuid4()
        tenant2.tenant_name = "Tenant 2"

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [tenant1, tenant2]
        mock_session.return_value = mock_db

        mock_calc_period.return_value = (date(2025, 12, 1), date(2025, 12, 31))

        # First tenant fails, second succeeds
        mock_generate.side_effect = [Exception("DB Error"), [MagicMock()]]

        result = generate_compliance_instances_daily()

        assert result["status"] == "success"
        assert result["total_created"] == 1
        assert "error" in result["tenants"][str(tenant1.id)]
        assert result["tenants"][str(tenant2.id)]["instances_created"] == 1


class TestRecalculateRagStatusHourly:
    """Tests for recalculate_rag_status_hourly task."""

    @patch("app.tasks.compliance_tasks.invalidate_dashboard_cache")
    @patch("app.tasks.compliance_tasks.SessionLocal")
    @patch("app.tasks.compliance_tasks.recalculate_rag_for_tenant")
    def test_recalculates_rag_for_all_tenants(self, mock_recalc, mock_session, mock_invalidate):
        """Test that RAG is recalculated for all active tenants."""
        from app.tasks.compliance_tasks import recalculate_rag_status_hourly

        tenant1 = MagicMock(spec=Tenant)
        tenant1.id = uuid4()
        tenant1.tenant_name = "Tenant 1"

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [tenant1]
        mock_session.return_value = mock_db

        mock_recalc.return_value = 10

        result = recalculate_rag_status_hourly()

        assert result["status"] == "success"
        assert result["total_updated"] == 10
        mock_invalidate.assert_called_once()

    @patch("app.tasks.compliance_tasks.invalidate_dashboard_cache")
    @patch("app.tasks.compliance_tasks.SessionLocal")
    @patch("app.tasks.compliance_tasks.recalculate_rag_for_tenant")
    def test_handles_redis_failure_gracefully(self, mock_recalc, mock_session, mock_invalidate):
        """Test task continues when Redis cache invalidation fails."""
        from app.tasks.compliance_tasks import recalculate_rag_status_hourly

        tenant = MagicMock(spec=Tenant)
        tenant.id = uuid4()
        tenant.tenant_name = "Tenant"

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [tenant]
        mock_session.return_value = mock_db

        mock_recalc.return_value = 5
        mock_invalidate.side_effect = Exception("Redis down")

        result = recalculate_rag_status_hourly()

        assert result["status"] == "success"
        assert result["total_updated"] == 5

    @patch("app.tasks.compliance_tasks.SessionLocal")
    def test_returns_no_tenants_when_empty(self, mock_session):
        """Test task handles no tenants case."""
        from app.tasks.compliance_tasks import recalculate_rag_status_hourly

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_session.return_value = mock_db

        result = recalculate_rag_status_hourly()

        assert result["status"] == "no_tenants"
        assert result["updated"] == 0


class TestGenerateQuarterlyInstances:
    """Tests for generate_quarterly_instances task."""

    @patch("app.tasks.compliance_tasks.SessionLocal")
    @patch("app.tasks.compliance_tasks.generate_instances_for_period")
    @patch("app.tasks.compliance_tasks.calculate_period_for_frequency")
    def test_generates_quarterly_instances(self, mock_calc_period, mock_generate, mock_session):
        """Test quarterly instance generation filters correctly."""
        from app.tasks.compliance_tasks import generate_quarterly_instances

        tenant = MagicMock(spec=Tenant)
        tenant.id = uuid4()
        tenant.tenant_name = "Tenant"

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [tenant]
        mock_session.return_value = mock_db

        # Q1 period (Apr-Jun)
        mock_calc_period.return_value = (date(2025, 4, 1), date(2025, 6, 30))

        # Create mock instances with different frequencies
        quarterly_instance = MagicMock()
        quarterly_master = MagicMock(frequency="Quarterly")
        quarterly_instance.compliance_master = quarterly_master

        monthly_instance = MagicMock()
        monthly_master = MagicMock(frequency="Monthly")
        monthly_instance.compliance_master = monthly_master

        mock_generate.return_value = [quarterly_instance, monthly_instance]

        result = generate_quarterly_instances()

        assert result["status"] == "success"
        # Should only count the quarterly instance
        assert result["tenants"][str(tenant.id)]["quarterly_instances"] == 1


class TestGenerateAnnualInstances:
    """Tests for generate_annual_instances task."""

    @patch("app.tasks.compliance_tasks.SessionLocal")
    @patch("app.tasks.compliance_tasks.generate_instances_for_period")
    @patch("app.tasks.compliance_tasks.calculate_period_for_frequency")
    def test_generates_annual_instances_on_april_1(self, mock_calc_period, mock_generate, mock_session):
        """Test annual instance generation for India FY."""
        from app.tasks.compliance_tasks import generate_annual_instances

        tenant = MagicMock(spec=Tenant)
        tenant.id = uuid4()
        tenant.tenant_name = "Tenant"

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [tenant]
        mock_session.return_value = mock_db

        # FY 2025-26 period
        mock_calc_period.return_value = (date(2025, 4, 1), date(2026, 3, 31))

        # Create mock annual instance
        annual_instance = MagicMock()
        annual_master = MagicMock(frequency="Annual")
        annual_instance.compliance_master = annual_master

        mock_generate.return_value = [annual_instance]

        result = generate_annual_instances()

        assert result["status"] == "success"
        assert result["tenants"][str(tenant.id)]["annual_instances"] == 1
        assert (
            "FY" in result["tenants"][str(tenant.id)]["period"]
            or "2025-04-01" in result["tenants"][str(tenant.id)]["period"]
        )

    @patch("app.tasks.compliance_tasks.SessionLocal")
    @patch("app.tasks.compliance_tasks.generate_instances_for_period")
    @patch("app.tasks.compliance_tasks.calculate_period_for_frequency")
    def test_filters_annual_frequency_only(self, mock_calc_period, mock_generate, mock_session):
        """Test that only annual frequency instances are counted."""
        from app.tasks.compliance_tasks import generate_annual_instances

        tenant = MagicMock(spec=Tenant)
        tenant.id = uuid4()
        tenant.tenant_name = "Tenant"

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [tenant]
        mock_session.return_value = mock_db

        mock_calc_period.return_value = (date(2025, 4, 1), date(2026, 3, 31))

        # Mix of frequencies
        annual_instance = MagicMock()
        annual_instance.compliance_master = MagicMock(frequency="Annual")

        monthly_instance = MagicMock()
        monthly_instance.compliance_master = MagicMock(frequency="Monthly")

        quarterly_instance = MagicMock()
        quarterly_instance.compliance_master = MagicMock(frequency="Quarterly")

        mock_generate.return_value = [annual_instance, monthly_instance, quarterly_instance]

        result = generate_annual_instances()

        assert result["tenants"][str(tenant.id)]["annual_instances"] == 1


class TestUpdateOverdueStatus:
    """Tests for update_overdue_status task."""

    @patch("app.tasks.compliance_tasks.SessionLocal")
    def test_marks_past_due_as_overdue(self, mock_session):
        """Test instances past due are marked as overdue."""
        from app.tasks.compliance_tasks import update_overdue_status

        mock_db = MagicMock()

        # Create overdue instance
        overdue_instance = MagicMock(spec=ComplianceInstance)
        overdue_instance.due_date = date.today() - timedelta(days=5)
        overdue_instance.status = "In Progress"
        overdue_instance.rag_status = "Amber"

        mock_db.query.return_value.filter.return_value.all.return_value = [overdue_instance]
        mock_session.return_value = mock_db

        result = update_overdue_status()

        assert result["status"] == "success"
        assert result["overdue_count"] == 1
        assert overdue_instance.status == "Overdue"
        assert overdue_instance.rag_status == "Red"
        mock_db.commit.assert_called_once()

    @patch("app.tasks.compliance_tasks.SessionLocal")
    def test_skips_completed_instances(self, mock_session):
        """Test completed instances are not marked overdue."""
        from app.tasks.compliance_tasks import update_overdue_status

        mock_db = MagicMock()
        # Query returns no instances (filter excludes Completed)
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_session.return_value = mock_db

        result = update_overdue_status()

        assert result["status"] == "success"
        assert result["overdue_count"] == 0

    @patch("app.tasks.compliance_tasks.SessionLocal")
    def test_handles_multiple_overdue_instances(self, mock_session):
        """Test multiple instances are updated correctly."""
        from app.tasks.compliance_tasks import update_overdue_status

        mock_db = MagicMock()

        instances = []
        for i in range(5):
            instance = MagicMock(spec=ComplianceInstance)
            instance.due_date = date.today() - timedelta(days=i + 1)
            instance.status = "In Progress"
            instance.rag_status = "Amber"
            instances.append(instance)

        mock_db.query.return_value.filter.return_value.all.return_value = instances
        mock_session.return_value = mock_db

        result = update_overdue_status()

        assert result["status"] == "success"
        assert result["overdue_count"] == 5
        for instance in instances:
            assert instance.status == "Overdue"
            assert instance.rag_status == "Red"

    @patch("app.tasks.compliance_tasks.SessionLocal")
    def test_handles_database_error(self, mock_session):
        """Test task handles database errors gracefully."""
        from app.tasks.compliance_tasks import update_overdue_status

        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("Database connection failed")
        mock_session.return_value = mock_db

        result = update_overdue_status()

        assert result["status"] == "error"
        assert "Database connection failed" in result["message"]
        mock_db.rollback.assert_called_once()


class TestInvalidateDashboardCache:
    """Tests for invalidate_dashboard_cache helper."""

    @patch("app.core.redis.redis_client")
    def test_deletes_dashboard_cache_keys(self, mock_redis):
        """Test that dashboard cache keys are deleted."""
        from app.tasks.compliance_tasks import invalidate_dashboard_cache

        # Mock scan returning some keys then stopping
        mock_redis.scan.side_effect = [
            (100, [b"dashboard:tenant1", b"dashboard:tenant2"]),
            (0, [b"dashboard:tenant3"]),
        ]

        invalidate_dashboard_cache()

        assert mock_redis.delete.call_count == 2
        mock_redis.delete.assert_any_call(b"dashboard:tenant1", b"dashboard:tenant2")
        mock_redis.delete.assert_any_call(b"dashboard:tenant3")

    @patch("app.core.redis.redis_client")
    def test_handles_redis_error(self, mock_redis):
        """Test cache invalidation handles Redis errors."""
        from app.tasks.compliance_tasks import invalidate_dashboard_cache

        mock_redis.scan.side_effect = Exception("Redis unavailable")

        # Should not raise, just log warning
        invalidate_dashboard_cache()  # No exception raised
