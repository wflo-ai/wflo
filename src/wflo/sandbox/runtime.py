"""Sandbox runtime for executing code in isolated Docker containers.

This module provides the SandboxRuntime class for secure code execution
with resource limits, network isolation, and security hardening.
"""

import asyncio
import json
import logging
import tarfile
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any

import aiodocker
from aiodocker.containers import DockerContainer

from wflo.config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of code execution in sandbox.

    Attributes:
        exit_code: Container exit code (0 = success)
        stdout: Standard output from execution
        stderr: Standard error from execution
        duration_seconds: Execution duration in seconds
        sandbox_id: Container ID
        started_at: Execution start time
        completed_at: Execution completion time
    """

    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    sandbox_id: str
    started_at: datetime
    completed_at: datetime

    @property
    def success(self) -> bool:
        """Check if execution was successful."""
        return self.exit_code == 0


class SandboxRuntime:
    """Runtime for executing code in isolated Docker containers.

    This class provides secure, isolated code execution with:
    - Resource limits (CPU, memory)
    - Network isolation
    - Timeout enforcement
    - Security hardening (seccomp, AppArmor)
    - Automatic cleanup

    Example:
        async with SandboxRuntime() as runtime:
            result = await runtime.execute_code(
                code="print('Hello, World!')",
                timeout_seconds=30,
            )
            print(result.stdout)  # "Hello, World!"
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize sandbox runtime.

        Args:
            settings: Application settings (optional)
        """
        self.settings = settings or get_settings()
        self.docker: aiodocker.Docker | None = None
        self._containers: set[str] = set()

    async def __aenter__(self) -> "SandboxRuntime":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.cleanup()
        await self.close()

    async def connect(self) -> None:
        """Connect to Docker daemon."""
        if self.docker is None:
            self.docker = aiodocker.Docker()
            logger.info("Connected to Docker daemon")

    async def close(self) -> None:
        """Close Docker connection."""
        if self.docker is not None:
            await self.docker.close()
            self.docker = None
            logger.info("Closed Docker connection")

    async def execute_code(
        self,
        code: str,
        timeout_seconds: int | None = None,
        language: str = "python",
        allow_network: bool | None = None,
        cpu_limit: float | None = None,
        memory_limit: str | None = None,
    ) -> ExecutionResult:
        """Execute code in an isolated sandbox.

        Args:
            code: Code to execute
            timeout_seconds: Maximum execution time (default: from settings)
            language: Programming language (currently only 'python')
            allow_network: Allow network access (default: from settings)
            cpu_limit: CPU limit in cores (default: from settings)
            memory_limit: Memory limit (e.g., "512m", default: from settings)

        Returns:
            ExecutionResult: Execution result with stdout, stderr, exit code

        Raises:
            TimeoutError: If execution exceeds timeout
            RuntimeError: If container creation or execution fails
        """
        if self.docker is None:
            await self.connect()

        # Use settings defaults if not specified
        timeout_seconds = timeout_seconds or self.settings.sandbox_timeout_seconds
        allow_network = (
            allow_network
            if allow_network is not None
            else self.settings.sandbox_network_access
        )
        cpu_limit = cpu_limit or self.settings.sandbox_cpu_limit
        memory_limit = memory_limit or self.settings.sandbox_memory_limit

        logger.info(
            f"Executing code in sandbox",
            extra={
                "timeout": timeout_seconds,
                "language": language,
                "allow_network": allow_network,
                "cpu_limit": cpu_limit,
                "memory_limit": memory_limit,
            },
        )

        started_at = datetime.now(timezone.utc)
        container = None  # Initialize to avoid UnboundLocalError in finally block

        try:
            # Create and execute container
            container = await self._create_container(
                code=code,
                language=language,
                allow_network=allow_network,
                cpu_limit=cpu_limit,
                memory_limit=memory_limit,
            )

            # Execute with timeout
            try:
                exit_code, stdout, stderr = await asyncio.wait_for(
                    self._run_container(container),
                    timeout=timeout_seconds,
                )
            except asyncio.TimeoutError:
                logger.warning(
                    f"Container {container.id} exceeded timeout of {timeout_seconds}s"
                )
                # Kill container on timeout
                await container.kill()
                raise TimeoutError(
                    f"Execution exceeded timeout of {timeout_seconds} seconds"
                )

            completed_at = datetime.now(timezone.utc)
            duration = (completed_at - started_at).total_seconds()

            result = ExecutionResult(
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                duration_seconds=duration,
                sandbox_id=container.id,
                started_at=started_at,
                completed_at=completed_at,
            )

            logger.info(
                f"Execution completed",
                extra={
                    "sandbox_id": container.id,
                    "exit_code": exit_code,
                    "duration": duration,
                },
            )

            return result

        finally:
            # Cleanup container if it was created
            if container is not None and container.id in self._containers:
                await self._cleanup_container(container)

    async def _create_container(
        self,
        code: str,
        language: str,
        allow_network: bool,
        cpu_limit: float,
        memory_limit: str,
    ) -> DockerContainer:
        """Create a Docker container for code execution.

        Args:
            code: Code to execute
            language: Programming language
            allow_network: Whether to allow network access
            cpu_limit: CPU limit in cores
            memory_limit: Memory limit (e.g., "512m")

        Returns:
            DockerContainer: Created container

        Raises:
            RuntimeError: If container creation fails
        """
        if self.docker is None:
            raise RuntimeError("Docker client not connected")

        # Determine image and command based on language
        if language == "python":
            image = self.settings.sandbox_image
            cmd = ["python", "-c", code]
        else:
            raise ValueError(f"Unsupported language: {language}")

        # Ensure image exists (pull if needed)
        try:
            await self.docker.images.inspect(image)
        except aiodocker.DockerError:
            logger.info(f"Pulling image: {image}")
            await self.docker.images.pull(image)

        # Container configuration
        config = {
            "Image": image,
            "Cmd": cmd,
            "HostConfig": {
                "Memory": self._parse_memory_limit(memory_limit),
                "MemorySwap": self._parse_memory_limit(memory_limit),  # No swap
                "NanoCpus": int(cpu_limit * 1_000_000_000),  # Convert to nano CPUs
                "PidsLimit": 100,  # Limit number of processes
                "ReadonlyRootfs": False,  # Allow writes to /tmp
                "NetworkMode": "none" if not allow_network else "bridge",
                "SecurityOpt": [
                    "no-new-privileges",  # Prevent privilege escalation
                ],
                # Limit capabilities
                "CapDrop": ["ALL"],
                "CapAdd": [],  # No capabilities by default
            },
            "NetworkingConfig": {
                "EndpointsConfig": {} if allow_network else {},
            },
            "User": "1000:1000",  # Non-root user
            "WorkingDir": "/workspace",
        }

        # Create container
        try:
            container = await self.docker.containers.create(config=config)
            self._containers.add(container.id)
            logger.debug(f"Created container: {container.id}")
            return container
        except Exception as e:
            logger.error(f"Failed to create container: {e}")
            raise RuntimeError(f"Failed to create container: {e}") from e

    async def _run_container(
        self, container: DockerContainer
    ) -> tuple[int, str, str]:
        """Run container and collect output.

        Args:
            container: Container to run

        Returns:
            tuple: (exit_code, stdout, stderr)
        """
        # Start container
        await container.start()
        logger.debug(f"Started container: {container.id}")

        # Wait for completion
        result = await container.wait()
        exit_code = result["StatusCode"]

        # Get logs
        logs = await container.log(stdout=True, stderr=True)

        # Separate stdout and stderr
        stdout_lines = []
        stderr_lines = []

        for line in logs:
            # aiodocker returns logs with stream prefix
            if isinstance(line, bytes):
                line = line.decode("utf-8", errors="replace")
            stdout_lines.append(line)

        stdout = "".join(stdout_lines)
        stderr = ""  # aiodocker combines stdout/stderr, separate if needed

        logger.debug(
            f"Container {container.id} exited with code {exit_code}",
            extra={
                "stdout_length": len(stdout),
                "stderr_length": len(stderr),
            },
        )

        return exit_code, stdout, stderr

    async def _cleanup_container(self, container: DockerContainer) -> None:
        """Remove container and cleanup.

        Args:
            container: Container to cleanup
        """
        try:
            await container.delete(force=True)
            self._containers.discard(container.id)
            logger.debug(f"Cleaned up container: {container.id}")
        except Exception as e:
            logger.warning(f"Failed to cleanup container {container.id}: {e}")

    async def cleanup(self) -> None:
        """Cleanup all tracked containers."""
        if self.docker is None:
            return

        logger.info(f"Cleaning up {len(self._containers)} containers")

        # Cleanup all tracked containers
        for container_id in list(self._containers):
            try:
                container = await self.docker.containers.get(container_id)
                await self._cleanup_container(container)
            except Exception as e:
                logger.warning(f"Failed to cleanup container {container_id}: {e}")
                self._containers.discard(container_id)

    @staticmethod
    def _parse_memory_limit(limit: str) -> int:
        """Parse memory limit string to bytes.

        Args:
            limit: Memory limit string (e.g., "512m", "1g", "1024k")

        Returns:
            int: Memory limit in bytes
        """
        limit = limit.lower().strip()

        multipliers = {
            "k": 1024,
            "m": 1024**2,
            "g": 1024**3,
        }

        for suffix, multiplier in multipliers.items():
            if limit.endswith(suffix):
                value = float(limit[:-1])
                return int(value * multiplier)

        # Assume bytes if no suffix
        return int(limit)
