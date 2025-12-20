"""
Seed script to generate test compliance instances with varied RAG statuses
"""

import uuid
from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models import (
    Entity,
    ComplianceMaster,
    ComplianceInstance,
    User,
    Tenant,
)


def create_test_entities(db: Session, tenant_id: str, user_id: str) -> list[Entity]:
    """Create 2 test entities for the tenant"""
    entities_data = [
        {
            "entity_code": "GCCINDIA01",
            "entity_name": "GCC India Pvt Ltd",
            "entity_type": "Private Limited Company",
            "pan": "AABCG1234F",
            "gstin": "29AABCG1234F1Z5",
            "cin": "U72900KA2020PTC134567",
            "address": "123 Tech Park, Bangalore",
            "city": "Bangalore",
            "state": "Karnataka",
            "pincode": "560001",
            "status": "active",
        },
        {
            "entity_code": "GCCMUM01",
            "entity_name": "GCC Mumbai Branch",
            "entity_type": "Branch Office",
            "pan": "AABCG1234F",
            "gstin": "27AABCG1234F1Z6",
            "address": "456 Business Center, Mumbai",
            "city": "Mumbai",
            "state": "Maharashtra",
            "pincode": "400001",
            "status": "active",
        },
    ]

    entities = []
    for entity_data in entities_data:
        # Check if entity already exists
        existing = (
            db.query(Entity)
            .filter(
                Entity.tenant_id == tenant_id,
                Entity.entity_code == entity_data["entity_code"],
            )
            .first()
        )

        if not existing:
            entity = Entity(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                created_by=user_id,
                updated_by=user_id,
                **entity_data,
            )
            db.add(entity)
            entities.append(entity)
            print(f"  ✓ Created entity: {entity_data['entity_code']}")
        else:
            entities.append(existing)
            print(f"  ⊘ Entity already exists: {entity_data['entity_code']}")

    db.flush()
    return entities


def generate_compliance_instances(
    db: Session, tenant_id: str, entities: list[Entity], user_id: str
) -> list[ComplianceInstance]:
    """Generate compliance instances with varied RAG statuses"""

    # Get compliance masters
    masters = (
        db.query(ComplianceMaster)
        .filter(ComplianceMaster.tenant_id.is_(None))  # System-wide templates
        .limit(12)
        .all()
    )

    if not masters:
        print("  ❌ No compliance masters found. Run compliance_masters_seed first.")
        return []

    instances = []
    today = date.today()

    # RAG distribution targets: 10 Green, 8 Amber, 6 Red
    rag_statuses = ["Green"] * 10 + ["Amber"] * 8 + ["Red"] * 6

    # Status options
    statuses = [
        "Not Started",
        "In Progress",
        "Review",
        "Pending Approval",
        "Filed",
        "Completed",
    ]

    instance_count = 0
    for i, master in enumerate(masters):
        for entity in entities:
            # Calculate dates based on RAG status
            if instance_count < len(rag_statuses):
                rag = rag_statuses[instance_count]
            else:
                rag = "Green"

            # Set due dates based on RAG status
            if rag == "Green":
                # Due date > 7 days away
                due_date = today + timedelta(days=10 + i)
                status = statuses[instance_count % 3]  # Mix of statuses
            elif rag == "Amber":
                # Due date < 7 days away
                due_date = today + timedelta(days=3 + (i % 5))
                status = "In Progress"
            else:  # Red
                # Overdue
                due_date = today - timedelta(days=5 + i)
                status = "Overdue"

            # Period is typically the month before due date
            period_end = due_date - timedelta(days=1)
            if master.frequency == "monthly":
                period_start = period_end.replace(day=1)
            elif master.frequency == "quarterly":
                # Q1: Jan-Mar, Q2: Apr-Jun, Q3: Jul-Sep, Q4: Oct-Dec
                month = period_end.month
                quarter_start_month = ((month - 1) // 3) * 3 + 1
                period_start = period_end.replace(month=quarter_start_month, day=1)
            elif master.frequency == "annual":
                period_start = period_end.replace(month=4, day=1)  # FY start
            else:
                period_start = period_end - timedelta(days=30)

            # Check if instance already exists
            existing = (
                db.query(ComplianceInstance)
                .filter(
                    ComplianceInstance.compliance_master_id == master.id,
                    ComplianceInstance.entity_id == entity.id,
                    ComplianceInstance.period_start == period_start,
                    ComplianceInstance.period_end == period_end,
                )
                .first()
            )

            if not existing:
                instance = ComplianceInstance(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    compliance_master_id=master.id,
                    entity_id=entity.id,
                    period_start=period_start,
                    period_end=period_end,
                    due_date=due_date,
                    status=status,
                    rag_status=rag,
                    owner_user_id=user_id if instance_count % 2 == 0 else None,
                    created_by=user_id,
                    updated_by=user_id,
                    meta_data={
                        "compliance_code": master.compliance_code,
                        "compliance_name": master.compliance_name,
                        "category": master.category,
                    },
                )
                db.add(instance)
                instances.append(instance)
                instance_count += 1

                # Stop at 24 instances (12 masters x 2 entities)
                if instance_count >= 24:
                    break

        if instance_count >= 24:
            break

    db.flush()
    print(f"  ✓ Created {len(instances)} compliance instances")

    # Print RAG distribution
    rag_counts = {"Green": 0, "Amber": 0, "Red": 0}
    for instance in instances:
        rag_counts[instance.rag_status] += 1
    print(
        f"    RAG Distribution: Green={rag_counts['Green']}, Amber={rag_counts['Amber']}, Red={rag_counts['Red']}"
    )

    return instances


def main():
    """Main seed runner for compliance instances"""
    print("=" * 70)
    print("COMPLIANCE INSTANCES - SEED SCRIPT")
    print("=" * 70)
    print()

    db = SessionLocal()

    try:
        # Get the test tenant and user we created earlier
        tenant = db.query(Tenant).filter(Tenant.tenant_code == "TEST001").first()
        if not tenant:
            print("❌ Test tenant not found. Please create a test tenant first.")
            return

        user = (
            db.query(User)
            .filter(User.tenant_id == tenant.id, User.email == "admin@testgcc.com")
            .first()
        )
        if not user:
            print("❌ Test user not found. Please create a test user first.")
            return

        print(f"Using tenant: {tenant.tenant_name} ({tenant.id})")
        print(f"Using user: {user.email} ({user.id})")
        print()

        # Create entities
        print("Creating test entities...")
        entities = create_test_entities(db, str(tenant.id), str(user.id))
        print()

        # Grant user access to entities
        print("Granting user access to entities...")
        for entity in entities:
            # Check if access already granted
            from sqlalchemy import text

            existing = db.execute(
                text(
                    "SELECT 1 FROM entity_access WHERE user_id = :user_id AND entity_id = :entity_id"
                ),
                {"user_id": str(user.id), "entity_id": str(entity.id)},
            ).first()

            if not existing:
                db.execute(
                    text(
                        "INSERT INTO entity_access (user_id, entity_id, tenant_id) VALUES (:user_id, :entity_id, :tenant_id)"
                    ),
                    {
                        "user_id": str(user.id),
                        "entity_id": str(entity.id),
                        "tenant_id": str(tenant.id),
                    },
                )
                print(f"  ✓ Granted access to: {entity.entity_code}")
            else:
                print(f"  ⊘ Access already granted: {entity.entity_code}")
        print()

        # Generate compliance instances
        print("Generating compliance instances...")
        instances = generate_compliance_instances(db, str(tenant.id), entities, str(user.id))
        print()

        # Commit all changes
        db.commit()

        print("=" * 70)
        print("SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print()
        print(f"Summary:")
        print(f"  - Entities created: {len(entities)}")
        print(f"  - Compliance instances created: {len(instances)}")
        print()

    except Exception as e:
        print(f"\n❌ Error during seeding: {str(e)}")
        import traceback

        traceback.print_exc()
        db.rollback()

    finally:
        db.close()


if __name__ == "__main__":
    main()
