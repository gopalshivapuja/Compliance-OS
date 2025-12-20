"""
Seed runner script to populate initial data
"""

import sys
from sqlalchemy.orm import Session
from app.core.database import engine, SessionLocal
from app.models import Base, ComplianceMaster, Role
from app.seeds.compliance_masters_seed import COMPLIANCE_MASTERS_SEED


def seed_roles(db: Session):
    """Seed default system roles"""
    roles_data = [
        {
            "role_code": "SYSTEM_ADMIN",
            "role_name": "System Administrator",
            "description": "Super user with access to all tenants and system configuration",
            "is_system_role": "yes",
        },
        {
            "role_code": "TENANT_ADMIN",
            "role_name": "Tenant Administrator",
            "description": "Manages users, entities, and compliance masters within their tenant",
            "is_system_role": "yes",
        },
        {
            "role_code": "CFO",
            "role_name": "CFO / Approver",
            "description": "Reviews and approves compliance instances and evidence",
            "is_system_role": "yes",
        },
        {
            "role_code": "TAX_LEAD",
            "role_name": "Tax Lead / Compliance Owner",
            "description": "Manages compliance instances, uploads evidence, marks as complete",
            "is_system_role": "yes",
        },
        {
            "role_code": "HR_LEAD",
            "role_name": "HR Lead",
            "description": "Manages payroll-related compliances",
            "is_system_role": "yes",
        },
        {
            "role_code": "COMPANY_SECRETARY",
            "role_name": "Company Secretary",
            "description": "Manages MCA and corporate governance compliances",
            "is_system_role": "yes",
        },
        {
            "role_code": "FPA_LEAD",
            "role_name": "FP&A Lead",
            "description": "Manages financial planning and analysis compliances",
            "is_system_role": "yes",
        },
    ]

    print("Seeding roles...")
    for role_data in roles_data:
        existing_role = db.query(Role).filter(Role.role_code == role_data["role_code"]).first()
        if not existing_role:
            role = Role(**role_data)
            db.add(role)
            print(f"  ✓ Created role: {role_data['role_code']}")
        else:
            print(f"  ⊘ Role already exists: {role_data['role_code']}")

    db.commit()
    print("Roles seeding completed!\n")


def seed_compliance_masters(db: Session):
    """Seed pre-loaded Indian GCC compliance masters"""
    print("Seeding compliance masters...")

    created_count = 0
    skipped_count = 0

    for master_data in COMPLIANCE_MASTERS_SEED:
        # Check if compliance master already exists (by code)
        existing_master = (
            db.query(ComplianceMaster)
            .filter(
                ComplianceMaster.compliance_code == master_data["compliance_code"],
                ComplianceMaster.tenant_id.is_(None),  # System-wide templates have NULL tenant_id
            )
            .first()
        )

        if not existing_master:
            compliance_master = ComplianceMaster(
                tenant_id=None,  # System-wide template
                **master_data,
            )
            db.add(compliance_master)
            created_count += 1
            print(
                f"  ✓ Created: {master_data['compliance_code']} - {master_data['compliance_name']}"
            )
        else:
            skipped_count += 1
            print(f"  ⊘ Already exists: {master_data['compliance_code']}")

    db.commit()
    print(f"\nCompliance masters seeding completed!")
    print(f"  Created: {created_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Total: {created_count + skipped_count}\n")


def main():
    """Main seed runner"""
    print("=" * 70)
    print("COMPLIANCE OS - DATABASE SEED SCRIPT")
    print("=" * 70)
    print()

    # Create database session
    db = SessionLocal()

    try:
        # Seed roles first
        seed_roles(db)

        # Seed compliance masters
        seed_compliance_masters(db)

        print("=" * 70)
        print("SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  1. Run the backend server: uvicorn app.main:app --reload")
        print("  2. Access API docs: http://localhost:8000/docs")
        print()

    except Exception as e:
        print(f"\n❌ Error during seeding: {str(e)}")
        db.rollback()
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()
