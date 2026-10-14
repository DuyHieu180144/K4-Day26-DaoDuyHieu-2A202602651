"""Comprehensive Test Runner for Day 26 MCP & Function Calling Labs.

Runs and validates:
1. 01-function-calling (Function Calling flow with Gemini SDK / Simulation fallback)
2. 02-mcp-basics (MCP Server & Client communication over stdio)
3. 03-production:
   - 3a: Auth Server + Client (Streamable HTTP with Bearer Token verification)
   - 3b: Tool Registry Client (Tool-centric discovery & semantic version matching)
   - 3c: Versioned Client & Server (Backward compatibility & server metadata)
4. 04-lab:
   - Setup verification (verify_setup.py)
   - Direct Streamable HTTP MCP test (test_mcp_direct.py)
"""
import os
import subprocess
import sys
import time
from pathlib import Path

# Fix stdout encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent
VENV_PYTHON = ROOT_DIR / ".venv" / "Scripts" / "python.exe"
if not VENV_PYTHON.exists():
    VENV_PYTHON = Path(sys.executable)


def run_section(title: str, cmd: list[str], cwd: Path) -> bool:
    print("\n" + "=" * 60)
    print(f"▶ RUNNING: {title}")
    print("=" * 60)
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    
    start = time.time()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        duration = time.time() - start
        print(proc.stdout.strip())
        if proc.stderr:
            print("[stderr]:", proc.stderr.strip())
        if proc.returncode == 0:
            print(f"✅ PASSED in {duration:.2f}s")
            return True
        else:
            print(f"❌ FAILED with returncode {proc.returncode}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def main():
    print("=" * 60)
    print("DAY 26 — FULL LAB SUITE EXECUTION")
    print("=" * 60)

    results = {}

    # 1. Step 01: Function Calling
    results["01-function-calling"] = run_section(
        "01: Function Calling (Gemini SDK)",
        [str(VENV_PYTHON), "weather_function_calling.py"],
        ROOT_DIR / "01-function-calling",
    )

    # 2. Step 02: MCP Basics
    results["02-mcp-basics"] = run_section(
        "02: MCP Basics (stdio transport)",
        [str(VENV_PYTHON), "weather_client.py"],
        ROOT_DIR / "02-mcp-basics",
    )

    # 3. Step 03: Production - Registry
    results["03-production (Registry)"] = run_section(
        "03: Tool Registry Discovery",
        [str(VENV_PYTHON), "registry_client.py"],
        ROOT_DIR / "03-production",
    )

    # 4. Step 03: Production - Versioning
    results["03-production (Versioning)"] = run_section(
        "03: Versioning & Backward Compatibility",
        [str(VENV_PYTHON), "versioned_client.py"],
        ROOT_DIR / "03-production",
    )

    # 5. Step 03: Production - Auth (start server, run client, stop server)
    print("\n" + "=" * 60)
    print("▶ RUNNING: 03: Authentication (Streamable HTTP + TokenVerifier)")
    print("=" * 60)
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    server_proc = subprocess.Popen(
        [str(VENV_PYTHON), "auth_server.py"],
        cwd=str(ROOT_DIR / "03-production"),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(2)
    try:
        client_proc = subprocess.run(
            [str(VENV_PYTHON), "auth_client.py"],
            cwd=str(ROOT_DIR / "03-production"),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        print(client_proc.stdout.strip())
        results["03-production (Auth)"] = (client_proc.returncode == 0)
        if client_proc.returncode == 0:
            print("✅ PASSED")
        else:
            print(f"❌ FAILED with returncode {client_proc.returncode}")
    finally:
        server_proc.terminate()
        server_proc.wait(timeout=5)

    # 6. Step 04: Lab 04 - verify_setup.py & test_mcp_direct.py
    # Start weather mcp server on port 8085
    print("\n" + "=" * 60)
    print("▶ RUNNING: 04-lab: FastMCP Server & ADK Client Verification")
    print("=" * 60)
    lab_server_env = env.copy()
    lab_server_env["PORT"] = "8085"
    lab_server = subprocess.Popen(
        [sys.executable, "weather.py"],
        cwd=str(ROOT_DIR / "04-lab" / "mcp-server"),
        env=lab_server_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(3)
    try:
        results["04-lab (verify_setup)"] = run_section(
            "04-lab: Setup Verification",
            [sys.executable, "verify_setup.py"],
            ROOT_DIR / "04-lab" / "mcp-client",
        )
        results["04-lab (test_mcp_direct)"] = run_section(
            "04-lab: Direct Remote MCP Tool Execution",
            [sys.executable, "test_mcp_direct.py"],
            ROOT_DIR / "04-lab" / "mcp-client",
        )
    finally:
        lab_server.terminate()
        lab_server.wait(timeout=5)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY RESULTS")
    print("=" * 60)
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} : {test_name}")
        if not passed:
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("🎉 ALL 6 LAB COMPONENTS PASSED SUCCESSFULLY!")
        return 0
    else:
        print("⚠️ SOME TESTS FAILED.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

