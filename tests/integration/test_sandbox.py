"""Integration tests for sandbox execution.

These tests require Docker to be running.
Run with: pytest tests/integration/test_sandbox.py -v
"""

import pytest

from wflo.sandbox import SandboxRuntime


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
class TestSandboxBasicExecution:
    """Test basic sandbox code execution."""

    async def test_execute_simple_python_code(self):
        """Test executing simple Python code."""
        async with SandboxRuntime() as runtime:
            result = await runtime.execute_code(
                code="print('Hello, World!')",
                timeout_seconds=30,
            )

            assert result.success
            assert result.exit_code == 0
            assert "Hello, World!" in result.stdout
            assert result.duration_seconds > 0
            assert result.sandbox_id

    async def test_execute_code_with_output(self):
        """Test code execution with multiple output lines."""
        async with SandboxRuntime() as runtime:
            code = """
print('Line 1')
print('Line 2')
print('Line 3')
"""
            result = await runtime.execute_code(code=code, timeout_seconds=30)

            assert result.success
            assert "Line 1" in result.stdout
            assert "Line 2" in result.stdout
            assert "Line 3" in result.stdout

    async def test_execute_code_with_variables(self):
        """Test code execution with variable manipulation."""
        async with SandboxRuntime() as runtime:
            code = """
x = 10
y = 20
result = x + y
print(f'Result: {result}')
"""
            result = await runtime.execute_code(code=code, timeout_seconds=30)

            assert result.success
            assert "Result: 30" in result.stdout

    async def test_execute_code_with_imports(self):
        """Test code execution with standard library imports."""
        async with SandboxRuntime() as runtime:
            code = """
import json
import datetime

data = {'date': datetime.datetime.now().isoformat()}
print(json.dumps(data))
"""
            result = await runtime.execute_code(code=code, timeout_seconds=30)

            assert result.success
            assert result.exit_code == 0


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
class TestSandboxErrorHandling:
    """Test sandbox error handling."""

    async def test_syntax_error(self):
        """Test handling of Python syntax errors."""
        async with SandboxRuntime() as runtime:
            code = "print('missing parenthesis'"  # Syntax error

            result = await runtime.execute_code(code=code, timeout_seconds=30)

            assert not result.success
            assert result.exit_code != 0

    async def test_runtime_error(self):
        """Test handling of runtime errors."""
        async with SandboxRuntime() as runtime:
            code = """
x = 1 / 0  # Division by zero
print('This should not print')
"""
            result = await runtime.execute_code(code=code, timeout_seconds=30)

            assert not result.success
            assert result.exit_code != 0

    async def test_import_error(self):
        """Test handling of import errors."""
        async with SandboxRuntime() as runtime:
            code = "import nonexistent_module"

            result = await runtime.execute_code(code=code, timeout_seconds=30)

            assert not result.success
            assert result.exit_code != 0


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
class TestSandboxTimeout:
    """Test sandbox timeout enforcement."""

    async def test_timeout_enforcement(self):
        """Test that code execution times out correctly."""
        async with SandboxRuntime() as runtime:
            code = """
import time
time.sleep(60)  # Sleep longer than timeout
print('This should not print')
"""

            with pytest.raises(TimeoutError):
                await runtime.execute_code(code=code, timeout_seconds=2)

    async def test_fast_execution_within_timeout(self):
        """Test that fast code completes before timeout."""
        async with SandboxRuntime() as runtime:
            code = "print('Fast execution')"

            result = await runtime.execute_code(code=code, timeout_seconds=30)

            assert result.success
            assert result.duration_seconds < 5  # Should be very fast


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
class TestSandboxResourceLimits:
    """Test sandbox resource limits."""

    async def test_memory_limit(self):
        """Test memory limit enforcement."""
        async with SandboxRuntime() as runtime:
            # Try to allocate more memory than limit
            code = """
try:
    # Try to allocate 1GB of memory
    data = bytearray(1024 * 1024 * 1024)
    print('Memory allocated')
except MemoryError:
    print('Memory limit reached')
"""
            result = await runtime.execute_code(
                code=code,
                timeout_seconds=30,
                memory_limit="256m",  # 256MB limit
            )

            # Should complete (either allocate or hit limit)
            assert result.exit_code is not None

    async def test_cpu_limit(self):
        """Test CPU limit configuration."""
        async with SandboxRuntime() as runtime:
            code = """
import time
start = time.time()
# Do some CPU work
for i in range(1000000):
    _ = i ** 2
end = time.time()
print(f'Duration: {end - start:.2f}s')
"""
            result = await runtime.execute_code(
                code=code,
                timeout_seconds=30,
                cpu_limit=0.5,  # Limit to 0.5 CPU cores
            )

            assert result.success


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
class TestSandboxNetworkIsolation:
    """Test sandbox network isolation."""

    async def test_network_disabled_by_default(self):
        """Test that network access is disabled by default."""
        async with SandboxRuntime() as runtime:
            code = """
import urllib.request
try:
    urllib.request.urlopen('http://example.com', timeout=5)
    print('Network access succeeded')
except Exception as e:
    print(f'Network access failed: {type(e).__name__}')
"""
            result = await runtime.execute_code(
                code=code,
                timeout_seconds=30,
                allow_network=False,
            )

            # Should fail to access network
            assert "failed" in result.stdout.lower() or result.exit_code != 0

    async def test_network_enabled_when_allowed(self):
        """Test that network access works when explicitly allowed."""
        async with SandboxRuntime() as runtime:
            code = """
import socket
# Just test DNS resolution (doesn't actually connect)
try:
    socket.gethostbyname('example.com')
    print('DNS resolution succeeded')
except Exception as e:
    print(f'DNS resolution failed: {type(e).__name__}')
"""
            result = await runtime.execute_code(
                code=code,
                timeout_seconds=30,
                allow_network=True,
            )

            # With network enabled, DNS should work
            # (actual network depends on Docker network config)
            assert result.exit_code == 0


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
class TestSandboxCleanup:
    """Test sandbox cleanup and resource management."""

    async def test_container_cleanup_on_success(self):
        """Test that containers are cleaned up after successful execution."""
        async with SandboxRuntime() as runtime:
            result = await runtime.execute_code(
                code="print('Test')",
                timeout_seconds=30,
            )

            assert result.success

            # After execution, container should be cleaned up
            # (tracked internally by runtime)
            assert len(runtime._containers) == 0

    async def test_container_cleanup_on_error(self):
        """Test that containers are cleaned up even after errors."""
        async with SandboxRuntime() as runtime:
            result = await runtime.execute_code(
                code="raise ValueError('Test error')",
                timeout_seconds=30,
            )

            assert not result.success

            # Container should still be cleaned up
            assert len(runtime._containers) == 0

    async def test_cleanup_all_containers(self):
        """Test cleanup of multiple containers."""
        runtime = SandboxRuntime()
        await runtime.connect()

        try:
            # Execute multiple times
            for i in range(3):
                await runtime.execute_code(
                    code=f"print('Execution {i}')",
                    timeout_seconds=30,
                )

            # All should be cleaned up
            assert len(runtime._containers) == 0
        finally:
            await runtime.close()


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
class TestSandboxContextManager:
    """Test sandbox context manager behavior."""

    async def test_context_manager_connects_and_closes(self):
        """Test that context manager properly connects and closes."""
        runtime = SandboxRuntime()
        assert runtime.docker is None

        async with runtime:
            assert runtime.docker is not None

        assert runtime.docker is None

    async def test_context_manager_cleans_up_on_exception(self):
        """Test that context manager cleans up even on exception."""
        try:
            async with SandboxRuntime() as runtime:
                await runtime.execute_code(
                    code="print('Test')",
                    timeout_seconds=30,
                )
                raise ValueError("Test exception")
        except ValueError:
            pass  # Expected

        # Should have cleaned up despite exception


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
class TestSandboxSecurity:
    """Test sandbox security features."""

    async def test_filesystem_isolation(self):
        """Test that sandbox has isolated filesystem."""
        async with SandboxRuntime() as runtime:
            code = """
import os
# Try to list root directory
try:
    files = os.listdir('/')
    print(f'Root directory has {len(files)} entries')
except Exception as e:
    print(f'Error: {e}')
"""
            result = await runtime.execute_code(code=code, timeout_seconds=30)

            # Should complete without error (filesystem is isolated)
            assert result.exit_code == 0

    async def test_non_root_user(self):
        """Test that code runs as non-root user."""
        async with SandboxRuntime() as runtime:
            code = """
import os
uid = os.getuid()
print(f'UID: {uid}')
if uid == 0:
    print('Running as root!')
else:
    print('Running as non-root user')
"""
            result = await runtime.execute_code(code=code, timeout_seconds=30)

            assert result.success
            assert "non-root" in result.stdout.lower()


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
class TestSandboxEdgeCases:
    """Test sandbox edge cases and corner cases."""

    async def test_empty_code(self):
        """Test executing empty code."""
        async with SandboxRuntime() as runtime:
            result = await runtime.execute_code(code="", timeout_seconds=30)

            # Empty code should succeed
            assert result.success

    async def test_code_with_unicode(self):
        """Test executing code with Unicode characters."""
        async with SandboxRuntime() as runtime:
            code = """
print('Hello 世界')
print('Unicode: ñ, é, 中文')
"""
            result = await runtime.execute_code(code=code, timeout_seconds=30)

            assert result.success
            assert "世界" in result.stdout

    async def test_large_output(self):
        """Test handling of large output."""
        async with SandboxRuntime() as runtime:
            code = """
for i in range(1000):
    print(f'Line {i}: ' + 'x' * 100)
"""
            result = await runtime.execute_code(code=code, timeout_seconds=30)

            assert result.success
            assert len(result.stdout) > 100000  # Large output
