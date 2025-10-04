from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import FileResponse
import io, uuid, threading, time
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from webappscanner import zap_launcher  # your zap_launcher.py

# In-memory scan store and lock (thread-safe)
SCAN_RESULTS = {}
SCAN_LOCK = threading.Lock()

# CWE → Suggestion map (short OWASP-based remediations)
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


def start_scan(scan_id, target):
    """Starts background spider + active scan."""
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

            # 1) open url
            zap.urlopen(target)
            with SCAN_LOCK:
                SCAN_RESULTS[scan_id]["progress"]["open_url"] = "done"

            # 2) spider
            spider_id = zap.spider.scan(target)
            prev_spider_percent = 0
            while True:
                raw = zap.spider.status(spider_id)
                try:
                    reported = int(float(raw))
                except Exception:
                    reported = 0
                reported = max(prev_spider_percent, reported)
                prev_spider_percent = reported
                with SCAN_LOCK:
                    SCAN_RESULTS[scan_id]["progress"]["spider"] = str(reported)
                if reported >= 100:
                    break
                time.sleep(1)
            with SCAN_LOCK:
                SCAN_RESULTS[scan_id]["progress"]["spider"] = "done"

            # 3) active scan
            ascan_id = zap.ascan.scan(target)
            prev_ascan_percent = 0
            while True:
                raw = zap.ascan.status(ascan_id)
                try:
                    reported = int(float(raw))
                except Exception:
                    reported = 0
                reported = max(prev_ascan_percent, reported)
                prev_ascan_percent = reported
                with SCAN_LOCK:
                    SCAN_RESULTS[scan_id]["progress"]["active_scan"] = str(reported)
                if reported >= 100:
                    break
                time.sleep(2)
            with SCAN_LOCK:
                SCAN_RESULTS[scan_id]["progress"]["active_scan"] = "done"

            # 4) collect alerts
            alerts = zap.core.alerts(baseurl=target)
            results = []
            for a in alerts:
                cweid = a.get("cweid")
                results.append({
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
                    "suggestion": get_suggestion(cweid, a.get("solution")),
                })
            with SCAN_LOCK:
                SCAN_RESULTS[scan_id]["results"] = results

        except Exception as e:
            with SCAN_LOCK:
                SCAN_RESULTS[scan_id]["error"] = str(e)

    t = threading.Thread(target=run, daemon=True)
    t.start()


@api_view(["POST"])
def run_zap_scan(request):
    target = (request.data.get("target") or "").strip()
    if not target:
        return Response({"error": "target is required"}, status=400)
    scan_id = str(uuid.uuid4())
    start_scan(scan_id, target)
    return Response({"scan_id": scan_id, "status": "started"})


@api_view(["GET"])
def scan_status(request, scan_id):
    with SCAN_LOCK:
        scan_data = SCAN_RESULTS.get(scan_id)
        if not scan_data:
            return Response({"status": "not_found"})
        if "error" in scan_data:
            return Response({"status": "error", "details": scan_data["error"]})

        progress = scan_data.get("progress", {})
        finished = (progress.get("spider") == "done" and progress.get("active_scan") == "done")
        status = "finished" if finished else "running"

        progress_list = [{"stage": k, "status": v} for k, v in progress.items()]

        return Response({
            "status": status,
            "progress": progress_list,
            "results": scan_data.get("results", []) if finished else []
        })


import io
from rest_framework.decorators import api_view
from django.http import FileResponse
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from threading import Lock

# --- global scan storage ---
SCAN_RESULTS = {}
SCAN_LOCK = Lock()

# --- logos ---
LOGO_LEFT_PATH = "/Users/darshitayar/Desktop/VaptManagement /frontend/src/assets/OTlogo.jpg"
LOGO_RIGHT_PATH = "/Users/darshitayar/Desktop/VaptManagement /frontend/src/assets/HomeIcon.png"


@api_view(["GET"])
def download_pdf_report(request, scan_id):
    with SCAN_LOCK:
        scan_data = SCAN_RESULTS.get(scan_id, {})
        results = scan_data.get("results", [])

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    elements = []

    # --- HEADER: logos + company info ---
    try:
        logo_left = Image(LOGO_LEFT_PATH, width=55, height=55)
        logo_right = Image(LOGO_RIGHT_PATH, width=70, height=70)
    except Exception:
        logo_left = Paragraph("", normal)
        logo_right = Paragraph("", normal)

    header_table = Table([
        [logo_left,
         Paragraph("<b>Orange Technolab Pvt Ltd<br/>ISO 9001 & 27001 Certified Company</b>", styles["Heading3"]),
         logo_right]
    ], colWidths=[70, 360, 70])
    header_table.setStyle(TableStyle([
        ("ALIGN", (0,0), (0,0), "LEFT"),
        ("ALIGN", (1,0), (1,0), "CENTER"),
        ("ALIGN", (2,0), (2,0), "RIGHT"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (1,0), (1,0), 10),
        ("RIGHTPADDING", (1,0), (1,0), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 12)
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 50))

    # --- Report Title ---
    elements.append(Paragraph("Web Application Security Scan Report", styles['Title']))
    elements.append(Spacer(1, 12))

    if not results:
        elements.append(Paragraph("✅ No alerts found. Run a scan first (or wait for scan to finish).", normal))
    else:
        data = [["Alert", "Risk", "URL", "Param", "CWE", "Suggestion"]]
        for r in results:
            data.append([
                Paragraph(r.get("alert", "") or "", normal),
                Paragraph(r.get("risk", "") or "", normal),
                Paragraph(r.get("url", "") or "", normal),
                Paragraph(r.get("param", "") or "", normal),
                Paragraph(str(r.get("cweid", "")), normal),
                Paragraph(r.get("suggestion", "") or "", normal),
            ])

        col_widths = [110, 60, 160, 60, 40, 150]
        table = Table(data, colWidths=col_widths, repeatRows=1)
        style = TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0d1b2a")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("ALIGN", (0,0), (-1,-1), "LEFT"),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,0), 10),
            ("BOTTOMPADDING", (0,0), (-1,0), 6),
            ("BACKGROUND", (0,1), (-1,-1), colors.whitesmoke),
            ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
        ])

        for idx, r in enumerate(results, start=1):
            risk = (r.get("risk") or "").lower()
            if "high" in risk:
                style.add("BACKGROUND", (0, idx), (-1, idx), colors.HexColor("#ffd6d6"))
            elif "medium" in risk:
                style.add("BACKGROUND", (0, idx), (-1, idx), colors.HexColor("#fff0d6"))
            elif "low" in risk:
                style.add("BACKGROUND", (0, idx), (-1, idx), colors.HexColor("#f7ffd6"))

        table.setStyle(style)
        elements.append(table)

    # --- Footer & Background ---
    def add_page(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(colors.HexColor("#f6f6f6"))
        canvas.rect(0, 0, doc.pagesize[0], doc.pagesize[1], stroke=0, fill=1)
        footer_text = "www.orangetechnolab.com | +91 88660 68968 | sales@orangewebtech.com"
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(colors.black)
        canvas.drawCentredString(doc.pagesize[0]/2, 20, footer_text)
        canvas.restoreState()

    doc.build(elements, onFirstPage=add_page, onLaterPages=add_page)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"webapp_scan_report_{scan_id}.pdf")
