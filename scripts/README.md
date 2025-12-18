# Utility Scripts

This directory contains helpful utility scripts for common development and operations tasks.

## Available Scripts

### `setup.sh` - Initial Project Setup
Sets up the development environment for first-time contributors.

**Prerequisites:**
- Python 3.11+
- Node.js 18+
- Docker Desktop

**Usage:**
```bash
./scripts/setup.sh
```

**What it does:**
- Checks for required prerequisites (Python, Node, Docker)
- Sets up Python virtual environment
- Installs backend dependencies
- Installs frontend dependencies
- Creates `.env` files from templates
- Provides next steps for getting started

---

### `health-check.sh` - Service Health Check
Verifies all services are running and healthy.

**Usage:**
```bash
./scripts/health-check.sh
```

**What it checks:**
- Docker container status (PostgreSQL, Redis, Backend, Celery, Frontend)
- HTTP endpoint health (Backend API, Frontend)
- Database connectivity
- Redis connectivity

**Output:**
- ✓ Green: Service is healthy
- ⚠ Yellow: Service is running but may have issues
- ✗ Red: Service is not running or unreachable

---

## Making Scripts Executable

If you encounter permission errors, make the scripts executable:

```bash
chmod +x scripts/*.sh
```

## Adding New Scripts

When adding new scripts to this directory:

1. **Use descriptive names**: `action-target.sh` (e.g., `backup-database.sh`)
2. **Add shebang**: Start with `#!/bin/bash`
3. **Use `set -e`**: Exit on error
4. **Add comments**: Explain what the script does
5. **Make executable**: `chmod +x scripts/your-script.sh`
6. **Update this README**: Document the new script

## Future Scripts (Planned)

- `seed-db.sh` - Database seeding wrapper
- `backup-db.sh` - Database backup utility
- `docker-clean.sh` - Clean Docker resources
- `run-tests.sh` - Run all tests (backend + frontend)
- `deploy.sh` - Deployment automation

## Best Practices

- Always run scripts from the project root directory
- Review script contents before running
- Keep scripts simple and focused on one task
- Use environment variables for configuration
- Handle errors gracefully
- Provide clear output messages

## Getting Help

If you encounter issues with any script:

1. Check the script output for error messages
2. Ensure all prerequisites are installed
3. Verify Docker Desktop is running
4. Check `.env` file configuration
5. Review the script code for troubleshooting

For additional help, see the main [README.md](../README.md) or open an issue on GitHub.
