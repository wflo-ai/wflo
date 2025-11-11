# Phase 5: Security Hardening - Implementation Plan

**Status**: Not Started
**Priority**: High (Production Blocker)
**Estimated Effort**: 3-5 weeks
**Target Completion**: Q2 2025

---

## Overview

Phase 5 focuses on hardening Wflo's security posture to make it production-ready. This includes securing the sandbox execution environment, implementing security scanning, adding audit logging, and performing security assessments.

### Objectives

1. ✅ Prevent malicious code execution in sandboxes
2. ✅ Detect vulnerabilities in dependencies and Docker images
3. ✅ Provide complete audit trail for compliance (SOC2, HIPAA)
4. ✅ Identify and fix security vulnerabilities before production
5. ✅ Establish security best practices and guidelines

### Success Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Container vulnerabilities | 0 critical, < 5 high | Unknown |
| Dependency vulnerabilities | 0 critical, < 10 high | Unknown |
| Security test coverage | > 90% | 0% |
| Audit log coverage | 100% of sensitive operations | 0% |
| Penetration test score | > 85/100 | Not tested |

---

## Phase 5 Components

### 1. Container Image Scanning 🔍

**Priority**: High
**Effort**: 1 week
**Dependencies**: Docker images must be built

#### Objectives
- Scan all Docker images for vulnerabilities
- Automate scanning in CI/CD pipeline
- Block deployment of images with critical vulnerabilities
- Maintain vulnerability database

#### Tools Evaluation

##### Option A: Trivy (Recommended)
**Pros**:
- Open source and free
- Fast scanning (< 30 seconds)
- Detects OS packages, language dependencies, and IaC misconfigurations
- CI/CD friendly
- Active community

**Cons**:
- Requires regular database updates
- Some false positives

**Example**:
```bash
# Install Trivy
brew install trivy  # macOS
apt-get install trivy  # Ubuntu

# Scan Docker image
trivy image wflo/runtime:python3.11

# Scan with severity filtering
trivy image --severity HIGH,CRITICAL wflo/runtime:python3.11

# Exit with error if vulnerabilities found
trivy image --exit-code 1 --severity CRITICAL wflo/runtime:python3.11
```

##### Option B: Snyk
**Pros**:
- Excellent UI and reporting
- Developer-friendly
- Good integrations

**Cons**:
- Paid product (free tier limited)
- Slower than Trivy

##### Option C: Clair
**Pros**:
- CNCF project
- API-first design

**Cons**:
- Complex setup
- Requires separate server

#### Implementation Plan

**Week 1: Setup and Integration**

1. **Install Trivy locally** (1 hour)
```bash
# macOS
brew install trivy

# Linux
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
sudo apt-get update
sudo apt-get install trivy

# Update vulnerability database
trivy image --download-db-only
```

2. **Scan existing images** (2 hours)
```bash
# Scan all Wflo images
for image in $(docker images --format "{{.Repository}}:{{.Tag}}" | grep wflo); do
  echo "Scanning $image..."
  trivy image --severity HIGH,CRITICAL $image
done

# Generate report
trivy image --format json --output trivy-report.json wflo/runtime:python3.11
```

3. **Create scanning script** (2 hours)

Create `scripts/scan_images.sh`:
```bash
#!/bin/bash
set -e

SEVERITY="HIGH,CRITICAL"
EXIT_CODE=1

echo "🔍 Scanning Wflo Docker images for vulnerabilities..."

# Update Trivy database
echo "Updating Trivy database..."
trivy image --download-db-only

# Images to scan
IMAGES=(
  "wflo/runtime:python3.11"
  "wflo/runtime:python3.12"
  "wflo/runtime:javascript"
  # Add more as needed
)

FAILED=0

for image in "${IMAGES[@]}"; do
  echo ""
  echo "Scanning $image..."

  if trivy image \
    --severity $SEVERITY \
    --exit-code $EXIT_CODE \
    --no-progress \
    $image; then
    echo "✅ $image: No critical vulnerabilities"
  else
    echo "❌ $image: Vulnerabilities found"
    FAILED=$((FAILED + 1))
  fi
done

echo ""
if [ $FAILED -eq 0 ]; then
  echo "✅ All images passed security scan"
  exit 0
else
  echo "❌ $FAILED image(s) failed security scan"
  exit 1
fi
```

```bash
chmod +x scripts/scan_images.sh
./scripts/scan_images.sh
```

4. **Add to CI/CD pipeline** (2 hours)

Update `.github/workflows/security.yml`:
```yaml
name: Security Scanning

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    # Run daily at 2 AM UTC
    - cron: '0 2 * * *'

jobs:
  container-scan:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Build Docker images
        run: |
          docker build -t wflo/runtime:python3.11 -f docker/Dockerfile.python311 .

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'wflo/runtime:python3.11'
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'HIGH,CRITICAL'

      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'

      - name: Fail on critical vulnerabilities
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'wflo/runtime:python3.11'
          exit-code: '1'
          severity: 'CRITICAL'
```

5. **Document remediation process** (1 hour)

Create `docs/security/vulnerability-remediation.md`:
```markdown
# Vulnerability Remediation Process

## When a vulnerability is detected

1. **Assess severity**: Critical > High > Medium > Low
2. **Check exploitability**: Is it actually exploitable in our context?
3. **Identify fix**: Update package, apply patch, or implement workaround
4. **Test fix**: Ensure it doesn't break functionality
5. **Deploy**: Release patched version
6. **Document**: Add to security changelog

## Common fixes

### OS package vulnerabilities
```bash
# Update base image
FROM python:3.11-slim  # Latest patch version

# Or explicitly update packages
RUN apt-get update && apt-get upgrade -y
```

### Python package vulnerabilities
```bash
# Update specific package
poetry update package-name

# Or pin to safe version
poetry add "package-name>=1.2.3"
```

## Exceptions

If a vulnerability cannot be fixed:
1. Document why (no fix available, false positive, not exploitable)
2. Add to `.trivyignore` with expiration date
3. Implement compensating controls
4. Track for future resolution
```

**Deliverables**:
- ✅ Trivy installed and configured
- ✅ Scanning script for all images
- ✅ CI/CD integration
- ✅ Remediation documentation
- ✅ Initial vulnerability report

---

### 2. gVisor Runtime Evaluation 🛡️

**Priority**: Medium
**Effort**: 1.5 weeks
**Dependencies**: Sandbox tests passing

#### What is gVisor?

gVisor is a sandboxing technology that provides an additional layer of isolation between containers and the host kernel. It implements a user-space kernel that intercepts and handles system calls, preventing malicious code from directly accessing the host.

**Security Benefits**:
- Kernel-level attack surface reduced by ~80%
- Prevents container breakout exploits
- Limits syscall access to safe subset
- Protects against kernel vulnerabilities

**Trade-offs**:
- ~10-30% performance overhead
- Not all syscalls supported (mostly POSIX)
- More complex setup

#### Implementation Plan

**Week 2-3: Evaluation and Testing**

1. **Install gVisor** (1 hour)

```bash
# Install runsc (gVisor runtime)
(
  set -e
  ARCH=$(uname -m)
  URL=https://storage.googleapis.com/gvisor/releases/release/latest/${ARCH}
  wget ${URL}/runsc ${URL}/runsc.sha512 \
    ${URL}/containerd-shim-runsc-v1 ${URL}/containerd-shim-runsc-v1.sha512
  sha512sum -c runsc.sha512 \
    -c containerd-shim-runsc-v1.sha512
  rm -f *.sha512
  chmod a+rx runsc containerd-shim-runsc-v1
  sudo mv runsc containerd-shim-runsc-v1 /usr/local/bin
)

# Configure Docker to use gVisor
sudo mkdir -p /etc/docker
cat <<EOF | sudo tee /etc/docker/daemon.json
{
  "runtimes": {
    "runsc": {
      "path": "/usr/local/bin/runsc"
    }
  }
}
EOF

sudo systemctl restart docker
```

2. **Test basic functionality** (2 hours)

```bash
# Run container with gVisor
docker run --runtime=runsc --rm python:3.11-slim python -c "print('Hello from gVisor')"

# Test Wflo sandbox
docker run --runtime=runsc --rm wflo/runtime:python3.11 \
  python -c "import os; print(os.listdir('/'))"
```

3. **Performance benchmarking** (4 hours)

Create `scripts/benchmark_gvisor.py`:
```python
#!/usr/bin/env python3
"""Benchmark gVisor vs runc performance for sandbox operations."""

import asyncio
import time
from statistics import mean, stdev

async def run_sandbox_task(runtime: str, code: str):
    """Run code in sandbox with specified runtime."""
    start = time.time()

    proc = await asyncio.create_subprocess_exec(
        'docker', 'run', '--runtime', runtime, '--rm',
        'wflo/runtime:python3.11',
        'python', '-c', code,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    await proc.communicate()
    return time.time() - start

async def benchmark():
    """Run benchmarks comparing runc and runsc."""

    test_cases = [
        ("Simple print", "print('Hello')"),
        ("File I/O", "with open('/tmp/test.txt', 'w') as f: f.write('test' * 1000)"),
        ("CPU-bound", "sum(i**2 for i in range(10000))"),
        ("Import libraries", "import json, datetime, math"),
    ]

    results = {}

    for name, code in test_cases:
        print(f"\n🔬 Benchmarking: {name}")

        runc_times = []
        runsc_times = []

        # Run each test 10 times
        for i in range(10):
            # Test with runc (default)
            t = await run_sandbox_task('runc', code)
            runc_times.append(t)

            # Test with runsc (gVisor)
            t = await run_sandbox_task('runsc', code)
            runsc_times.append(t)

            print(f"  Run {i+1}/10: runc={runc_times[-1]:.3f}s, runsc={runsc_times[-1]:.3f}s")

        runc_avg = mean(runc_times)
        runsc_avg = mean(runsc_times)
        overhead = ((runsc_avg - runc_avg) / runc_avg) * 100

        results[name] = {
            'runc': {'mean': runc_avg, 'stdev': stdev(runc_times)},
            'runsc': {'mean': runsc_avg, 'stdev': stdev(runsc_times)},
            'overhead_%': overhead,
        }

        print(f"  📊 Results:")
        print(f"    runc:  {runc_avg:.3f}s ± {stdev(runc_times):.3f}s")
        print(f"    runsc: {runsc_avg:.3f}s ± {stdev(runsc_times):.3f}s")
        print(f"    Overhead: {overhead:+.1f}%")

    # Summary
    print("\n" + "="*60)
    print("📈 SUMMARY")
    print("="*60)

    for name, data in results.items():
        print(f"{name:20s}: {data['overhead_%']:+6.1f}% overhead")

    avg_overhead = mean([r['overhead_%'] for r in results.values()])
    print(f"\n{'Average overhead':20s}: {avg_overhead:+6.1f}%")

    if avg_overhead < 20:
        print("\n✅ gVisor overhead is acceptable (< 20%)")
    else:
        print("\n⚠️  gVisor overhead is significant (> 20%)")

if __name__ == '__main__':
    asyncio.run(benchmark())
```

```bash
chmod +x scripts/benchmark_gvisor.py
python scripts/benchmark_gvisor.py
```

4. **Compatibility testing** (4 hours)

Test all sandbox features work with gVisor:
```bash
# Run sandbox tests with gVisor
SANDBOX_RUNTIME=runsc poetry run pytest tests/integration/test_sandbox.py -v

# Test specific features
docker run --runtime=runsc --rm wflo/runtime:python3.11 python -c "
import subprocess
import socket
import os
import sys

# Test subprocess
subprocess.run(['echo', 'test'])

# Test network (if enabled)
try:
    socket.gethostbyname('google.com')
    print('Network: OK')
except:
    print('Network: BLOCKED')

# Test file system
os.makedirs('/tmp/test', exist_ok=True)
with open('/tmp/test/file.txt', 'w') as f:
    f.write('test')
print('File system: OK')
"
```

5. **Update sandbox runtime** (2 hours)

Modify `src/wflo/sandbox/runtime.py`:
```python
class DockerSandbox:
    def __init__(
        self,
        image: str = "wflo/runtime:python3.11",
        timeout: int = 60,
        memory_limit: str = "512m",
        cpu_limit: float = 1.0,
        network_disabled: bool = True,
        use_gvisor: bool = True,  # NEW: Enable gVisor by default
    ):
        self.image = image
        self.timeout = timeout
        self.memory_limit = memory_limit
        self.cpu_limit = cpu_limit
        self.network_disabled = network_disabled
        self.use_gvisor = use_gvisor

    async def execute(self, code: str, language: str = "python") -> dict:
        """Execute code in sandboxed container."""

        container_config = {
            'image': self.image,
            'detach': True,
            'mem_limit': self.memory_limit,
            'nano_cpus': int(self.cpu_limit * 1e9),
            'network_disabled': self.network_disabled,
            'runtime': 'runsc' if self.use_gvisor else 'runc',  # NEW
            # ... rest of config
        }

        # Rest of implementation...
```

6. **Configuration and documentation** (1 hour)

Add to `wflo/config/settings.py`:
```python
class Settings(BaseSettings):
    # ... existing settings

    # Sandbox security
    sandbox_use_gvisor: bool = Field(
        default=True,
        description="Use gVisor for enhanced sandbox security"
    )
    sandbox_gvisor_platform: str = Field(
        default="systrap",
        description="gVisor platform: systrap (faster) or kvm (more secure)"
    )
```

Update `INFRASTRUCTURE.md`:
```markdown
### gVisor Setup (Optional, Recommended for Production)

gVisor provides enhanced security for sandbox execution.

**Install**:
```bash
# See scripts/install_gvisor.sh for automated setup
./scripts/install_gvisor.sh

# Or manual install
wget https://storage.googleapis.com/gvisor/releases/release/latest/x86_64/runsc
chmod +x runsc
sudo mv runsc /usr/local/bin/
```

**Configure**:
```bash
# Enable in settings
SANDBOX_USE_GVISOR=true
SANDBOX_GVISOR_PLATFORM=systrap  # or kvm for more isolation
```

**Verify**:
```bash
docker run --runtime=runsc --rm wflo/runtime:python3.11 \
  python -c "print('gVisor is working')"
```
```

**Decision Criteria**:

| Criterion | Recommendation |
|-----------|----------------|
| Performance overhead < 20% | ✅ Enable gVisor |
| All sandbox tests pass | ✅ Enable gVisor |
| Production environment | ✅ Enable gVisor |
| Development/testing only | ⚠️ Optional |

**Deliverables**:
- ✅ gVisor installed and tested
- ✅ Performance benchmarks
- ✅ Compatibility report
- ✅ Integration in sandbox runtime
- ✅ Documentation and configuration
- ✅ Recommendation (enable/disable)

---

### 3. Security Audit Logging 📝

**Priority**: High (Compliance requirement)
**Effort**: 1 week
**Dependencies**: None

#### Objectives
- Log all security-relevant events
- Tamper-proof audit trail
- Compliance with SOC2, HIPAA, GDPR
- Efficient storage and retrieval
- Real-time alerting on suspicious activity

#### Events to Audit

**Authentication & Authorization**:
- User login/logout
- Failed authentication attempts
- Permission changes
- API key creation/rotation
- Token issuance/revocation

**Workflow Operations**:
- Workflow creation/modification/deletion
- Workflow execution start/stop
- Approval requests/responses
- Budget changes
- Policy modifications

**Data Access**:
- Sensitive data reads
- Data exports
- Database queries on sensitive tables

**Administrative Actions**:
- User management (create/delete/modify)
- Configuration changes
- Infrastructure changes
- Security setting modifications

**Sandbox Operations**:
- Code execution attempts
- Resource limit violations
- Network access attempts
- File system modifications outside allowed paths

#### Implementation

**Week 3: Audit Logging System**

1. **Define audit log schema** (2 hours)

Create `src/wflo/observability/audit.py`:
```python
"""Security audit logging."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class AuditEventType(str, Enum):
    """Types of auditable events."""

    # Authentication
    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout"
    AUTH_FAILED = "auth.failed"
    AUTH_TOKEN_CREATED = "auth.token.created"
    AUTH_TOKEN_REVOKED = "auth.token.revoked"

    # Authorization
    AUTHZ_PERMISSION_GRANTED = "authz.permission.granted"
    AUTHZ_PERMISSION_DENIED = "authz.permission.denied"
    AUTHZ_ROLE_ASSIGNED = "authz.role.assigned"

    # Workflows
    WORKFLOW_CREATED = "workflow.created"
    WORKFLOW_MODIFIED = "workflow.modified"
    WORKFLOW_DELETED = "workflow.deleted"
    WORKFLOW_EXECUTED = "workflow.executed"
    WORKFLOW_APPROVED = "workflow.approved"
    WORKFLOW_REJECTED = "workflow.rejected"

    # Data Access
    DATA_READ = "data.read"
    DATA_EXPORTED = "data.exported"

    # Administrative
    ADMIN_USER_CREATED = "admin.user.created"
    ADMIN_USER_DELETED = "admin.user.deleted"
    ADMIN_CONFIG_CHANGED = "admin.config.changed"

    # Sandbox
    SANDBOX_EXECUTION = "sandbox.execution"
    SANDBOX_VIOLATION = "sandbox.violation"
    SANDBOX_NETWORK_ATTEMPT = "sandbox.network.attempt"

    # Security
    SECURITY_VULNERABILITY_DETECTED = "security.vulnerability.detected"
    SECURITY_INCIDENT = "security.incident"


class AuditSeverity(str, Enum):
    """Severity levels for audit events."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditEvent(BaseModel):
    """Audit log event."""

    # Event identification
    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: AuditEventType
    severity: AuditSeverity = AuditSeverity.INFO

    # Actor (who performed the action)
    actor_id: Optional[str] = None
    actor_type: str = "user"  # user, system, service
    actor_ip: Optional[str] = None

    # Target (what was acted upon)
    resource_type: Optional[str] = None  # workflow, user, config
    resource_id: Optional[str] = None

    # Action details
    action: str
    status: str = "success"  # success, failure, denied

    # Context
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None
    session_id: Optional[str] = None

    # Additional data
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Security
    signature: Optional[str] = None  # HMAC signature for tamper detection

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class AuditLogger:
    """Centralized audit logging."""

    def __init__(self):
        """Initialize audit logger."""
        from wflo.observability import get_logger
        self.logger = get_logger("audit")

    async def log(self, event: AuditEvent) -> None:
        """Log an audit event.

        Args:
            event: Audit event to log
        """
        # Add signature for tamper detection
        event.signature = self._sign_event(event)

        # Log to structured logging
        self.logger.info(
            "audit_event",
            event_id=event.id,
            event_type=event.event_type,
            severity=event.severity,
            actor_id=event.actor_id,
            resource_type=event.resource_type,
            resource_id=event.resource_id,
            action=event.action,
            status=event.status,
            metadata=event.metadata,
        )

        # Store in database for long-term retention
        await self._store_event(event)

        # Send to Kafka for real-time processing
        await self._publish_event(event)

        # Alert on critical events
        if event.severity == AuditSeverity.CRITICAL:
            await self._send_alert(event)

    def _sign_event(self, event: AuditEvent) -> str:
        """Create HMAC signature for event."""
        import hashlib
        import hmac
        from wflo.config import get_settings

        settings = get_settings()
        secret = settings.audit_signing_key.get_secret_value()

        # Create canonical representation
        canonical = f"{event.id}|{event.timestamp.isoformat()}|{event.event_type}|{event.action}"

        # Generate HMAC
        signature = hmac.new(
            secret.encode(),
            canonical.encode(),
            hashlib.sha256
        ).hexdigest()

        return signature

    async def _store_event(self, event: AuditEvent) -> None:
        """Store event in database."""
        from wflo.db.engine import get_session
        from wflo.db.models import AuditLogModel

        async for session in get_session():
            audit_record = AuditLogModel(
                id=event.id,
                timestamp=event.timestamp,
                event_type=event.event_type,
                severity=event.severity,
                actor_id=event.actor_id,
                actor_type=event.actor_type,
                actor_ip=event.actor_ip,
                resource_type=event.resource_type,
                resource_id=event.resource_id,
                action=event.action,
                status=event.status,
                request_id=event.request_id,
                correlation_id=event.correlation_id,
                metadata=event.metadata,
                signature=event.signature,
            )
            session.add(audit_record)
            await session.commit()

    async def _publish_event(self, event: AuditEvent) -> None:
        """Publish event to Kafka for real-time processing."""
        from wflo.events import get_producer

        producer = get_producer()
        await producer.send(
            topic="audit.events",
            key=event.id,
            value=event.dict(),
        )

    async def _send_alert(self, event: AuditEvent) -> None:
        """Send alert for critical events."""
        # TODO: Implement alerting (Slack, PagerDuty, etc.)
        self.logger.critical(
            "critical_audit_event",
            event_id=event.id,
            event_type=event.event_type,
            action=event.action,
        )


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


async def audit_log(
    event_type: AuditEventType,
    action: str,
    actor_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    status: str = "success",
    severity: AuditSeverity = AuditSeverity.INFO,
    metadata: Optional[dict[str, Any]] = None,
) -> None:
    """Convenience function for logging audit events.

    Args:
        event_type: Type of event
        action: Description of action performed
        actor_id: ID of actor performing action
        resource_type: Type of resource acted upon
        resource_id: ID of resource
        status: success, failure, or denied
        severity: Event severity
        metadata: Additional context
    """
    logger = get_audit_logger()

    event = AuditEvent(
        event_type=event_type,
        action=action,
        actor_id=actor_id,
        resource_type=resource_type,
        resource_id=resource_id,
        status=status,
        severity=severity,
        metadata=metadata or {},
    )

    await logger.log(event)
```

2. **Create audit log database model** (1 hour)

Add to `src/wflo/db/models.py`:
```python
class AuditLogModel(Base):
    """Audit log for security and compliance."""

    __tablename__ = "audit_logs"

    id = mapped_column(String(36), primary_key=True)
    timestamp = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    # Event
    event_type = mapped_column(String(100), nullable=False, index=True)
    severity = mapped_column(String(20), nullable=False, index=True)

    # Actor
    actor_id = mapped_column(String(100), index=True)
    actor_type = mapped_column(String(50))
    actor_ip = mapped_column(String(45))  # IPv6

    # Resource
    resource_type = mapped_column(String(50), index=True)
    resource_id = mapped_column(String(100), index=True)

    # Action
    action = mapped_column(Text, nullable=False)
    status = mapped_column(String(20), nullable=False, index=True)

    # Context
    request_id = mapped_column(String(36), index=True)
    correlation_id = mapped_column(String(36), index=True)
    session_id = mapped_column(String(100))

    # Data
    metadata = mapped_column(JSON)

    # Security
    signature = mapped_column(String(64), nullable=False)  # HMAC-SHA256

    # Indexes
    __table_args__ = (
        Index('idx_audit_timestamp_type', 'timestamp', 'event_type'),
        Index('idx_audit_actor_resource', 'actor_id', 'resource_type'),
    )
```

Create migration:
```bash
poetry run alembic revision --autogenerate -m "add audit logs table"
poetry run alembic upgrade head
```

3. **Integrate audit logging** (4 hours)

Add audit calls throughout codebase:

`src/wflo/temporal/workflows.py`:
```python
from wflo.observability.audit import audit_log, AuditEventType, AuditSeverity

@workflow.defn
class WfloWorkflow:
    @workflow.run
    async def run(self, workflow_id: str, inputs: dict, max_cost_usd: float | None = None):
        # Audit workflow execution start
        await audit_log(
            event_type=AuditEventType.WORKFLOW_EXECUTED,
            action=f"Started workflow execution",
            resource_type="workflow",
            resource_id=workflow_id,
            metadata={
                "inputs": inputs,
                "max_cost_usd": max_cost_usd,
            },
        )

        try:
            # Execute workflow...
            result = await self._execute(workflow_id, inputs, max_cost_usd)

            # Audit success
            await audit_log(
                event_type=AuditEventType.WORKFLOW_EXECUTED,
                action=f"Completed workflow execution",
                resource_type="workflow",
                resource_id=workflow_id,
                status="success",
                metadata={"result": result},
            )

            return result

        except Exception as e:
            # Audit failure
            await audit_log(
                event_type=AuditEventType.WORKFLOW_EXECUTED,
                action=f"Failed workflow execution",
                resource_type="workflow",
                resource_id=workflow_id,
                status="failure",
                severity=AuditSeverity.ERROR,
                metadata={"error": str(e)},
            )
            raise
```

`src/wflo/sandbox/runtime.py`:
```python
async def execute(self, code: str, language: str = "python") -> dict:
    # Audit sandbox execution
    await audit_log(
        event_type=AuditEventType.SANDBOX_EXECUTION,
        action=f"Executing {language} code in sandbox",
        resource_type="sandbox",
        metadata={
            "language": language,
            "code_length": len(code),
            "image": self.image,
        },
    )

    try:
        result = await self._execute_in_container(code)

        # Check for violations
        if result.get('exit_code') != 0:
            await audit_log(
                event_type=AuditEventType.SANDBOX_VIOLATION,
                action="Sandbox execution failed",
                resource_type="sandbox",
                severity=AuditSeverity.WARNING,
                metadata={
                    "exit_code": result['exit_code'],
                    "stderr": result.get('stderr', '')[:500],
                },
            )

        return result

    except Exception as e:
        await audit_log(
            event_type=AuditEventType.SANDBOX_VIOLATION,
            action="Sandbox execution error",
            resource_type="sandbox",
            severity=AuditSeverity.ERROR,
            metadata={"error": str(e)},
        )
        raise
```

4. **Audit log query API** (2 hours)

Create `src/wflo/observability/audit_queries.py`:
```python
"""Audit log queries for compliance and forensics."""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from wflo.db.models import AuditLogModel
from wflo.observability.audit import AuditEventType, AuditSeverity


async def get_audit_logs(
    session: AsyncSession,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    event_type: Optional[AuditEventType] = None,
    actor_id: Optional[str] = None,
    resource_id: Optional[str] = None,
    severity: Optional[AuditSeverity] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[AuditLogModel]:
    """Query audit logs with filters."""

    query = select(AuditLogModel)

    if start_time:
        query = query.where(AuditLogModel.timestamp >= start_time)
    if end_time:
        query = query.where(AuditLogModel.timestamp <= end_time)
    if event_type:
        query = query.where(AuditLogModel.event_type == event_type)
    if actor_id:
        query = query.where(AuditLogModel.actor_id == actor_id)
    if resource_id:
        query = query.where(AuditLogModel.resource_id == resource_id)
    if severity:
        query = query.where(AuditLogModel.severity == severity)

    query = query.order_by(AuditLogModel.timestamp.desc())
    query = query.limit(limit).offset(offset)

    result = await session.execute(query)
    return result.scalars().all()


async def get_audit_summary(
    session: AsyncSession,
    start_time: datetime,
    end_time: datetime,
) -> dict:
    """Get audit log summary for time period."""

    # Count by event type
    event_counts = await session.execute(
        select(
            AuditLogModel.event_type,
            func.count(AuditLogModel.id).label('count')
        )
        .where(AuditLogModel.timestamp >= start_time)
        .where(AuditLogModel.timestamp <= end_time)
        .group_by(AuditLogModel.event_type)
    )

    # Count by severity
    severity_counts = await session.execute(
        select(
            AuditLogModel.severity,
            func.count(AuditLogModel.id).label('count')
        )
        .where(AuditLogModel.timestamp >= start_time)
        .where(AuditLogModel.timestamp <= end_time)
        .group_by(AuditLogModel.severity)
    )

    # Top actors
    top_actors = await session.execute(
        select(
            AuditLogModel.actor_id,
            func.count(AuditLogModel.id).label('count')
        )
        .where(AuditLogModel.timestamp >= start_time)
        .where(AuditLogModel.timestamp <= end_time)
        .where(AuditLogModel.actor_id.isnot(None))
        .group_by(AuditLogModel.actor_id)
        .order_by(func.count(AuditLogModel.id).desc())
        .limit(10)
    )

    return {
        'period': {
            'start': start_time,
            'end': end_time,
        },
        'event_counts': {row.event_type: row.count for row in event_counts},
        'severity_counts': {row.severity: row.count for row in severity_counts},
        'top_actors': {row.actor_id: row.count for row in top_actors},
    }


async def verify_audit_integrity(
    session: AsyncSession,
    audit_log_id: str,
) -> bool:
    """Verify audit log signature hasn't been tampered with."""

    from wflo.observability.audit import AuditLogger

    result = await session.execute(
        select(AuditLogModel).where(AuditLogModel.id == audit_log_id)
    )
    audit_log = result.scalar_one_or_none()

    if not audit_log:
        return False

    # Recreate event and check signature
    from wflo.observability.audit import AuditEvent
    event = AuditEvent(
        id=audit_log.id,
        timestamp=audit_log.timestamp,
        event_type=audit_log.event_type,
        action=audit_log.action,
    )

    logger = AuditLogger()
    expected_signature = logger._sign_event(event)

    return audit_log.signature == expected_signature
```

**Deliverables**:
- ✅ Audit logging system implemented
- ✅ Database model and migrations
- ✅ Integration in key components
- ✅ Query API for compliance reports
- ✅ Signature verification for tamper detection

---

### 4. Penetration Testing 🎯

**Priority**: Medium
**Effort**: 1-2 weeks (ongoing)
**Dependencies**: All Phase 5 components complete

#### Objectives
- Identify vulnerabilities before production
- Test security controls effectiveness
- Validate threat model assumptions
- Provide remediation recommendations

#### Scope

**In Scope**:
- Web application (if any)
- API endpoints
- Sandbox escape attempts
- Authentication/authorization
- Database security
- Infrastructure configuration

**Out of Scope**:
- Physical security
- Social engineering
- DDoS attacks
- Third-party services

#### Approach

**Week 4-5: Testing and Remediation**

1. **Automated scanning** (1 day)

```bash
# Install OWASP ZAP
docker pull zaproxy/zap-stable

# Run baseline scan
docker run -t zaproxy/zap-stable zap-baseline.py \
  -t http://localhost:8000 \
  -r zap-report.html

# Review report
open zap-report.html
```

2. **Sandbox escape testing** (2 days)

Create `tests/security/test_sandbox_escape.py`:
```python
"""Security tests for sandbox escape attempts."""

import pytest

class TestSandboxSecurity:
    """Test sandbox escape scenarios."""

    @pytest.mark.security
    async def test_cannot_access_host_filesystem(self, sandbox):
        """Ensure sandbox cannot access host files."""
        code = """
import os
# Try to read /etc/passwd from host
try:
    with open('/etc/passwd', 'r') as f:
        print(f.read())
except Exception as e:
    print(f'BLOCKED: {e}')
"""
        result = await sandbox.execute(code)
        assert 'BLOCKED' in result['stdout']
        assert '/etc/passwd' not in result['stdout']

    @pytest.mark.security
    async def test_cannot_execute_shell_commands(self, sandbox):
        """Ensure sandbox cannot execute arbitrary shell commands."""
        code = """
import subprocess
try:
    subprocess.run(['ls', '/'], capture_output=True, check=True)
    print('DANGER: Shell access')
except Exception as e:
    print(f'BLOCKED: {e}')
"""
        result = await sandbox.execute(code)
        assert 'BLOCKED' in result['stdout']

    @pytest.mark.security
    async def test_resource_limits_enforced(self, sandbox):
        """Ensure resource limits cannot be exceeded."""
        # Try to consume excessive memory
        code = """
try:
    # Try to allocate 1GB of memory
    data = bytearray(1024 * 1024 * 1024)
    print('DANGER: Memory limit bypassed')
except MemoryError:
    print('BLOCKED: Memory limit enforced')
"""
        result = await sandbox.execute(code)
        assert 'BLOCKED' in result['stdout'] or result['exit_code'] != 0

    @pytest.mark.security
    async def test_network_access_blocked(self, sandbox):
        """Ensure network access is blocked when disabled."""
        code = """
import socket
try:
    s = socket.socket()
    s.connect(('google.com', 80))
    print('DANGER: Network access')
except Exception as e:
    print(f'BLOCKED: {e}')
"""
        result = await sandbox.execute(code)
        assert 'BLOCKED' in result['stdout']
```

Run security tests:
```bash
poetry run pytest tests/security/ -v -m security
```

3. **Authentication/authorization testing** (1 day)

Test common vulnerabilities:
- SQL injection
- JWT token manipulation
- Session fixation
- Privilege escalation
- CSRF attacks

4. **Dependency vulnerability testing** (Ongoing)

```bash
# Python dependencies
poetry run safety check

# Or use pip-audit
pip-audit

# Node dependencies (if any)
npm audit

# Generate report
poetry run safety check --json > security-audit.json
```

5. **Infrastructure hardening** (1 day)

Run security benchmarks:
```bash
# Docker bench security
docker run --rm --net host --pid host --cap-add audit_control \
  -v /var/lib:/var/lib \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /usr/lib/systemd:/usr/lib/systemd \
  -v /etc:/etc \
  docker/docker-bench-security

# Review and remediate findings
```

**Deliverables**:
- ✅ Penetration test report
- ✅ Security test suite
- ✅ Vulnerability remediation plan
- ✅ Infrastructure hardening checklist

---

## Implementation Timeline

### Week 1: Container Scanning
- Day 1-2: Setup Trivy, scan images
- Day 3: Create scanning scripts
- Day 4: CI/CD integration
- Day 5: Documentation

### Week 2: gVisor Evaluation
- Day 1: Install and basic testing
- Day 2-3: Performance benchmarking
- Day 4: Compatibility testing
- Day 5: Documentation and decision

### Week 3: Audit Logging
- Day 1: Schema and models
- Day 2: Implementation
- Day 3-4: Integration
- Day 5: Testing and documentation

### Week 4-5: Penetration Testing
- Week 4: Automated scanning, sandbox testing
- Week 5: Manual testing, remediation

---

## Success Criteria

Phase 5 is complete when:

- [ ] All Docker images scanned with < 5 high-severity vulnerabilities
- [ ] gVisor evaluation complete with recommendation
- [ ] Audit logging covering 100% of sensitive operations
- [ ] Penetration testing complete with > 85/100 score
- [ ] All critical vulnerabilities remediated
- [ ] Security documentation complete
- [ ] Security tests added to CI/CD
- [ ] Team trained on security practices

---

## Maintenance

**Ongoing Activities** (after Phase 5):

1. **Weekly**: Review audit logs for suspicious activity
2. **Weekly**: Scan new Docker images
3. **Monthly**: Review and update threat model
4. **Monthly**: Dependency vulnerability scanning
5. **Quarterly**: Security training for team
6. **Annually**: Full penetration testing
7. **Continuously**: Monitor security advisories

---

## Resources

### Tools
- **Trivy**: https://github.com/aquasecurity/trivy
- **gVisor**: https://gvisor.dev/
- **OWASP ZAP**: https://www.zaproxy.org/
- **Safety**: https://pyup.io/safety/
- **Docker Bench**: https://github.com/docker/docker-bench-security

### Documentation
- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **CIS Docker Benchmark**: https://www.cisecurity.org/benchmark/docker
- **NIST Cybersecurity Framework**: https://www.nist.gov/cyberframework

### Training
- **Security training**: Consider Pluralsight, Udemy, or SecurityTube
- **CTF practice**: HackTheBox, TryHackMe
- **Certifications**: CEH, OSCP, or cloud security certs

---

## Next Steps

1. Review this plan with team
2. Allocate resources (developers, security experts)
3. Set timeline for Phase 5
4. Begin with highest priority items (container scanning, audit logging)
5. Track progress using project management tool
6. Schedule regular security reviews

---

**Questions or concerns?** Contact the security team or review this document with stakeholders before beginning implementation.
