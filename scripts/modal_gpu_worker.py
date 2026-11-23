"""Optional Modal serverless GPU worker template for CUDA / Triton kernel & heavy ML lab benchmarking.

Deploy with:
    pip install modal
    modal deploy scripts/modal_gpu_worker.py

Then set MODAL_GPU_ENDPOINT in your .env file.
"""
try:
    import modal
except ImportError:
    modal = None  # Allows importing locally without Modal installed

if modal is not None:
    app = modal.App("ml-command-center-gpu-runner")
    image = modal.Image.debian_slim(python_version="3.11").pip_install(
        "torch",
        "triton",
        "numpy",
    )

    @app.function(image=image, gpu="T4", timeout=45)
    @modal.fastapi_endpoint(method="POST")
    def benchmark_kernel(payload: dict) -> dict:
        import subprocess
        import tempfile
        import time
        from pathlib import Path

        user_code = payload.get("user_code", "")
        harness_code = payload.get("harness_code", "")
        t0 = time.perf_counter()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / "user_solution.py").write_text(user_code, encoding="utf-8")
            (p / "harness.py").write_text(harness_code, encoding="utf-8")
            proc = subprocess.run(
                ["python3", str(p / "harness.py")],
                cwd=tmp,
                capture_output=True,
                text=True,
                timeout=30,
            )
        return {
            "ok": proc.returncode == 0,
            "stdout": proc.stdout[:12000],
            "stderr": proc.stderr[:12000],
            "elapsed_ms": round((time.perf_counter() - t0) * 1000.0, 2),
        }
