import os
import time
import subprocess
import socket
import shlex
import signal
from zapv2 import ZAPv2

CANDIDATE_PATHS = [
    os.environ.get("ZAP_PATH"),
    "/Applications/ZAP.app/Contents/MacOS/ZAP.sh",   # macOS default (ZAP app)
    "/Applications/ZAP.app/Contents/Java/zap.sh",
    "/usr/local/bin/zap.sh",
    "/opt/zaproxy/zap.sh",
]
ZAP_PATH = next((p for p in CANDIDATE_PATHS if p and os.path.exists(p)), None)

ZAP_PORT = int(os.environ.get("ZAP_PORT", 8090))
ZAP_API_KEY = os.environ.get("ZAP_API_KEY", "changeme")
ZAP_BASE = f"http://127.0.0.1:{ZAP_PORT}"
START_TIMEOUT = int(os.environ.get("ZAP_START_TIMEOUT", 60))
LOG_FILE = os.path.expanduser(os.environ.get("ZAP_LAUNCHER_LOG", "~/zap_launcher.log"))

DEFAULT_JAVA_HEAP = os.environ.get("ZAP_JAVA_HEAP", "6000m")
DEFAULT_SPIDER_THREADS = int(os.environ.get("ZAP_SPIDER_THREADS", 8))
DEFAULT_SPIDER_MAX_DEPTH = int(os.environ.get("ZAP_SPIDER_MAX_DEPTH", 3))
DEFAULT_PSCAN_MAX_ALERTS = int(os.environ.get("ZAP_PSCAN_MAX_ALERTS", 5000))


def _port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except Exception:
        return False


def _is_zap_running():
    try:
        zap = ZAPv2(apikey=ZAP_API_KEY, proxies={"http": ZAP_BASE, "https": ZAP_BASE})
        _ = zap.core.version
        return True
    except Exception:
        return _port_open("127.0.0.1", ZAP_PORT)


def start_zap(wait=True, timeout=START_TIMEOUT, heap=DEFAULT_JAVA_HEAP, extra_jvm_opts=None, extra_configs=None):
    if _is_zap_running():
        print("ZAP already running.")
        return True

    if not ZAP_PATH:
        raise FileNotFoundError("ZAP start script not found. Set ZAP_PATH env or install ZAP.")

    env = os.environ.copy()
    jvm_list = []
    if heap:
        jvm_list.append(f"-Xmx{heap}")

    jvm_list.append("-XX:+UseG1GC")
    jvm_list.append("-XX:MaxGCPauseMillis=200")
    if extra_jvm_opts:
        jvm_list.extend(extra_jvm_opts)

    existing = env.get("JAVA_TOOL_OPTIONS", "").strip()
    env["JAVA_TOOL_OPTIONS"] = f"{' '.join(jvm_list)} {existing}".strip()
    env["ZAP_JAVA_OPTS"] = env["JAVA_TOOL_OPTIONS"]

    args = [ZAP_PATH, "-daemon", "-port", str(ZAP_PORT), "-host", "127.0.0.1", "-config", f"api.key={ZAP_API_KEY}"]

    default_configs = {
        "spider.threadCount": str(DEFAULT_SPIDER_THREADS),
        "spider.maxDepth": str(DEFAULT_SPIDER_MAX_DEPTH),
        "pscan.maxAlerts": str(DEFAULT_PSCAN_MAX_ALERTS),
    }
    merged_configs = default_configs.copy()
    if extra_configs:
        merged_configs.update(extra_configs)
    for k, v in merged_configs.items():
        args += ["-config", f"{k}={v}"]

    log_dir = os.path.dirname(LOG_FILE)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    lf = open(LOG_FILE, "ab")

    print("Starting OWASP ZAP with JVM options:", env["JAVA_TOOL_OPTIONS"])
    print("Command:", " ".join(shlex.quote(a) for a in args))
    subprocess.Popen(args, env=env, stdout=lf, stderr=lf, close_fds=True)

    if not wait:
        return True

    start = time.time()
    while time.time() - start < timeout:
        if _is_zap_running():
            print("ZAP started and API reachable.")
            return True
        time.sleep(1)

    raise TimeoutError(f"Timed out waiting for ZAP to start. Check log: {LOG_FILE}")


def stop_zap(graceful=True, timeout=15):
    if not _is_zap_running():
        print("ZAP is not running.")
        return True

    try:
        subprocess.run(["pkill", "-f", "zap-.*jar"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["pkill", "-f", "org.zaproxy"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)
    except Exception:
        pass

    try:
        out = subprocess.check_output(["ps", "aux"], text=True)
        for line in out.splitlines():
            if ("zap" in line.lower() and "java" in line.lower()) or "zap-" in line:
                parts = line.split()
                pid = int(parts[1])
                try:
                    os.kill(pid, signal.SIGTERM)
                except Exception:
                    pass
        start = time.time()
        while _is_zap_running() and (time.time() - start) < timeout:
            time.sleep(0.5)
    except Exception:
        pass

    if _is_zap_running():
        print("ZAP still appears to be running after stop attempt.")
        return False
    print("ZAP stopped.")
    return True


def restart_zap(wait=True, timeout=START_TIMEOUT, heap=DEFAULT_JAVA_HEAP, extra_jvm_opts=None, extra_configs=None):
    stop_zap()
    return start_zap(wait=wait, timeout=timeout, heap=heap, extra_jvm_opts=extra_jvm_opts, extra_configs=extra_configs)


def get_zap_client():
    if not _is_zap_running():
        print("ZAP not running. Starting with defaults...")
        start_zap(wait=True)
    return ZAPv2(apikey=ZAP_API_KEY, proxies={"http": ZAP_BASE, "https": ZAP_BASE})


if __name__ == "__main__":
    print("zap_launcher.py - quick CLI")
    print("ZAP_PATH:", ZAP_PATH)
    print("ZAP_BASE:", ZAP_BASE)
    print("LOG_FILE:", LOG_FILE)
    print("Default heap:", DEFAULT_JAVA_HEAP)
    action = os.environ.get("ZAP_ACTION", "start").lower()
    if action == "start":
        start_zap()
    elif action == "stop":
        stop_zap()
    elif action == "restart":
        restart_zap()
    else:
        print("Unknown action. Use ZAP_ACTION=start|stop|restart")
