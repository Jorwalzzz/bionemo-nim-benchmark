"""Backwards-compatible shim delegating to bionemo_benchmark.mcp.server."""
from bionemo_benchmark.mcp.server import *  # noqa: F401, F403
from bionemo_benchmark.mcp.server import main

if __name__ == "__main__":
    main()
