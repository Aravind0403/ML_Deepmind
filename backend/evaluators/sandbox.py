"""Strict AST + OS-resource-limited subprocess sandbox for executing untrusted user Python code."""
from __future__ import annotations

import ast
import os
import resource
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

FORBIDDEN_MODULES = {
    "os",
    "sys",
    "subprocess",
    "socket",
    "shutil",
    "pathlib",
    "ctypes",
    "urllib",
    "http",
    "requests",
    "httpx",
    "multiprocessing",
    "threading",
    "signal",
    "resource",
    "importlib",
    "builtins",
    "pickle",
    "tempfile",
    "glob",
    "fcntl",
    "pty",
    "webbrowser",
}

FORBIDDEN_CALLS = {"open", "exec", "eval", "__import__", "compile", "breakpoint", "input"}


@dataclass
class SandboxResult:
    ok: bool
    exit_code: int
    stdout: str
    stderr: str
    elapsed_ms: float
    timed_out: bool = False
    violation: str | None = None


def check_ast_safety(
    code: str,
    banned_apis: Iterable[str] = (),
    ban_matmul_op: bool = False,
) -> str | None:
    """Statically inspect user Python code for unsafe imports/calls or problem-banned APIs."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return f"SyntaxError on line {exc.lineno}: {exc.msg}"

    banned_set = set(banned_apis)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_mod = alias.name.split(".")[0]
                if root_mod in FORBIDDEN_MODULES:
                    return f"Sandbox violation: importing '{root_mod}' is not permitted."
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root_mod = node.module.split(".")[0]
                if root_mod in FORBIDDEN_MODULES:
                    return f"Sandbox violation: importing from '{root_mod}' is not permitted."
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
                return f"Sandbox violation: calling '{node.func.id}()' is not permitted."
            if isinstance(node.func, ast.Attribute) and node.func.attr in banned_set:
                return f"Problem constraint violation: calling '.{node.func.attr}()' is banned for this exercise."
            if isinstance(node.func, ast.Name) and node.func.id in banned_set:
                return f"Problem constraint violation: calling '{node.func.id}()' is banned for this exercise."
        elif ban_matmul_op and isinstance(node, ast.MatMult):
            return "Problem constraint violation: using the '@' matmul operator is banned for this exercise."

    return None


def _apply_limits(timeout_sec: int, max_mem_mb: int) -> None:
    """Apply POSIX resource caps inside the child process before exec."""
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (timeout_sec, timeout_sec + 1))
    except Exception:
        pass
    try:
        # Cap writable file size to 4MB
        resource.setrlimit(resource.RLIMIT_FSIZE, (4 * 1024 * 1024, 4 * 1024 * 1024))
    except Exception:
        pass
    try:
        # Cap open file descriptors
        resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    except Exception:
        pass
    try:
        # Cap heap/data segment (safe on macOS + Linux unlike RLIMIT_AS with OpenBLAS)
        mem_bytes = max_mem_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_DATA, (mem_bytes, mem_bytes))
    except Exception:
        pass


def run_sandboxed_script(
    user_code: str,
    harness_code: str,
    timeout_sec: int = 5,
    max_mem_mb: int = 512,
    banned_apis: Iterable[str] = (),
    ban_matmul_op: bool = False,
) -> SandboxResult:
    """Execute user_code + harness_code inside an isolated temp dir with strict CPU/mem/timeout caps."""
    violation = check_ast_safety(user_code, banned_apis=banned_apis, ban_matmul_op=ban_matmul_op)
    if violation:
        return SandboxResult(
            ok=False,
            exit_code=2,
            stdout="",
            stderr=violation,
            elapsed_ms=0.0,
            timed_out=False,
            violation=violation,
        )

    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": tempfile.gettempdir(),
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "VECLIB_MAXIMUM_THREADS": "1",
        "NUMEXPR_NUM_THREADS": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
    }

    t0 = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="dml_sandbox_") as tmpdir:
        tmp = Path(tmpdir)
        (tmp / "user_solution.py").write_text(user_code, encoding="utf-8")
        (tmp / "run_harness.py").write_text(harness_code, encoding="utf-8")

        try:
            proc = subprocess.run(
                [sys.executable, "-I", str(tmp / "run_harness.py")],
                cwd=tmpdir,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                preexec_fn=lambda: _apply_limits(timeout_sec, max_mem_mb),
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            cpu_killed = proc.returncode in (-24, 152)  # SIGXCPU from RLIMIT_CPU
            stderr_out = proc.stderr[:12000]
            if cpu_killed and not stderr_out:
                stderr_out = f"Execution killed by CPU time limit ({timeout_sec}s — possible infinite loop)."
            return SandboxResult(
                ok=proc.returncode == 0,
                exit_code=proc.returncode,
                stdout=proc.stdout[:12000],
                stderr=stderr_out,
                elapsed_ms=round(elapsed_ms, 2),
                timed_out=cpu_killed,
            )
        except subprocess.TimeoutExpired as exc:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            return SandboxResult(
                ok=False,
                exit_code=124,
                stdout=(exc.stdout or "")[:4000] if isinstance(exc.stdout, str) else "",
                stderr=f"Execution timed out after {timeout_sec}s (possible infinite loop or O(N^3) blowup).",
                elapsed_ms=round(elapsed_ms, 2),
                timed_out=True,
            )
