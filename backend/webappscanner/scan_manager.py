import threading
import time
from webappscanner.zap_launcher import get_zap_client

# Store scan results in memory
SCAN_RESULTS = {}

def run_scan_async(scan_id, target):
    zap = get_zap_client()
    progress = []

    try:
        zap.urlopen(target)
        progress.append({"stage": "open_url", "status": "done"})

        # Spider with maxChildren to avoid memory issues
        spider_id = zap.spider.scan(target, maxChildren=20)
        while int(zap.spider.status(spider_id)) < 100:
            progress.append({"stage": "spider", "status": f"{zap.spider.status(spider_id)}%"})
            time.sleep(1)
        progress.append({"stage": "spider", "status": "done"})

        # Active scan
        ascan_id = zap.ascan.scan(target)
        while int(zap.ascan.status(ascan_id)) < 100:
            progress.append({"stage": "active_scan", "status": f"{zap.ascan.status(ascan_id)}%"})
            time.sleep(2)
        progress.append({"stage": "active_scan", "status": "done"})

        # Gather alerts
        alerts = zap.core.alerts(baseurl=target)
        results = []
        for a in alerts:
            results.append({
                "alert": a.get("alert"),
                "risk": a.get("risk"),
                "confidence": a.get("confidence"),
                "url": a.get("url"),
                "param": a.get("param"),
                "cweid": a.get("cweid"),
            })

        SCAN_RESULTS[scan_id] = {"results": results, "progress": progress}

    except Exception as e:
        SCAN_RESULTS[scan_id] = {"results": [], "progress": progress, "error": str(e)}

def start_scan(scan_id, target):
    thread = threading.Thread(target=run_scan_async, args=(scan_id, target))
    thread.start()
