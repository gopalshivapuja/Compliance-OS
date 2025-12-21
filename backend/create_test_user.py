"""
Create a test user for manual testing
Run this script to create a test user that you can use to login to the application.
"""

from app.core.database import SessionLocal
from app.models import Tenant, User, Role, user_roles, Entity, entity_access
from app.core.security import get_password_hash


def create_test_data():
    """Create test tenant, user, and entities for manual testing"""
    db = SessionLocal()

    try:
        print("=" * 70)
        print("CREATING TEST USER FOR MANUAL TESTING")
        print("=" * 70)
        print()

        # 1. Create test tenant
        print("1. Creating test tenant...")
        existing_tenant = db.query(Tenant).filter(Tenant.tenant_code == "TEST_GCC").first()
        if existing_tenant:
            tenant = existing_tenant
            print(f"   ✓ Using existing tenant: {tenant.tenant_name}")
        else:
            tenant = Tenant(
                tenant_name="Test GCC Company",
                tenant_code="TEST_GCC",
                contact_email="admin@testgcc.com",
                status="active",
            )
            db.add(tenant)
            db.flush()
            print(f"   ✓ Created tenant: {tenant.tenant_name}")

        # 2. Get or create roles
        print("\n2. Getting system roles...")
        cfo_role = db.query(Role).filter(Role.role_code == "CFO").first()
        system_admin_role = db.query(Role).filter(Role.role_code == "SYSTEM_ADMIN").first()
        tax_lead_role = db.query(Role).filter(Role.role_code == "TAX_LEAD").first()

        if not cfo_role or not system_admin_role or not tax_lead_role:
            print("   ⚠️  System roles not found. Please run seed script first:")
            print("      cd backend && python -m app.seeds.run_seed")
            return

        print("   ✓ Found CFO role")
        print("   ✓ Found System Admin role")
        print("   ✓ Found Tax Lead role")

        # 3. Create test users with different roles
        print("\n3. Creating test users...")

        users_to_create = [
            {
                "email": "admin@testgcc.com",
                "first_name": "System",
                "last_name": "Admin",
                "password": "Admin123!",  # pragma: allowlist secret
                "role": system_admin_role,
                "role_name": "System Admin",
            },
            {
                "email": "cfo@testgcc.com",
                "first_name": "Chief",
                "last_name": "Financial Officer",
                "password": "CFO12345!",  # pragma: allowlist secret
                "role": cfo_role,
                "role_name": "CFO",
            },
            {
                "email": "tax@testgcc.com",
                "first_name": "Tax",
                "last_name": "Lead",
                "password": "Tax12345!",  # pragma: allowlist secret
                "role": tax_lead_role,
                "role_name": "Tax Lead",
            },
        ]

        created_users = []
        for user_data in users_to_create:
            existing_user = db.query(User).filter(User.email == user_data["email"]).first()
            if existing_user:
                print(f"   ⊘ User already exists: {user_data['email']}")
                created_users.append(existing_user)
                continue

            user = User(
                tenant_id=tenant.id,
                email=user_data["email"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                password_hash=get_password_hash(user_data["password"]),
                status="active",
                is_system_admin=(user_data["role_name"] == "System Admin"),
            )
            db.add(user)
            db.flush()

            # Assign role
            db.execute(
                user_roles.insert().values(
                    user_id=user.id,
                    role_id=user_data["role"].id,
                    tenant_id=tenant.id,
                )
            )

            created_users.append(user)
            print(f"   ✓ Created user: {user_data['email']} ({user_data['role_name']})")

        # 4. Create test entities
        print("\n4. Creating test entities...")
        entities_to_create = [
            {
                "entity_code": "IND-BLR",
                "entity_name": "India - Bangalore GCC",
                "entity_type": "Company",
            },
            {
                "entity_code": "IND-HYD",
                "entity_name": "India - Hyderabad Branch",
                "entity_type": "Branch",
            },
        ]

        created_entities = []
        for entity_data in entities_to_create:
            existing_entity = (
                db.query(Entity)
                .filter(Entity.entity_code == entity_data["entity_code"], Entity.tenant_id == tenant.id)
                .first()
            )
            if existing_entity:
                print(f"   ⊘ Entity already exists: {entity_data['entity_code']}")
                created_entities.append(existing_entity)
                continue

            entity = Entity(
                tenant_id=tenant.id,
                entity_code=entity_data["entity_code"],
                entity_name=entity_data["entity_name"],
                entity_type=entity_data["entity_type"],
                status="active",
            )
            db.add(entity)
            db.flush()
            created_entities.append(entity)
            print(f"   ✓ Created entity: {entity_data['entity_code']}")

        # 5. Grant entity access to all users
        print("\n5. Granting entity access...")
        for user in created_users:
            for entity in created_entities:
                # Check if access already exists
                existing_access = db.execute(
                    entity_access.select().where(
                        entity_access.c.user_id == user.id,
                        entity_access.c.entity_id == entity.id,
                    )
                ).first()

                if not existing_access:
                    db.execute(
                        entity_access.insert().values(
                            user_id=user.id,
                            entity_id=entity.id,
                            tenant_id=tenant.id,
                        )
                    )
                    print(f"   ✓ Granted {user.email} access to {entity.entity_code}")

        db.commit()

        print("\n" + "=" * 70)
        print("TEST DATA CREATED SUCCESSFULLY!")
        print("=" * 70)
        print()
        print("You can now login with these accounts:")
        print()
        print("1. System Admin:")
        print("   Email:    admin@testgcc.com")
        print("   Password: Admin123!")
        print("   Access:   Full system access, can view audit logs")
        print()
        print("2. CFO:")
        print("   Email:    cfo@testgcc.com")
        print("   Password: CFO12345!")
        print("   Access:   Can approve, view audit logs")
        print()
        print("3. Tax Lead:")
        print("   Email:    tax@testgcc.com")
        print("   Password: Tax12345!")
        print("   Access:   Can manage compliance instances")
        print()
        print("Frontend: http://localhost:3000/login")
        print("Backend API: http://localhost:8000/docs")
        print()

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    create_test_data()
