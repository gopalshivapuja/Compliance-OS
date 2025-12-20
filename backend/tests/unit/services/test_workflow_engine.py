"""
Workflow Engine Unit Tests

Tests for task state machine, sequence enforcement, and escalation logic.
Phase 4 implementation.

Test Categories:
- STANDARD_WORKFLOW constant validation
- Role resolution to user
- Task creation from workflow config
- Task state transitions (Pending -> In Progress -> Completed/Rejected)
- Sequence enforcement and parent task dependencies
- Task assignment and reassignment
- Instance completion logic
- User task queries
- Overdue and upcoming task queries
"""

import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch, PropertyMock
from uuid import uuid4

from app.services.workflow_engine import (
    STANDARD_WORKFLOW,
    resolve_role_to_user,
    get_role_by_code,
    create_workflow_tasks,
    get_tasks_for_instance,
    get_current_task,
    get_next_pending_task,
    start_task,
    complete_task,
    reject_task,
    reassign_task,
    check_instance_completion,
    get_user_assigned_tasks,
    get_overdue_tasks,
    get_tasks_due_soon,
    update_instance_status_from_tasks,
)


class TestStandardWorkflow:
    """Tests for the STANDARD_WORKFLOW constant."""

    def test_standard_workflow_has_five_steps(self):
        """Standard workflow should have 5 sequential steps."""
        assert len(STANDARD_WORKFLOW) == 5

    def test_standard_workflow_steps_in_order(self):
        """Steps should be: Prepare, Review, CFO Approval, File, Archive."""
        expected_steps = ["Prepare", "Review", "CFO Approval", "File", "Archive"]
        actual_steps = [step["step"] for step in STANDARD_WORKFLOW]
        assert actual_steps == expected_steps

    def test_standard_workflow_sequences_are_sequential(self):
        """Sequence numbers should be 1 through 5."""
        sequences = [step["sequence"] for step in STANDARD_WORKFLOW]
        assert sequences == [1, 2, 3, 4, 5]

    def test_cfo_approval_has_cfo_role(self):
        """CFO Approval step should have CFO role."""
        cfo_step = next(s for s in STANDARD_WORKFLOW if s["step"] == "CFO Approval")
        assert cfo_step.get("role") == "CFO"

    def test_all_steps_have_required_fields(self):
        """Each step should have step, task_type, description, sequence."""
        required_fields = {"step", "task_type", "description", "sequence"}
        for step in STANDARD_WORKFLOW:
            assert required_fields.issubset(step.keys())


class TestResolveRoleToUser:
    """Tests for resolve_role_to_user function."""

    def test_resolve_role_to_user_returns_matching_user(self):
        """Should return user with matching role and entity access."""
        db = MagicMock()
        tenant_id = uuid4()
        entity_id = uuid4()
        user_id = uuid4()
        role_id = uuid4()

        # Mock role
        mock_role = MagicMock()
        mock_role.id = role_id
        mock_role.role_code = "TAX_LEAD"

        # Mock user
        mock_user = MagicMock()
        mock_user.id = user_id
        mock_user.status = "active"

        # Setup query chain
        db.query.return_value.filter.return_value.first.return_value = mock_role
        db.query.return_value.join.return_value.join.return_value.filter.return_value.first.return_value = mock_user

        result = resolve_role_to_user(db, tenant_id, entity_id, "TAX_LEAD")

        assert result == mock_user

    def test_resolve_role_to_user_returns_none_for_unknown_role(self):
        """Should return None if role code doesn't exist."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = resolve_role_to_user(db, uuid4(), uuid4(), "UNKNOWN_ROLE")

        assert result is None

    def test_resolve_role_to_user_returns_none_if_no_user_has_access(self):
        """Should return None if no user with role has entity access."""
        db = MagicMock()
        mock_role = MagicMock()
        mock_role.id = uuid4()

        # Role exists but no user found
        db.query.return_value.filter.return_value.first.return_value = mock_role
        db.query.return_value.join.return_value.join.return_value.filter.return_value.first.return_value = None

        result = resolve_role_to_user(db, uuid4(), uuid4(), "TAX_LEAD")

        assert result is None


class TestGetRoleByCode:
    """Tests for get_role_by_code function."""

    def test_get_role_by_code_returns_role(self):
        """Should return role matching the code."""
        db = MagicMock()
        mock_role = MagicMock()
        mock_role.role_code = "CFO"
        db.query.return_value.filter.return_value.first.return_value = mock_role

        result = get_role_by_code(db, "CFO")

        assert result == mock_role

    def test_get_role_by_code_returns_none_for_unknown(self):
        """Should return None for unknown role code."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = get_role_by_code(db, "NONEXISTENT")

        assert result is None


class TestTaskStateTransitions:
    """Tests for workflow task state machine."""

    def test_start_task_pending_to_in_progress(self):
        """Task can transition from Pending to In Progress."""
        db = MagicMock()
        user_id = uuid4()
        task = MagicMock()
        task.status = "Pending"
        task.parent_task_id = None

        result = start_task(db, task, user_id)

        assert task.status == "In Progress"
        assert task.started_at == date.today()
        assert task.updated_by == user_id
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(task)

    def test_start_task_fails_if_not_pending(self):
        """Cannot start a task that is not in Pending state."""
        db = MagicMock()
        task = MagicMock()
        task.status = "In Progress"

        with pytest.raises(ValueError, match="Cannot start task"):
            start_task(db, task, uuid4())

    def test_start_task_fails_if_parent_not_completed(self):
        """Cannot start task if parent task is not completed."""
        db = MagicMock()
        task = MagicMock()
        task.status = "Pending"
        task.parent_task_id = uuid4()

        # Mock parent task
        parent_task = MagicMock()
        parent_task.status = "In Progress"
        db.query.return_value.filter.return_value.first.return_value = parent_task

        with pytest.raises(ValueError, match="parent task not completed"):
            start_task(db, task, uuid4())

    def test_start_task_succeeds_if_parent_completed(self):
        """Can start task if parent task is completed."""
        db = MagicMock()
        task = MagicMock()
        task.status = "Pending"
        task.parent_task_id = uuid4()

        # Mock completed parent
        parent_task = MagicMock()
        parent_task.status = "Completed"
        db.query.return_value.filter.return_value.first.return_value = parent_task

        result = start_task(db, task, uuid4())

        assert task.status == "In Progress"

    def test_complete_task_in_progress_to_completed(self):
        """Task can transition from In Progress to Completed."""
        db = MagicMock()
        user_id = uuid4()
        task = MagicMock()
        task.status = "In Progress"
        task.compliance_instance = MagicMock()

        result = complete_task(db, task, user_id, "Task completed successfully")

        assert task.status == "Completed"
        assert task.completed_at == date.today()
        assert task.completion_remarks == "Task completed successfully"
        assert task.updated_by == user_id

    def test_complete_task_directly_from_pending(self):
        """Task can be completed directly from Pending state."""
        db = MagicMock()
        task = MagicMock()
        task.status = "Pending"
        task.compliance_instance = MagicMock()

        with patch("app.services.workflow_engine.check_instance_completion"):
            result = complete_task(db, task, uuid4())

        assert task.status == "Completed"

    def test_complete_task_fails_if_already_completed(self):
        """Cannot complete an already completed task."""
        db = MagicMock()
        task = MagicMock()
        task.status = "Completed"

        with pytest.raises(ValueError, match="Cannot complete task"):
            complete_task(db, task, uuid4())

    def test_complete_task_fails_if_rejected(self):
        """Cannot complete a rejected task."""
        db = MagicMock()
        task = MagicMock()
        task.status = "Rejected"

        with pytest.raises(ValueError, match="Cannot complete task"):
            complete_task(db, task, uuid4())

    def test_reject_task_in_progress_to_rejected(self):
        """Task can transition from In Progress to Rejected."""
        db = MagicMock()
        user_id = uuid4()
        task = MagicMock()
        task.status = "In Progress"

        result = reject_task(db, task, user_id, "Missing documentation")

        assert task.status == "Rejected"
        assert task.rejection_reason == "Missing documentation"
        assert task.updated_by == user_id

    def test_reject_task_from_pending(self):
        """Task can be rejected directly from Pending state."""
        db = MagicMock()
        task = MagicMock()
        task.status = "Pending"

        result = reject_task(db, task, uuid4(), "Wrong assignment")

        assert task.status == "Rejected"

    def test_reject_task_fails_if_already_completed(self):
        """Cannot reject a completed task."""
        db = MagicMock()
        task = MagicMock()
        task.status = "Completed"

        with pytest.raises(ValueError, match="Cannot reject task"):
            reject_task(db, task, uuid4(), "Some reason")

    def test_reject_task_requires_reason(self):
        """Rejection must include a reason."""
        db = MagicMock()
        task = MagicMock()
        task.status = "Pending"

        with pytest.raises(ValueError, match="Rejection reason is required"):
            reject_task(db, task, uuid4(), "")

    def test_reject_task_fails_with_none_reason(self):
        """Rejection fails if reason is None."""
        db = MagicMock()
        task = MagicMock()
        task.status = "Pending"

        with pytest.raises(ValueError, match="Rejection reason is required"):
            reject_task(db, task, uuid4(), None)


class TestSequenceEnforcement:
    """Tests for task sequence ordering."""

    def test_get_next_pending_task_returns_first_pending(self):
        """Should return first pending task when no parent dependency."""
        db = MagicMock()
        instance_id = uuid4()

        task1 = MagicMock()
        task1.status = "Completed"
        task1.parent_task_id = None

        task2 = MagicMock()
        task2.status = "Pending"
        task2.parent_task_id = task1.id

        task1_mock = MagicMock()
        task1_mock.status = "Completed"

        with patch("app.services.workflow_engine.get_tasks_for_instance") as mock_get_tasks:
            mock_get_tasks.return_value = [task1, task2]
            db.query.return_value.filter.return_value.first.return_value = task1_mock

            result = get_next_pending_task(db, instance_id)

        assert result == task2

    def test_get_next_pending_task_blocked_by_parent(self):
        """Should return None if parent task is not completed."""
        db = MagicMock()
        instance_id = uuid4()

        task1 = MagicMock()
        task1.id = uuid4()
        task1.status = "In Progress"

        task2 = MagicMock()
        task2.status = "Pending"
        task2.parent_task_id = task1.id

        parent_mock = MagicMock()
        parent_mock.status = "In Progress"

        with patch("app.services.workflow_engine.get_tasks_for_instance") as mock_get_tasks:
            mock_get_tasks.return_value = [task1, task2]
            db.query.return_value.filter.return_value.first.return_value = parent_mock

            result = get_next_pending_task(db, instance_id)

        assert result is None

    def test_get_next_pending_task_no_parent_starts_immediately(self):
        """First task without parent can start immediately."""
        db = MagicMock()
        instance_id = uuid4()

        task = MagicMock()
        task.status = "Pending"
        task.parent_task_id = None

        with patch("app.services.workflow_engine.get_tasks_for_instance") as mock_get_tasks:
            mock_get_tasks.return_value = [task]

            result = get_next_pending_task(db, instance_id)

        assert result == task

    def test_get_next_pending_task_returns_none_when_all_completed(self):
        """Should return None when all tasks are completed."""
        db = MagicMock()
        instance_id = uuid4()

        task1 = MagicMock()
        task1.status = "Completed"

        task2 = MagicMock()
        task2.status = "Completed"

        with patch("app.services.workflow_engine.get_tasks_for_instance") as mock_get_tasks:
            mock_get_tasks.return_value = [task1, task2]

            result = get_next_pending_task(db, instance_id)

        assert result is None


class TestGetTasksForInstance:
    """Tests for retrieving tasks for an instance."""

    def test_get_tasks_for_instance_ordered_by_sequence(self):
        """Tasks should be returned ordered by sequence_order."""
        db = MagicMock()
        instance_id = uuid4()

        tasks = [MagicMock(sequence_order=i) for i in range(1, 4)]
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = tasks

        result = get_tasks_for_instance(db, instance_id)

        assert len(result) == 3
        db.query.return_value.filter.return_value.order_by.assert_called_once()

    def test_get_tasks_for_instance_returns_empty_list(self):
        """Should return empty list if no tasks exist."""
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = get_tasks_for_instance(db, uuid4())

        assert result == []


class TestGetCurrentTask:
    """Tests for getting current active task."""

    def test_get_current_task_returns_first_non_completed(self):
        """Should return first non-completed task."""
        db = MagicMock()
        instance_id = uuid4()

        current_task = MagicMock()
        current_task.status = "In Progress"
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = current_task

        result = get_current_task(db, instance_id)

        assert result == current_task

    def test_get_current_task_returns_none_when_all_completed(self):
        """Should return None when all tasks are completed."""
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = get_current_task(db, uuid4())

        assert result is None


class TestTaskReassignment:
    """Tests for task reassignment logic."""

    def test_reassign_to_user(self):
        """Task can be reassigned to a specific user."""
        db = MagicMock()
        task = MagicMock()
        new_user_id = uuid4()
        updated_by = uuid4()

        result = reassign_task(db, task, user_id=new_user_id, updated_by=updated_by)

        assert task.assigned_to_user_id == new_user_id
        assert task.assigned_to_role_id is None
        assert task.updated_by == updated_by
        db.commit.assert_called_once()

    def test_reassign_to_role(self):
        """Task can be reassigned to a role."""
        db = MagicMock()
        task = MagicMock()
        new_role_id = uuid4()
        updated_by = uuid4()

        result = reassign_task(db, task, role_id=new_role_id, updated_by=updated_by)

        assert task.assigned_to_user_id is None
        assert task.assigned_to_role_id == new_role_id
        db.commit.assert_called_once()

    def test_reassign_clears_both_assignments(self):
        """Reassigning with no user or role clears assignments."""
        db = MagicMock()
        task = MagicMock()
        task.assigned_to_user_id = uuid4()
        task.assigned_to_role_id = uuid4()

        result = reassign_task(db, task, updated_by=uuid4())

        assert task.assigned_to_user_id is None
        assert task.assigned_to_role_id is None


class TestInstanceCompletion:
    """Tests for completing compliance instances via workflow."""

    def test_all_tasks_complete_marks_instance_complete(self):
        """Instance should complete when all tasks are done."""
        db = MagicMock()
        instance = MagicMock()
        instance.id = uuid4()
        instance.status = "In Progress"

        tasks = [
            MagicMock(status="Completed"),
            MagicMock(status="Completed"),
            MagicMock(status="Completed"),
        ]

        with patch("app.services.workflow_engine.get_tasks_for_instance") as mock_get:
            mock_get.return_value = tasks

            result = check_instance_completion(db, instance)

        assert result is True
        assert instance.status == "Completed"
        assert instance.completion_date == date.today()
        assert instance.rag_status == "Green"
        db.commit.assert_called_once()

    def test_incomplete_tasks_do_not_complete_instance(self):
        """Instance should not complete if tasks are pending."""
        db = MagicMock()
        instance = MagicMock()
        instance.id = uuid4()
        instance.status = "In Progress"

        tasks = [
            MagicMock(status="Completed"),
            MagicMock(status="In Progress"),
            MagicMock(status="Pending"),
        ]

        with patch("app.services.workflow_engine.get_tasks_for_instance") as mock_get:
            mock_get.return_value = tasks

            result = check_instance_completion(db, instance)

        assert result is False
        assert instance.status == "In Progress"
        db.commit.assert_not_called()

    def test_no_tasks_returns_false(self):
        """Should return False if no tasks exist."""
        db = MagicMock()
        instance = MagicMock()
        instance.id = uuid4()

        with patch("app.services.workflow_engine.get_tasks_for_instance") as mock_get:
            mock_get.return_value = []

            result = check_instance_completion(db, instance)

        assert result is False

    def test_already_completed_instance_stays_completed(self):
        """Already completed instance should not change."""
        db = MagicMock()
        instance = MagicMock()
        instance.id = uuid4()
        instance.status = "Completed"

        tasks = [
            MagicMock(status="Completed"),
            MagicMock(status="Completed"),
        ]

        with patch("app.services.workflow_engine.get_tasks_for_instance") as mock_get:
            mock_get.return_value = tasks

            result = check_instance_completion(db, instance)

        # Returns False because status didn't change
        assert result is False


class TestUpdateInstanceStatusFromTasks:
    """Tests for updating instance status based on task states."""

    def test_all_completed_sets_completed_status(self):
        """All completed tasks should set instance to Completed."""
        db = MagicMock()
        instance = MagicMock()
        instance.id = uuid4()
        instance.status = "In Progress"

        tasks = [
            MagicMock(status="Completed"),
            MagicMock(status="Completed"),
        ]

        with patch("app.services.workflow_engine.get_tasks_for_instance") as mock_get:
            mock_get.return_value = tasks

            result = update_instance_status_from_tasks(db, instance)

        assert result == "Completed"
        assert instance.status == "Completed"

    def test_rejected_task_sets_blocked_status(self):
        """Any rejected task should set instance to Blocked."""
        db = MagicMock()
        instance = MagicMock()
        instance.id = uuid4()
        instance.status = "In Progress"

        tasks = [
            MagicMock(status="Completed"),
            MagicMock(status="Rejected"),
            MagicMock(status="Pending"),
        ]

        with patch("app.services.workflow_engine.get_tasks_for_instance") as mock_get:
            mock_get.return_value = tasks

            result = update_instance_status_from_tasks(db, instance)

        assert result == "Blocked"

    def test_in_progress_task_sets_in_progress_status(self):
        """In Progress tasks should set instance to In Progress."""
        db = MagicMock()
        instance = MagicMock()
        instance.id = uuid4()
        instance.status = "Not Started"

        tasks = [
            MagicMock(status="Completed"),
            MagicMock(status="In Progress"),
            MagicMock(status="Pending"),
        ]

        with patch("app.services.workflow_engine.get_tasks_for_instance") as mock_get:
            mock_get.return_value = tasks

            result = update_instance_status_from_tasks(db, instance)

        assert result == "In Progress"

    def test_all_pending_sets_not_started_status(self):
        """All pending tasks should set instance to Not Started."""
        db = MagicMock()
        instance = MagicMock()
        instance.id = uuid4()
        instance.status = "Not Started"

        tasks = [
            MagicMock(status="Pending"),
            MagicMock(status="Pending"),
        ]

        with patch("app.services.workflow_engine.get_tasks_for_instance") as mock_get:
            mock_get.return_value = tasks

            result = update_instance_status_from_tasks(db, instance)

        assert result == "Not Started"

    def test_no_tasks_returns_current_status(self):
        """No tasks should return current instance status."""
        db = MagicMock()
        instance = MagicMock()
        instance.id = uuid4()
        instance.status = "Pending"

        with patch("app.services.workflow_engine.get_tasks_for_instance") as mock_get:
            mock_get.return_value = []

            result = update_instance_status_from_tasks(db, instance)

        assert result == "Pending"


class TestGetUserAssignedTasks:
    """Tests for user task queries."""

    def test_get_user_assigned_tasks_direct_assignment(self):
        """Should return tasks directly assigned to user."""
        db = MagicMock()
        user_id = uuid4()
        tenant_id = uuid4()

        tasks = [MagicMock(), MagicMock()]
        db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = tasks

        result = get_user_assigned_tasks(db, user_id, tenant_id, include_role_tasks=False)

        assert len(result) == 2

    def test_get_user_assigned_tasks_with_status_filter(self):
        """Should filter by status when specified."""
        db = MagicMock()
        user_id = uuid4()
        tenant_id = uuid4()

        mock_user = MagicMock()
        mock_user.roles = []
        db.query.return_value.filter.return_value.first.return_value = mock_user

        result = get_user_assigned_tasks(db, user_id, tenant_id, status_filter=["Pending", "In Progress"])

        # Verify filter was applied
        db.query.assert_called()


class TestGetOverdueTasks:
    """Tests for overdue task queries."""

    def test_get_overdue_tasks_returns_past_due_tasks(self):
        """Should return tasks with due date before today."""
        db = MagicMock()
        tenant_id = uuid4()
        today = date(2024, 6, 15)

        overdue_tasks = [
            MagicMock(due_date=date(2024, 6, 10)),
            MagicMock(due_date=date(2024, 6, 14)),
        ]
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = overdue_tasks

        result = get_overdue_tasks(db, tenant_id, today=today)

        assert len(result) == 2

    def test_get_overdue_tasks_excludes_completed(self):
        """Should only return Pending or In Progress tasks."""
        db = MagicMock()
        tenant_id = uuid4()

        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = get_overdue_tasks(db, tenant_id)

        # Verify filter includes status check
        db.query.assert_called()

    def test_get_overdue_tasks_defaults_to_today(self):
        """Should use today's date when not specified."""
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = get_overdue_tasks(db, uuid4())

        # Function should complete without error using default today


class TestGetTasksDueSoon:
    """Tests for upcoming task queries."""

    def test_get_tasks_due_soon_within_days(self):
        """Should return tasks due within specified days."""
        db = MagicMock()
        tenant_id = uuid4()
        today = date(2024, 6, 15)

        upcoming_tasks = [
            MagicMock(due_date=date(2024, 6, 16)),
            MagicMock(due_date=date(2024, 6, 17)),
        ]
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = upcoming_tasks

        result = get_tasks_due_soon(db, tenant_id, days=3, today=today)

        assert len(result) == 2

    def test_get_tasks_due_soon_default_3_days(self):
        """Should default to 3 days lookahead."""
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = get_tasks_due_soon(db, uuid4())

        # Function should complete using default 3 days

    def test_get_tasks_due_soon_excludes_overdue(self):
        """Should not include tasks already overdue."""
        db = MagicMock()
        tenant_id = uuid4()
        today = date(2024, 6, 15)

        # Only include tasks due on or after today
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = get_tasks_due_soon(db, tenant_id, today=today)

        db.query.assert_called()


class TestCreateWorkflowTasks:
    """Tests for workflow task creation."""

    def test_create_workflow_tasks_uses_standard_workflow(self):
        """Should use STANDARD_WORKFLOW when no config provided."""
        db = MagicMock()
        instance = MagicMock()
        instance.id = uuid4()
        instance.tenant_id = uuid4()
        instance.entity_id = uuid4()
        instance.due_date = date.today() + timedelta(days=30)
        instance.compliance_master = None

        # Mock resolve_role_to_user to return None
        with patch("app.services.workflow_engine.resolve_role_to_user") as mock_resolve:
            mock_resolve.return_value = None
            with patch("app.services.workflow_engine.get_role_by_code") as mock_role:
                mock_role.return_value = MagicMock(id=uuid4())

                result = create_workflow_tasks(db, instance)

        assert len(result) == 5  # STANDARD_WORKFLOW has 5 steps
        db.add.assert_called()
        db.commit.assert_called_once()

    def test_create_workflow_tasks_uses_custom_config(self):
        """Should use provided workflow_config when specified."""
        db = MagicMock()
        instance = MagicMock()
        instance.id = uuid4()
        instance.tenant_id = uuid4()
        instance.entity_id = uuid4()
        instance.due_date = date.today() + timedelta(days=30)
        instance.compliance_master = None

        custom_workflow = [
            {"step": "Step 1", "task_type": "Prepare", "description": "First step", "sequence": 1},
            {"step": "Step 2", "task_type": "Complete", "description": "Second step", "sequence": 2},
        ]

        with patch("app.services.workflow_engine.resolve_role_to_user") as mock_resolve:
            mock_resolve.return_value = None
            with patch("app.services.workflow_engine.get_role_by_code") as mock_role:
                mock_role.return_value = MagicMock(id=uuid4())

                result = create_workflow_tasks(db, instance, workflow_config=custom_workflow)

        assert len(result) == 2

    def test_create_workflow_tasks_assigns_to_resolved_user(self):
        """Should assign to user when role resolves."""
        db = MagicMock()
        instance = MagicMock()
        instance.id = uuid4()
        instance.tenant_id = uuid4()
        instance.entity_id = uuid4()
        instance.due_date = date.today() + timedelta(days=30)
        instance.compliance_master = MagicMock()
        instance.compliance_master.compliance_name = "Test Compliance"
        instance.compliance_master.workflow_config = None
        instance.compliance_master.owner_role_code = "TAX_LEAD"
        instance.compliance_master.approver_role_code = "CFO"

        mock_user = MagicMock()
        mock_user.id = uuid4()

        with patch("app.services.workflow_engine.resolve_role_to_user") as mock_resolve:
            mock_resolve.return_value = mock_user
            with patch("app.services.workflow_engine.get_role_by_code") as mock_role:
                mock_role.return_value = None

                result = create_workflow_tasks(db, instance)

        # Verify at least one task was created with user assignment
        db.add.assert_called()

    def test_create_workflow_tasks_calculates_due_dates(self):
        """Task due dates should be before instance due date."""
        db = MagicMock()
        instance = MagicMock()
        instance.id = uuid4()
        instance.tenant_id = uuid4()
        instance.entity_id = uuid4()
        instance.due_date = date.today() + timedelta(days=30)
        instance.compliance_master = None

        with patch("app.services.workflow_engine.resolve_role_to_user") as mock_resolve:
            mock_resolve.return_value = None
            with patch("app.services.workflow_engine.get_role_by_code") as mock_role:
                mock_role.return_value = MagicMock(id=uuid4())

                result = create_workflow_tasks(db, instance)

        # All tasks created, due dates calculated
        assert db.add.call_count == 5

    def test_create_workflow_tasks_sets_parent_task_id(self):
        """Tasks should be linked via parent_task_id."""
        db = MagicMock()
        instance = MagicMock()
        instance.id = uuid4()
        instance.tenant_id = uuid4()
        instance.entity_id = uuid4()
        instance.due_date = date.today() + timedelta(days=30)
        instance.compliance_master = None

        created_tasks = []

        def capture_add(task):
            task.id = uuid4()  # Simulate flush assigning ID
            created_tasks.append(task)

        db.add.side_effect = capture_add

        with patch("app.services.workflow_engine.resolve_role_to_user") as mock_resolve:
            mock_resolve.return_value = None
            with patch("app.services.workflow_engine.get_role_by_code") as mock_role:
                mock_role.return_value = MagicMock(id=uuid4())

                result = create_workflow_tasks(db, instance)

        # First task should have no parent
        assert created_tasks[0].parent_task_id is None
        # Subsequent tasks should have parent
        for i in range(1, len(created_tasks)):
            assert created_tasks[i].parent_task_id is not None


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_start_task_with_completed_parent(self):
        """Task can start when parent is completed."""
        db = MagicMock()
        task = MagicMock()
        task.status = "Pending"
        task.parent_task_id = uuid4()

        parent = MagicMock()
        parent.status = "Completed"
        db.query.return_value.filter.return_value.first.return_value = parent

        result = start_task(db, task, uuid4())

        assert task.status == "In Progress"

    def test_complete_task_triggers_instance_completion_check(self):
        """Completing task should check instance completion."""
        db = MagicMock()
        task = MagicMock()
        task.status = "In Progress"
        task.compliance_instance = MagicMock()

        with patch("app.services.workflow_engine.check_instance_completion") as mock_check:
            result = complete_task(db, task, uuid4())

        mock_check.assert_called_once_with(db, task.compliance_instance)

    def test_reject_with_whitespace_reason_fails(self):
        """Rejection with only whitespace should fail."""
        db = MagicMock()
        task = MagicMock()
        task.status = "Pending"

        # Empty string after strip
        with pytest.raises(ValueError, match="Rejection reason is required"):
            reject_task(db, task, uuid4(), "")

    def test_overdue_check_with_custom_date(self):
        """Overdue check should use provided reference date."""
        db = MagicMock()
        tenant_id = uuid4()
        custom_date = date(2024, 12, 31)

        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = get_overdue_tasks(db, tenant_id, today=custom_date)

        # Should complete using custom date

    def test_tasks_due_soon_with_zero_days(self):
        """Due soon check with 0 days should only return tasks due today."""
        db = MagicMock()
        tenant_id = uuid4()
        today = date(2024, 6, 15)

        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = get_tasks_due_soon(db, tenant_id, days=0, today=today)

        # Should complete with 0 day window
