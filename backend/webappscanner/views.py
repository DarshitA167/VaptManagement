# backend/webappscanner/views.py

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import FileResponse
from django.utils import timezone
from django.db import transaction
from django.db.models import Max, Sum, Case, When, IntegerField
import io
import uuid
import threading
import time

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from .models import WebAppScanResult
from . import zap_launcher

# Thread-safe in-memory store for live progress and results
SCAN_RESULTS = {}
SCAN_LOCK = threading.Lock()

# CWE suggestions map
CWE_SUGGESTIONS = {
    "79": "Sanitize/encode all user input and use CSP to prevent XSS.",
    "89": "Use parameterized queries / ORM or prepared statements to avoid SQL injection.",
    "200": "Avoid revealing sensitive data in responses; restrict access and mask data.",
    "352": "Use CSRF tokens and SameSite cookies for state-changing endpoints.",
    "22": "Validate and sanitize file paths; use allowlists and avoid direct file writes.",
    "20": "Implement strict input validation (allowlist) and output encoding.",
    "287": "Enforce strong authentication, least privilege, and logging.",
    "502": "Validate and restrict inbound request targets to prevent SSRF.",
}


def get_suggestion(cweid, zap_solution=""):
    if not cweid:
        return zap_solution or "No suggestion available"
    return CWE_SUGGESTIONS.get(str(cweid), zap_solution or "No suggestion available")


def start_scan(scan_id, target, spider_timeout=600, ascan_timeout=1800):
    """
    Start a background thread that runs spider + active scan using ZAP,
    stores live progress to SCAN_RESULTS, and persists alerts to DB when finished.
    """

    with SCAN_LOCK:
        SCAN_RESULTS[scan_id] = {
            "progress": {"open_url": "pending", "spider": "0", "active_scan": "0"},
            "results": [],
            "started_at": time.time(),
        }

    def run():
        try:
            # get or start zap
            try:
                zap = zap_launcher.get_zap_client()
            except Exception:
                zap_launcher.start_zap(wait=True)
                zap = zap_launcher.get_zap_client()

            # open url
            try:
                zap.urlopen(target)
                with SCAN_LOCK:
                    SCAN_RESULTS[scan_id]["progress"]["open_url"] = "done"
            except Exception as e:
                # mark open_url as error and continue (scan may still proceed)
                with SCAN_LOCK:
                    SCAN_RESULTS[scan_id]["progress"]["open_url"] = "error"
                    SCAN_RESULTS[scan_id]["error"] = f"open_url failed: {e}"

            # spider
            try:
                spider_id = zap.spider.scan(target)
                prev_spider_percent = 0
                start_time = time.time()
                while True:
                    try:
                        raw = zap.spider.status(spider_id)
                        reported = int(float(raw)) if raw not in (None, "") else 0
                    except Exception:
                        reported = 0
                    reported = max(prev_spider_percent, reported)
                    prev_spider_percent = reported
                    with SCAN_LOCK:
                        SCAN_RESULTS[scan_id]["progress"]["spider"] = str(reported)
                    if reported >= 100:
                        break
                    if (time.time() - start_time) > spider_timeout:
                        # timeout - bail out
                        with SCAN_LOCK:
                            SCAN_RESULTS[scan_id]["progress"]["spider"] = "timeout"
                        break
                    time.sleep(1)
                with SCAN_LOCK:
                    # if not already "done" or "timeout"
                    if SCAN_RESULTS[scan_id]["progress"].get("spider") != "timeout":
                        SCAN_RESULTS[scan_id]["progress"]["spider"] = "done"
            except Exception as e:
                with SCAN_LOCK:
                    SCAN_RESULTS[scan_id]["progress"]["spider"] = "error"
                    SCAN_RESULTS[scan_id]["error"] = f"spider failed: {e}"

            # active scan
            try:
                ascan_id = zap.ascan.scan(target)
                prev_ascan_percent = 0
                start_time = time.time()
                while True:
                    try:
                        raw = zap.ascan.status(ascan_id)
                        reported = int(float(raw)) if raw not in (None, "") else 0
                    except Exception:
                        reported = 0
                    reported = max(prev_ascan_percent, reported)
                    prev_ascan_percent = reported
                    with SCAN_LOCK:
                        SCAN_RESULTS[scan_id]["progress"]["active_scan"] = str(reported)
                    if reported >= 100:
                        break
                    if (time.time() - start_time) > ascan_timeout:
                        with SCAN_LOCK:
                            SCAN_RESULTS[scan_id]["progress"]["active_scan"] = "timeout"
                        break
                    time.sleep(2)
                with SCAN_LOCK:
                    if SCAN_RESULTS[scan_id]["progress"].get("active_scan") != "timeout":
                        SCAN_RESULTS[scan_id]["progress"]["active_scan"] = "done"
            except Exception as e:
                with SCAN_LOCK:
                    SCAN_RESULTS[scan_id]["progress"]["active_scan"] = "error"
                    SCAN_RESULTS[scan_id]["error"] = f"ascan failed: {e}"

            # collect alerts from ZAP
            try:
                alerts = zap.core.alerts(baseurl=target) or []
            except Exception:
                alerts = []

            results = []
            for a in alerts:
                cweid = a.get("cweid")
                suggestion = get_suggestion(cweid, a.get("solution"))
                item = {
                    "alert": a.get("alert"),
                    "risk": a.get("risk"),
                    "confidence": a.get("confidence"),
                    "url": a.get("url"),
                    "param": a.get("param"),
                    "cweid": cweid,
                    "wascid": a.get("wascid"),
                    "description": a.get("description"),
                    "solution": a.get("solution"),
                    "reference": a.get("reference"),
                    "evidence": a.get("evidence"),
                    "suggestion": suggestion,
                }
                results.append(item)

            # Save to memory for immediate retrieval
            with SCAN_LOCK:
                SCAN_RESULTS[scan_id]["results"] = results

            # Persist results to DB (atomic)
            try:
                with transaction.atomic():
                    if results:
                        # create one row per alert
                        objs = []
                        for r in results:
                            objs.append(WebAppScanResult(
                                scan_id=scan_id,
                                target=target,
                                alert=r.get("alert"),
                                risk=r.get("risk"),
                                confidence=r.get("confidence"),
                                url=r.get("url"),
                                param=r.get("param"),
                                cweid=r.get("cweid"),
                                wascid=r.get("wascid"),
                                description=r.get("description"),
                                solution=r.get("solution"),
                                reference=r.get("reference"),
                                evidence=r.get("evidence"),
                                suggestion=r.get("suggestion"),
                            ))
                        WebAppScanResult.objects.bulk_create(objs)
                    else:
                        # create a placeholder row to mark the run (no alerts)
                        WebAppScanResult.objects.create(
                            scan_id=scan_id,
                            target=target,
                            alert=None
                        )
            except Exception as e:
                with SCAN_LOCK:
                    SCAN_RESULTS[scan_id].setdefault("meta", {})["db_error"] = str(e)

        except Exception as e:
            with SCAN_LOCK:
                SCAN_RESULTS[scan_id]["error"] = str(e)

    t = threading.Thread(target=run, daemon=True)
    t.start()


@api_view(["POST"])
def run_zap_scan(request):
    """
    Kick off a ZAP scan in background. Returns a scan_id for polling.
    """
    target = (request.data.get("target") or "").strip()
    if not target:
        return Response({"error": "target is required"}, status=400)

    scan_id = str(uuid.uuid4())
    start_scan(scan_id, target)
    return Response({
        "scan_id": scan_id,
        "status": "started",
        "target": target,
        "started_at": timezone.now().isoformat()
    })


@api_view(["GET"])
def scan_status(request, scan_id):
    """
    Return live progress and results (results only when finished).
    """
    with SCAN_LOCK:
        scan_data = SCAN_RESULTS.get(scan_id)
        if not scan_data:
            return Response({"status": "not_found"})
        if "error" in scan_data:
            return Response({"status": "error", "details": scan_data["error"]})

        progress = scan_data.get("progress", {})
        finished = (progress.get("spider") == "done" and progress.get("active_scan") == "done")
        status = "finished" if finished else "running"

        return Response({
            "status": status,
            "progress": [{"stage": k, "status": v} for k, v in progress.items()],
            "results": scan_data.get("results", []) if finished else []
        })


@api_view(["GET"])
def download_pdf_report(request, scan_id):
    """
    Build PDF from saved DB results for given scan_id.
    Falls back to in-memory results if DB empty.
    """
    # try DB first
    rows = list(WebAppScanResult.objects.filter(scan_id=scan_id).order_by("created_at").values())
    if not rows:
        # fallback to in-memory
        with SCAN_LOCK:
            rows = SCAN_RESULTS.get(scan_id, {}).get("results", [])

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    elements = []

    # Optional logos (guarded)
    LOGO_LEFT_PATH = "/Users/darshitayar/Desktop/VaptManagement /frontend/src/assets/OTlogo.jpg"
    LOGO_RIGHT_PATH = "/Users/darshitayar/Desktop/VaptManagement /frontend/src/assets/HomeIcon.png"
    try:
        logo_left = Image(LOGO_LEFT_PATH, width=55, height=55)
        logo_right = Image(LOGO_RIGHT_PATH, width=70, height=70)
    except Exception:
        logo_left = Paragraph("", normal)
        logo_right = Paragraph("", normal)

    header_table = Table(
        [[logo_left,
          Paragraph("<b>Orange Technolab Pvt Ltd ISO 9001 & 27001 Certified Company<br/></b>", styles["Heading3"]),
          logo_right]],
        colWidths=[70, 360, 70]
    )
    header_table.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 18))
    elements.append(Paragraph(f"Scan Report: {scan_id}", styles["Title"]))
    elements.append(Spacer(1, 12))

    # build table of results
    if not rows:
        elements.append(Paragraph("✅ No alerts found for this scan.", normal))
    else:
        data = [["Alert", "Risk", "URL", "Param", "CWE", "Suggestion"]]
        # normalize rows whether they came from DB (dict) or in-memory (dict item)
        for r in rows:
            alert = r.get("alert") if isinstance(r, dict) else None
            risk = r.get("risk")
            url = r.get("url")
            param = r.get("param")
            cweid = r.get("cweid")
            suggestion = r.get("suggestion")
            data.append([
                Paragraph(str(alert or ""), normal),
                Paragraph(str(risk or ""), normal),
                Paragraph(str(url or ""), normal),
                Paragraph(str(param or ""), normal),
                Paragraph(str(cweid or ""), normal),
                Paragraph(str(suggestion or ""), normal),
            ])

        table = Table(data, colWidths=[120, 60, 160, 60, 40, 150], repeatRows=1)
        style = TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0d1b2a")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
        ])
        table.setStyle(style)
        elements.append(table)

    def footer(canvas, doc):
        canvas.saveState()
        footer_text = "www.orangetechnolab.com"
        canvas.setFont("Helvetica", 9)
        canvas.drawCentredString(doc.pagesize[0]/2, 20, footer_text)
        canvas.restoreState()

    doc.build(elements, onFirstPage=footer, onLaterPages=footer)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"webapp_scan_report_{scan_id}.pdf")


@api_view(["GET"])
def scan_history(request):
    """
    Return grouped history: unique scan runs (group by scan_id), latest timestamp and alerts_count.
    Response format: { "scans": [ { scan_id, target, timestamp, status, alerts_count }, ... ] }
    """
    try:
        limit = int(request.GET.get("limit", 20))
        # group by scan_id and target, compute latest created_at and count of non-null alerts
        scans_qs = WebAppScanResult.objects.values("scan_id", "target").annotate(
            timestamp=Max("created_at"),
            alerts_count=Sum(
                Case(
                    When(alert__isnull=False, then=1),
                    default=0,
                    output_field=IntegerField(),
                )
            )
        ).order_by("-timestamp")[:limit]

        data = []
        for s in scans_qs:
            alerts_count = int(s.get("alerts_count") or 0)
            data.append({
                "scan_id": s["scan_id"],
                "target": s["target"],
                "timestamp": s["timestamp"],
                "status": "finished",  # we persist only after run ends
                "alerts_count": alerts_count,
            })

        return Response({"scans": data})
    except Exception as e:
        return Response({"error": str(e)}, status=500)
