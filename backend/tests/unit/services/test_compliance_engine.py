"""
Compliance Engine Unit Tests

Tests for instance generation, due date calculation, and RAG status.
Phase 4 implementation.

Test Categories:
- Due Date Calculation: Rule-based due date computation
- Period Calculation: Monthly, quarterly, annual period boundaries
- RAG Status: Green/Amber/Red status calculation
- Dependency Resolution: Handling compliance dependencies
"""

from datetime import date, timedelta
from unittest.mock import MagicMock

from app.services.compliance_engine import (
    calculate_due_date,
    calculate_period_for_frequency,
    calculate_rag_status,
    check_dependencies_met,
    get_india_fy_quarter,
    get_quarter_end_date,
)


class TestDueDateCalculation:
    """Tests for due date calculation rules."""

    def test_monthly_due_date_on_specific_day(self):
        """Due date should fall on specified day of next month."""
        rule = {"type": "monthly", "day": 11, "offset_days": 0}
        period_end = date(2024, 3, 31)  # March 2024

        result = calculate_due_date(rule, period_end)

        assert result == date(2024, 4, 11)  # April 11

    def test_monthly_due_date_with_offset(self):
        """Due date should include offset days."""
        rule = {"type": "monthly", "day": 11, "offset_days": 5}
        period_end = date(2024, 3, 31)

        result = calculate_due_date(rule, period_end)

        assert result == date(2024, 4, 16)  # April 11 + 5 days

    def test_monthly_due_date_first_of_month(self):
        """Due date on first day of next month."""
        rule = {"type": "monthly", "day": 1, "offset_days": 0}
        period_end = date(2024, 1, 31)

        result = calculate_due_date(rule, period_end)

        assert result == date(2024, 2, 1)

    def test_monthly_due_date_day_31_in_short_month(self):
        """Day 31 in February should adjust to last day of month."""
        rule = {"type": "monthly", "day": 31, "offset_days": 0}
        period_end = date(2024, 1, 31)  # Next month is Feb (leap year)

        result = calculate_due_date(rule, period_end)

        assert result == date(2024, 2, 29)  # Last day of Feb in leap year

    def test_monthly_due_date_day_30_in_february(self):
        """Day 30 in February should adjust to last day."""
        rule = {"type": "monthly", "day": 30, "offset_days": 0}
        period_end = date(2023, 1, 31)  # Next month is Feb (non-leap year)

        result = calculate_due_date(rule, period_end)

        assert result == date(2023, 2, 28)

    def test_quarterly_due_date_with_offset(self):
        """Quarterly due date should be offset days after quarter end."""
        rule = {"type": "quarterly", "offset_days": 31}
        period_end = date(2024, 6, 30)  # Q1 India FY

        result = calculate_due_date(rule, period_end)

        assert result == date(2024, 7, 31)  # 31 days after June 30

    def test_quarterly_due_date_no_offset(self):
        """Quarterly due date with no offset returns quarter end."""
        rule = {"type": "quarterly", "offset_days": 0}
        period_end = date(2024, 9, 30)  # Q2 India FY

        result = calculate_due_date(rule, period_end)

        assert result == date(2024, 9, 30)

    def test_annual_due_date_specific_month_day(self):
        """Annual due date on specific month and day."""
        rule = {"type": "annual", "month": 9, "day": 30, "offset_days": 0}
        period_end = date(2024, 3, 31)  # FY end (FY 2023-24)

        result = calculate_due_date(rule, period_end)

        # FY year is 2023 for Mar 2024, month 9 >= 4 so year = 2023
        assert result == date(2023, 9, 30)

    def test_annual_due_date_with_offset(self):
        """Annual due date with offset days."""
        rule = {"type": "annual", "month": 7, "day": 31, "offset_days": 15}
        period_end = date(2024, 3, 31)

        result = calculate_due_date(rule, period_end)

        # FY year is 2023 for Mar 2024, month 7 >= 4 so year = 2023
        assert result == date(2023, 8, 15)  # July 31, 2023 + 15 days

    def test_fixed_date_rule(self):
        """Fixed date should return the same date every year."""
        rule = {"type": "fixed_date", "month": 6, "day": 15}
        period_end = date(2024, 3, 31)

        result = calculate_due_date(rule, period_end)

        assert result == date(2024, 6, 15)

    def test_event_based_rule_with_offset(self):
        """Event-based due date should be offset from period end."""
        rule = {"type": "event_based", "offset_days": 30}
        period_end = date(2024, 5, 15)  # Event date

        result = calculate_due_date(rule, period_end)

        assert result == date(2024, 6, 14)  # 30 days after event

    def test_unknown_rule_type_returns_period_end(self):
        """Unknown rule type should default to period end date."""
        rule = {"type": "unknown_type"}
        period_end = date(2024, 3, 31)

        result = calculate_due_date(rule, period_end)

        assert result == period_end

    def test_empty_rule_defaults_to_monthly(self):
        """Empty rule should default to monthly type (day 1)."""
        rule = {}
        period_end = date(2024, 3, 31)

        result = calculate_due_date(rule, period_end)

        # Empty rule defaults to monthly with day=1, offset=0
        assert result == date(2024, 4, 1)  # First day of next month


class TestPeriodCalculation:
    """Tests for period calculation based on frequency."""

    def test_monthly_period_january(self):
        """Monthly period for January."""
        target_date = date(2024, 1, 15)

        start, end = calculate_period_for_frequency("Monthly", target_date)

        assert start == date(2024, 1, 1)
        assert end == date(2024, 1, 31)

    def test_monthly_period_february_leap_year(self):
        """Monthly period for February in leap year."""
        target_date = date(2024, 2, 15)

        start, end = calculate_period_for_frequency("Monthly", target_date)

        assert start == date(2024, 2, 1)
        assert end == date(2024, 2, 29)

    def test_monthly_period_february_non_leap_year(self):
        """Monthly period for February in non-leap year."""
        target_date = date(2023, 2, 15)

        start, end = calculate_period_for_frequency("Monthly", target_date)

        assert start == date(2023, 2, 1)
        assert end == date(2023, 2, 28)

    def test_quarterly_period_q1_india_fy(self):
        """Q1 of India FY (Apr-Jun)."""
        target_date = date(2024, 5, 15)  # May

        start, end = calculate_period_for_frequency("Quarterly", target_date)

        assert start == date(2024, 4, 1)
        assert end == date(2024, 6, 30)

    def test_quarterly_period_q2_india_fy(self):
        """Q2 of India FY (Jul-Sep)."""
        target_date = date(2024, 8, 15)  # August

        start, end = calculate_period_for_frequency("Quarterly", target_date)

        assert start == date(2024, 7, 1)
        assert end == date(2024, 9, 30)

    def test_quarterly_period_q3_india_fy(self):
        """Q3 of India FY (Oct-Dec)."""
        target_date = date(2024, 11, 15)  # November

        start, end = calculate_period_for_frequency("Quarterly", target_date)

        assert start == date(2024, 10, 1)
        assert end == date(2024, 12, 31)

    def test_quarterly_period_q4_india_fy(self):
        """Q4 of India FY (Jan-Mar)."""
        target_date = date(2024, 2, 15)  # February

        start, end = calculate_period_for_frequency("Quarterly", target_date)

        assert start == date(2024, 1, 1)
        assert end == date(2024, 3, 31)

    def test_annual_period_india_fy_before_april(self):
        """Annual period for date before April (same FY year - 1)."""
        target_date = date(2024, 2, 15)  # Feb 2024 is in FY 2023-24

        start, end = calculate_period_for_frequency("Annual", target_date)

        assert start == date(2023, 4, 1)
        assert end == date(2024, 3, 31)

    def test_annual_period_india_fy_after_april(self):
        """Annual period for date after April (current FY)."""
        target_date = date(2024, 5, 15)  # May 2024 is in FY 2024-25

        start, end = calculate_period_for_frequency("Annual", target_date)

        assert start == date(2024, 4, 1)
        assert end == date(2025, 3, 31)

    def test_unknown_frequency_defaults_to_monthly(self):
        """Unknown frequency should default to monthly period."""
        target_date = date(2024, 5, 15)

        start, end = calculate_period_for_frequency("unknown", target_date)

        assert start == date(2024, 5, 1)
        assert end == date(2024, 5, 31)


class TestIndiaFYQuarter:
    """Tests for India Financial Year quarter calculation."""

    def test_april_is_q1(self):
        """April should be Q1 of India FY."""
        result = get_india_fy_quarter(date(2024, 4, 15))
        assert result == 1

    def test_june_is_q1(self):
        """June should be Q1 of India FY."""
        result = get_india_fy_quarter(date(2024, 6, 30))
        assert result == 1

    def test_july_is_q2(self):
        """July should be Q2 of India FY."""
        result = get_india_fy_quarter(date(2024, 7, 1))
        assert result == 2

    def test_september_is_q2(self):
        """September should be Q2 of India FY."""
        result = get_india_fy_quarter(date(2024, 9, 30))
        assert result == 2

    def test_october_is_q3(self):
        """October should be Q3 of India FY."""
        result = get_india_fy_quarter(date(2024, 10, 15))
        assert result == 3

    def test_december_is_q3(self):
        """December should be Q3 of India FY."""
        result = get_india_fy_quarter(date(2024, 12, 31))
        assert result == 3

    def test_january_is_q4(self):
        """January should be Q4 of India FY."""
        result = get_india_fy_quarter(date(2024, 1, 15))
        assert result == 4

    def test_march_is_q4(self):
        """March should be Q4 of India FY."""
        result = get_india_fy_quarter(date(2024, 3, 31))
        assert result == 4


class TestQuarterEndDate:
    """Tests for quarter end date calculation."""

    def test_q1_end_date(self):
        """Q1 ends on June 30."""
        # Date in Q1 (Apr-Jun)
        result = get_quarter_end_date(date(2024, 5, 15))
        assert result == date(2024, 6, 30)

    def test_q2_end_date(self):
        """Q2 ends on September 30."""
        # Date in Q2 (Jul-Sep)
        result = get_quarter_end_date(date(2024, 8, 15))
        assert result == date(2024, 9, 30)

    def test_q3_end_date(self):
        """Q3 ends on December 31."""
        # Date in Q3 (Oct-Dec)
        result = get_quarter_end_date(date(2024, 11, 15))
        assert result == date(2024, 12, 31)

    def test_q4_end_date(self):
        """Q4 ends on March 31."""
        # Date in Q4 (Jan-Mar)
        result = get_quarter_end_date(date(2024, 2, 15))
        assert result == date(2024, 3, 31)


class TestRAGStatusCalculation:
    """Tests for RAG (Red/Amber/Green) status calculation."""

    def _create_instance_mock(self, due_date, status, blocking_id=None):
        """Helper to create properly configured instance mock."""
        mock_instance = MagicMock()
        mock_instance.due_date = due_date
        mock_instance.status = status
        mock_instance.blocking_compliance_instance_id = blocking_id
        mock_instance.blocking_instance = None
        return mock_instance

    def test_green_status_more_than_7_days(self):
        """Status should be Green when > 7 days to due date."""
        mock_instance = self._create_instance_mock(due_date=date.today() + timedelta(days=14), status="Not Started")

        result = calculate_rag_status(mock_instance)

        assert result == "Green"

    def test_green_status_exactly_8_days(self):
        """Status should be Green when exactly 8 days to due date."""
        mock_instance = self._create_instance_mock(due_date=date.today() + timedelta(days=8), status="In Progress")

        result = calculate_rag_status(mock_instance)

        assert result == "Green"

    def test_amber_status_exactly_7_days(self):
        """Status should be Amber when exactly 7 days to due date."""
        mock_instance = self._create_instance_mock(due_date=date.today() + timedelta(days=7), status="Not Started")

        result = calculate_rag_status(mock_instance)

        assert result == "Amber"

    def test_amber_status_within_7_days(self):
        """Status should be Amber when < 7 days to due date."""
        mock_instance = self._create_instance_mock(due_date=date.today() + timedelta(days=5), status="In Progress")

        result = calculate_rag_status(mock_instance)

        assert result == "Amber"

    def test_amber_status_1_day_remaining(self):
        """Status should be Amber when 1 day remaining."""
        mock_instance = self._create_instance_mock(due_date=date.today() + timedelta(days=1), status="Not Started")

        result = calculate_rag_status(mock_instance)

        assert result == "Amber"

    def test_amber_status_due_today(self):
        """Status should be Amber when due today."""
        mock_instance = self._create_instance_mock(due_date=date.today(), status="In Progress")

        result = calculate_rag_status(mock_instance)

        assert result == "Amber"

    def test_red_status_overdue_1_day(self):
        """Status should be Red when 1 day overdue."""
        mock_instance = self._create_instance_mock(due_date=date.today() - timedelta(days=1), status="Not Started")

        result = calculate_rag_status(mock_instance)

        assert result == "Red"

    def test_red_status_overdue_many_days(self):
        """Status should be Red when many days overdue."""
        mock_instance = self._create_instance_mock(due_date=date.today() - timedelta(days=30), status="In Progress")

        result = calculate_rag_status(mock_instance)

        assert result == "Red"

    def test_green_status_when_completed(self):
        """Completed instances should be Green regardless of due date."""
        mock_instance = self._create_instance_mock(
            due_date=date.today() - timedelta(days=10), status="Completed"  # Overdue
        )

        result = calculate_rag_status(mock_instance)

        assert result == "Green"

    def test_rag_with_custom_today_date(self):
        """RAG calculation should respect custom today date."""
        mock_instance = self._create_instance_mock(due_date=date(2024, 6, 15), status="Not Started")

        # 10 days before due date
        custom_today = date(2024, 6, 5)
        result = calculate_rag_status(mock_instance, today=custom_today)

        assert result == "Green"

    def test_rag_custom_today_overdue(self):
        """RAG with custom today date showing overdue."""
        mock_instance = self._create_instance_mock(due_date=date(2024, 6, 15), status="Not Started")

        # 5 days after due date
        custom_today = date(2024, 6, 20)
        result = calculate_rag_status(mock_instance, today=custom_today)

        assert result == "Red"


class TestDependencyResolution:
    """Tests for compliance dependency handling."""

    def test_no_dependencies_returns_true(self):
        """Instance with no dependencies should pass check."""
        mock_db = MagicMock()
        mock_instance = MagicMock()
        mock_instance.blocking_compliance_instance_id = None
        mock_instance.blocking_instance = None
        mock_instance.compliance_master = MagicMock()
        mock_instance.compliance_master.dependencies = None

        met, blocking = check_dependencies_met(mock_db, mock_instance)

        assert met is True
        assert blocking == []

    def test_empty_dependencies_returns_true(self):
        """Instance with empty dependencies list should pass."""
        mock_db = MagicMock()
        mock_instance = MagicMock()
        mock_instance.blocking_compliance_instance_id = None
        mock_instance.blocking_instance = None
        mock_instance.compliance_master = MagicMock()
        mock_instance.compliance_master.dependencies = []

        met, blocking = check_dependencies_met(mock_db, mock_instance)

        assert met is True
        assert blocking == []

    def test_no_master_returns_true(self):
        """Instance without master should pass dependency check."""
        mock_db = MagicMock()
        mock_instance = MagicMock()
        mock_instance.blocking_compliance_instance_id = None
        mock_instance.blocking_instance = None
        mock_instance.compliance_master = None

        met, blocking = check_dependencies_met(mock_db, mock_instance)

        assert met is True
        assert blocking == []


class TestEdgeCases:
    """Edge case tests for compliance engine."""

    def test_calculate_due_date_year_boundary(self):
        """Due date calculation crossing year boundary."""
        rule = {"type": "monthly", "day": 15, "offset_days": 0}
        period_end = date(2024, 12, 31)  # December

        result = calculate_due_date(rule, period_end)

        assert result == date(2025, 1, 15)  # January next year

    def test_monthly_period_december(self):
        """Monthly period for December."""
        target_date = date(2024, 12, 15)

        start, end = calculate_period_for_frequency("Monthly", target_date)

        assert start == date(2024, 12, 1)
        assert end == date(2024, 12, 31)

    def test_annual_period_boundary_march_31(self):
        """Annual period on March 31 (FY end date)."""
        target_date = date(2024, 3, 31)

        start, end = calculate_period_for_frequency("Annual", target_date)

        assert start == date(2023, 4, 1)
        assert end == date(2024, 3, 31)

    def test_annual_period_boundary_april_1(self):
        """Annual period on April 1 (FY start date)."""
        target_date = date(2024, 4, 1)

        start, end = calculate_period_for_frequency("Annual", target_date)

        assert start == date(2024, 4, 1)
        assert end == date(2025, 3, 31)
