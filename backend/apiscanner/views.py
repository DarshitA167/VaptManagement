import io
import re
import threading
import time
from datetime import timezone
from django.http import FileResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

from .models import APIScan
from .serializers import APIScanSerializer

# Use your existing zap launcher (adjust import if needed)
from webappscanner import zap_launcher

# Basic CWE -> suggestion mapping (OWASP-style). Expand as you need.
CWE_SUGGESTIONS = {
    "79": "Validate and sanitize all user inputs to prevent XSS.",
    "89": "Use parameterized queries or ORM to prevent SQL Injection.",
    "200": "Avoid returning sensitive info in responses; mask or restrict access.",
    "352": "Use CSRF tokens for every state-changing request.",
    "22": "Validate and restrict file paths to prevent path traversal.",
}

def extract_cves(text):
    """Return list of CVEs found in text"""
    if not text:
        return []
    return re.findall(r"CVE-\d{4}-\d{4,7}", text, flags=re.IGNORECASE)

def get_suggestion_from_cwe(cweid, zap_solution=""):
    if not cweid:
        return zap_solution or "No suggestion available"
    return CWE_SUGGESTIONS.get(str(cweid), zap_solution or "Refer to ZAP solution / OWASP guidance")

def _update_progress(scan_obj, stage, status):
    # keep only the latest entry for a stage
    prog = [p for p in scan_obj.progress if p.get("stage") != stage]
    prog.append({"stage": stage, "status": status, "ts": time.time()})
    scan_obj.progress = prog
    scan_obj.save(update_fields=["progress"])

def _run_scan_thread(scan_id, target):
    """
    Background thread that runs the scan and updates APIScan DB record.
    """
    try:
        scan = APIScan.objects.get(id=scan_id)
    except APIScan.DoesNotExist:
        return

    scan.status = "running"
    scan.progress = []
    scan.results = []
    scan.error = ""
    scan.save()

    try:
        # get or start ZAP
        try:
            zap = zap_launcher.get_zap_client()
        except Exception:
            zap_launcher.start_zap(wait=True)
            zap = zap_launcher.get_zap_client()

        # 1) Open URL
        try:
            zap.urlopen(target)
        except Exception:
            # sometimes zap.urlopen raises; continue anyway
            pass
        _update_progress(scan, "open_url", "done")

        # 2) Spider (non blocking polling)
        spider_id = zap.spider.scan(target)
        while True:
            try:
                status = int(zap.spider.status(spider_id))
            except Exception:
                status = 0
            _update_progress(scan, "spider", f"{status}%")
            if status >= 100:
                break
            time.sleep(1)

        _update_progress(scan, "spider", "done")

        # 3) Active scan (may be slow / heavy — you can tune / disable)
        ascan_id = zap.ascan.scan(target)
        while True:
            try:
                status = int(zap.ascan.status(ascan_id))
            except Exception:
                status = 0
            _update_progress(scan, "active_scan", f"{status}%")
            if status >= 100:
                break
            time.sleep(2)

        _update_progress(scan, "active_scan", "done")

        # 4) Gather alerts
        alerts = []
        try:
            alerts = zap.core.alerts(baseurl=target)
        except Exception:
            try:
                # fallback: get all alerts
                alerts = zap.core.alerts()
            except Exception:
                alerts = []

        results = []
        for a in alerts:
            # parse CVE from reference/description
            text = (a.get("reference", "") or "") + " " + (a.get("description", "") or "")
            cves = extract_cves(text)
            cve = cves[0] if cves else ""

            risk = a.get("risk") or ""
            # map risk to priority
            priority = "low"
            if "high" in risk.lower():
                priority = "high"
            elif "medium" in risk.lower():
                priority = "medium"
            elif "low" in risk.lower() or "inform" in risk.lower():
                priority = "low"

            cweid = a.get("cweid")
            suggestion = get_suggestion_from_cwe(cweid, a.get("solution", ""))

            res = {
                "alert": a.get("alert"),
                "risk": risk,
                "priority": priority,
                "cve": cve,
                "url": a.get("url"),
                "param": a.get("param"),
                "cweid": cweid,
                "description": a.get("description"),
                "solution": a.get("solution"),
                "reference": a.get("reference"),
                "suggestion": suggestion,
            }
            results.append(res)

        scan.results = results
        scan.status = "finished"
        scan.finished_at = time.time()  # timestamp float OK; you can change to datetime
        # convert finished_at to a timezone-aware datetime
        from django.utils import timezone as dj_tz
        scan.finished_at = dj_tz.now()
        scan.save()

    except Exception as exc:
        scan.status = "error"
        scan.error = str(exc)
        scan.save()

@api_view(["POST"])
def start_api_scan(request):
    """
    POST { "target": "https://api.example.com" } -> returns scan_id
    """
    target = (request.data.get("target") or "").strip()
    if not target:
        return Response({"error": "target is required"}, status=400)

    scan = APIScan.objects.create(target=target, status="pending")
    # launch background thread
    t = threading.Thread(target=_run_scan_thread, args=(scan.id, target), daemon=True)
    t.start()

    return Response({"scan_id": str(scan.id), "status": "started"})

@api_view(["GET"])
def scan_status(request, scan_id):
    try:
        scan = APIScan.objects.get(id=scan_id)
    except APIScan.DoesNotExist:
        return Response({"error": "not found"}, status=404)
    data = {
        "scan_id": str(scan.id),
        "status": scan.status,
        "progress": scan.progress,
        "error": scan.error,
    }
    return Response(data)

@api_view(["GET"])
def scan_results(request, scan_id):
    try:
        scan = APIScan.objects.get(id=scan_id)
    except APIScan.DoesNotExist:
        return Response({"error": "not found"}, status=404)
    return Response({"scan_id": str(scan.id), "results": scan.results, "created_at": scan.created_at, "finished_at": scan.finished_at})
@api_view(["GET"])
def download_pdf_report(request, scan_id):
    import io
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.styles import getSampleStyleSheet
    from django.http import FileResponse
    from .models import APIScan

    try:
        scan = APIScan.objects.get(id=scan_id)
    except APIScan.DoesNotExist:
        return Response({"error": "not found"}, status=404)

    results = scan.results or []
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=30, leftMargin=30, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    title_style = styles["Title"]

    elements = []

    # HEADER: logos + tagline
    logo_left_path = "//Users/darshitayar/Desktop/VaptManagement /frontend/src/assets/OTlogo.jpg"
    logo_right_path = "/Users/darshitayar/Desktop/VaptManagement /frontend/src/assets/HomeIcon.png"

    try:
        logo_left = Image(logo_left_path, width=55, height=55)
        logo_right = Image(logo_right_path, width=70, height=70)
    except Exception:
        logo_left = Paragraph("", normal)
        logo_right = Paragraph("", normal)

    header_table = Table([
        [logo_left,
         Paragraph("<b>Orange Technolab Pvt Ltd<br/>ISO 9001 & 27001 Certified Company</b>", styles["Heading3"]),
         logo_right]
    ], colWidths=[70, 360, 70])
    header_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("ALIGN", (2, 0), (2, 0), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (1, 0), (1, 0), 10),
        ("RIGHTPADDING", (1, 0), (1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12)
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 60))  # more space below logos

    # Report title & meta
    elements.append(Paragraph("API Scan Report", title_style))
    elements.append(Spacer(1, 12))  # more space below title
    elements.append(Paragraph(f"Target: {scan.target}", normal))
    elements.append(Paragraph(f"Scan ID: {scan.id}", normal))
    elements.append(Paragraph(f"Created: {scan.created_at}", normal))
    if scan.finished_at:
        elements.append(Paragraph(f"Finished: {scan.finished_at}", normal))
    elements.append(Spacer(1, 12))

    if not results:
        elements.append(Paragraph("No vulnerabilities found or scan still running.", normal))
    else:
        data = [["Date", "Vulnerability", "CVE", "Priority", "URL/Path", "Suggestion"]]
        for r in results:
            created = str(scan.created_at)
            vuln = r.get("alert", "")
            cve = r.get("cve", "")
            priority = r.get("priority", "")
            url = r.get("url", "") or ""
            suggestion = r.get("suggestion", "") or (r.get("solution","") or "")

            if priority.lower() == "high":
                bg_color = colors.HexColor("#fb948b")
            elif priority.lower() == "medium":
                bg_color = colors.HexColor("#f9e6a8")
            else:
                bg_color = colors.HexColor("#dff6c5")

            data.append([
                Paragraph(created, normal),
                Paragraph(vuln, normal),
                Paragraph(cve, normal),
                Paragraph(priority, normal),
                Paragraph(url, normal),
                Paragraph(suggestion, normal),
                bg_color
            ])

        col_widths = [70, 120, 70, 60, 140, 120]
        table = Table([row[:-1] for row in data], colWidths=col_widths, repeatRows=1)

        table_style = TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d1b2a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ])

        for i, row in enumerate(data[1:], start=1):
            table_style.add("BACKGROUND", (0, i), (-1, i), row[-1])

        table.setStyle(table_style)
        elements.append(table)

    # Footer & background
    def add_page(canvas, doc):
        canvas.saveState()
        # Background color
        canvas.setFillColor(colors.HexColor("#f6f6f6"))
        canvas.rect(0, 0, doc.pagesize[0], doc.pagesize[1], stroke=0, fill=1)
        # Footer on top
        footer_text = "www.orangetechnolab.com | +91 88660 68968 | sales@orangewebtech.com"
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(colors.black)  # ensure footer text is visible
        canvas.drawCentredString(doc.pagesize[0]/2, 20, footer_text)

        # --- Draw small 3mm x 3mm color blocks legend above footer (bottom-right corner) ---
        block_size = 8  # ~3mm in points
        padding = 5
        start_x = doc.pagesize[0] - 140  # 140pts from left
        start_y = 40  # above footer

        canvas.setFillColor(colors.HexColor("#fb948b"))
        canvas.rect(start_x, start_y, block_size, block_size, fill=1, stroke=0)
        canvas.setFillColor(colors.black)
        canvas.setFont("Helvetica", 7)
        canvas.drawString(start_x + block_size + 2, start_y, "High Risk")

        canvas.setFillColor(colors.HexColor("#f9e6a8"))
        canvas.rect(start_x, start_y + block_size + 2, block_size, block_size, fill=1, stroke=0)
        canvas.setFillColor(colors.black)
        canvas.drawString(start_x + block_size + 2, start_y + block_size + 2, "Medium Risk")

        canvas.setFillColor(colors.HexColor("#dff6c5"))
        canvas.rect(start_x, start_y + 2*(block_size + 2), block_size, block_size, fill=1, stroke=0)
        canvas.setFillColor(colors.black)
        canvas.drawString(start_x + block_size + 2, start_y + 2*(block_size + 2), "Low Risk")



        canvas.restoreState()


    doc.build(elements, onFirstPage=add_page, onLaterPages=add_page)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"api_scan_report_{scan_id}.pdf")


@api_view(["GET"])
def past_scans(request):
    """
    Returns list of past API scans that completed successfully, latest first.
    Failed or running scans are excluded.
    """
    scans = APIScan.objects.filter(status="finished").order_by('-created_at')
    serializer = APIScanSerializer(scans, many=True)
    return Response(serializer.data)