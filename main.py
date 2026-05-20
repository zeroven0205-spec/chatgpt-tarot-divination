import logging
import os
import socket
import subprocess
import uvicorn

from src.app import app
from src.config import settings

logging.basicConfig(
    format="%(asctime)s: %(levelname)s: %(name)s: %(message)s",
    level=logging.INFO
)
_logger = logging.getLogger(__name__)

_logger.info(f"settings: {settings.model_dump_json(indent=2)}")


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def kill_port(port: int):
    try:
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True, text=True
        )
        if result.stdout.strip():
            pids = result.stdout.strip().split("\n")
            killed = []
            for pid in pids:
                # 验证进程是否为 uvicorn 或 python，避免误杀无关进程
                try:
                    cmd_result = subprocess.run(
                        ["ps", "-p", pid, "-o", "comm="],
                        capture_output=True, text=True
                    )
                    cmd = cmd_result.stdout.strip()
                    if cmd in ("uvicorn", "python", "python3", "java", "node"):
                        subprocess.run(["kill", "-9", pid], check=False)
                        killed.append(f"{pid}({cmd})")
                    else:
                        _logger.warning(
                            f"Skipping PID {pid} (cmd={cmd}) — not a known server process"
                        )
                except Exception:
                    pass
            if killed:
                _logger.info(f"Port {port} killed processes: {killed}")
    except Exception as e:
        _logger.warning(f"Failed to kill port {port}: {e}")


if __name__ == "__main__":
    port = 8000
    if is_port_in_use(port):
        _logger.info(f"Port {port} is in use, killing...")
        kill_port(port)
    uvicorn.run(app, host="0.0.0.0", port=8000)
