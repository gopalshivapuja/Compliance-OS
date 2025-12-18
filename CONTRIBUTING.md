# Contributing to Compliance OS

First off, thank you for considering contributing to Compliance OS! This project aims to revolutionize compliance management for Global Capability Centers in India.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## Getting Started

### Development Setup

For detailed setup instructions, please refer to [PHASE1_SETUP_GUIDE.md](./PHASE1_SETUP_GUIDE.md).

Quick setup:

```bash
# Clone the repository
git clone https://github.com/your-org/compliance-os.git
cd compliance-os

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration

# Frontend setup
cd ../frontend
npm install
cp .env.example .env
# Edit .env with your configuration
```

## Development Workflow

### Branch Naming Conventions

We follow a structured branch naming convention:

- `feature/short-description` - For new features
- `fix/short-description` - For bug fixes
- `docs/short-description` - For documentation updates
- `refactor/short-description` - For code refactoring
- `test/short-description` - For adding tests

Examples:
- `feature/evidence-approval-workflow`
- `fix/rag-status-calculation`
- `docs/update-api-documentation`

### Commit Message Format

We use a structured commit message format for clarity and automated changelog generation:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no functional changes)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Build process, dependencies, or auxiliary tool changes

**Example**:
```
feat(auth): implement JWT token refresh endpoint

- Add refresh token endpoint to /api/v1/auth/refresh
- Store refresh tokens in Redis with 7-day expiry
- Add token blacklisting on logout
- Update auth store to handle token refresh

Closes #42
```

## Making Changes

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Write clear, commented code
- Follow the project's code style (see below)
- Add tests for new functionality
- Update documentation as needed

### 3. Test Your Changes

**Backend**:
```bash
cd backend
pytest                      # Run tests
black app/                  # Format code
flake8 app/                 # Lint code
mypy app/                   # Type check
```

**Frontend**:
```bash
cd frontend
npm test                    # Run tests
npm run lint                # Lint code
npm run type-check          # TypeScript check
npm run format              # Format code
```

### 4. Commit Your Changes

```bash
git add .
git commit -m "feat(module): clear description of changes"
```

### 5. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 6. Create a Pull Request

- Go to the repository on GitHub
- Click "New Pull Request"
- Select your branch
- Fill out the PR template (see below)
- Request review from maintainers

## Pull Request Process

### PR Title Format

```
<type>(<scope>): <description>
```

Example: `feat(evidence): add approval workflow with immutability`

### PR Description Template

```markdown
## Description
Brief description of the changes made.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Related Issue
Closes #[issue number]

## Changes Made
- Bullet point list of changes
- Be specific and clear

## Testing Done
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] No new linter errors

## Screenshots (if applicable)
Add screenshots for UI changes.

## Checklist
- [ ] My code follows the project's code style
- [ ] I have commented my code where necessary
- [ ] I have updated the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix/feature works
- [ ] All tests pass locally
```

### Code Review Checklist

Your PR will be reviewed for:

✅ **Functionality**: Does it work as intended?
✅ **Code Quality**: Is it clean, readable, and maintainable?
✅ **Tests**: Are there adequate tests?
✅ **Documentation**: Is documentation updated?
✅ **Security**: Are there any security concerns?
✅ **Performance**: Are there any performance implications?
✅ **Audit Readiness**: Does it maintain audit trail requirements?

## Code Style Guidelines

### Backend (Python/FastAPI)

**Follow PEP 8** with these specifics:

- Use **Black** for formatting (line length: 120)
- Use **type hints** for all function parameters and return values
- Use **docstrings** for classes and complex functions
- Import order: standard library, third-party, local imports

**Example**:
```python
from typing import List, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.user import UserResponse

async def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
) -> List[UserResponse]:
    """
    Retrieve a list of users with pagination.

    Args:
        db: Database session
        current_user: Authenticated user
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of user objects
    """
    # Implementation
    pass
```

**Naming Conventions**:
- Functions/variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_leading_underscore`

### Frontend (TypeScript/React)

**Follow Airbnb JavaScript Style Guide** with these specifics:

- Use **Prettier** for formatting
- Use **functional components** with hooks
- Use **TypeScript strict mode**
- Use **named exports** over default exports

**Example**:
```typescript
import { useState, useEffect } from 'react';
import { useAuthStore } from '@/lib/store/auth-store';
import { ComplianceInstance } from '@/types';
import { api } from '@/lib/api/client';

interface DashboardProps {
  tenantId: string;
  entityId?: string;
}

export function Dashboard({ tenantId, entityId }: DashboardProps) {
  const [instances, setInstances] = useState<ComplianceInstance[]>([]);
  const { user } = useAuthStore();

  useEffect(() => {
    // Fetch compliance instances
  }, [tenantId, entityId]);

  return (
    <div className="dashboard">
      {/* Component JSX */}
    </div>
  );
}
```

**Naming Conventions**:
- Components: `PascalCase`
- Functions/variables: `camelCase`
- Constants: `UPPER_SNAKE_CASE`
- Types/Interfaces: `PascalCase`

### Database Migrations

When creating Alembic migrations:

```bash
# Always review auto-generated migrations
alembic revision --autogenerate -m "add evidence approval workflow"

# Edit the generated migration file to:
# 1. Add data migrations if needed
# 2. Ensure indexes are created
# 3. Add comments for clarity
# 4. Test upgrade and downgrade

alembic upgrade head      # Test upgrade
alembic downgrade -1      # Test downgrade
```

## Testing Requirements

### Backend Tests

**Required test coverage**: >80% for new code

**Test structure**:
```
backend/tests/
├── unit/
│   ├── models/          # Model tests
│   ├── services/        # Service logic tests
│   └── utils/           # Utility function tests
└── integration/
    └── api/             # API endpoint tests
```

**Example**:
```python
# tests/unit/models/test_user.py
def test_user_password_hashing(db_session):
    """Test that user passwords are hashed correctly."""
    user = User(email="test@example.com")
    user.set_password("Test123!@#")

    assert user.password_hash != "Test123!@#"
    assert user.verify_password("Test123!@#")
    assert not user.verify_password("wrongpassword")
```

### Frontend Tests

**Required test coverage**: >70% for new components

**Test structure**:
```
frontend/src/__tests__/
├── components/
├── lib/
└── integration/
```

**Example**:
```typescript
// __tests__/components/Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from '@/components/ui/Button';

describe('Button', () => {
  it('renders with correct text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('calls onClick handler when clicked', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    fireEvent.click(screen.getByText('Click me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

## Security Guidelines

### Critical Requirements

1. **Multi-Tenant Isolation**: ALWAYS filter queries by `tenant_id`
2. **Input Validation**: Validate all user inputs with Pydantic/Zod
3. **Authentication**: Use JWT tokens, never store passwords in plaintext
4. **Authorization**: Check user permissions before data access
5. **Audit Trail**: Log all sensitive actions to `audit_logs`
6. **Evidence Immutability**: Enforce `is_immutable` flag on approved evidence

### Reporting Security Vulnerabilities

**Do NOT open public issues for security vulnerabilities.**

Instead, email security@compliance-os.com with:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if applicable)

We will acknowledge within 48 hours and provide a timeline for fix.

## Documentation

### When to Update Documentation

Update documentation when:
- Adding new features
- Changing APIs
- Modifying configuration
- Adding environment variables
- Changing deployment process

### Documentation Files to Update

- `README.md` - For user-facing changes
- `CLAUDE.md` - For developer workflow changes
- `ARCHITECTURE.md` - For architectural changes
- API docs - For endpoint changes
- Inline comments - For complex code logic

## Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Open a GitHub Issue with the bug template
- **Feature Requests**: Open a GitHub Issue with the feature template
- **Security Issues**: Email security@compliance-os.com

## Recognition

Contributors will be recognized in:
- CHANGELOG.md (for each release)
- GitHub contributors page
- Annual contributor spotlight

---

**Remember**: "If it cannot stand up to an auditor, it does not ship." 🎯

Thank you for contributing to Compliance OS!
