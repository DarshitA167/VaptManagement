import socket
import requests
from urllib.parse import urlparse
import json
import io

from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from .models import DomainScan

@csrf_exempt
def scan_domain(request):
    """
    POST /api/domainscanner/scan/
    Body JSON: { "domain": "example.com", "download_pdf": true|false }
    - Performs a small domain probe (DNS -> IP, HTTP GET -> headers & status)
    - Saves the scan to DB (DomainScan)
    - If download_pdf is true, returns FileResponse with PDF, else returns JSON result
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        raw_domain = data.get("domain")
        if not raw_domain:
            return JsonResponse({"error": "Domain is required"}, status=400)

        # Normalize domain & base_url
        parsed = urlparse(raw_domain if "://" in raw_domain else f"http://{raw_domain}")
        scheme = parsed.scheme or "http"
        domain = parsed.netloc or parsed.path
        base_url = f"{scheme}://{domain}"

        result = {
            "input": raw_domain,
            "domain": domain,
            "scheme": scheme,
            "base_url": base_url,
        }

        # Get IP address
        try:
            ip = socket.gethostbyname(domain)
            result["ip"] = ip
        except Exception as e:
            result["ip_error"] = str(e)

        # Get HTTP headers & status
        try:
            resp = requests.get(base_url, timeout=5)
            result["status_code"] = resp.status_code
            # convert headers to normal dict (some header values are lists/objects)
            result["headers"] = {k: v for k, v in resp.headers.items()}
        except Exception as e:
            result["http_error"] = str(e)

        # Save the scan to DB (always save, even if PDF requested)
        try:
            scan_obj = DomainScan.objects.create(
                domain=domain,
                ip=result.get("ip"),
                status_code=result.get("status_code"),
                results=result
            )
        except Exception as db_e:
            # don't fail the whole process for DB write issues; just log in result
            result["db_error"] = str(db_e)
            scan_obj = None

        # If PDF requested, build and return PDF
        if data.get("download_pdf"):
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=30,
                leftMargin=30,
                topMargin=40,
                bottomMargin=40
            )
            styles = getSampleStyleSheet()
            normal = styles["Normal"]
            title_style = styles["Title"]
            heading_style = styles["Heading2"]

            elements = []

            # Optional logos — if path is invalid, we'll fallback gracefully
            LOGO_LEFT_PATH = "/Users/darshitayar/Desktop/VaptManagement /frontend/src/assets/OTlogo.jpg"
            LOGO_RIGHT_PATH = "/Users/darshitayar/Desktop/VaptManagement /frontend/src/assets/HomeIcon.png"
            try:
                logo_left = Image(LOGO_LEFT_PATH, width=55, height=55)
            except Exception:
                logo_left = Paragraph("", normal)
            try:
                logo_right = Image(LOGO_RIGHT_PATH, width=70, height=70)
            except Exception:
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
            elements.append(Spacer(1, 40))

            # Title & meta
            elements.append(Paragraph("🌐 Domain Scan Report", title_style))
            elements.append(Spacer(1, 12))

            meta_data = [
                ["Input", result.get("input", "N/A")],
                ["Domain", result.get("domain", "N/A")],
                ["Scheme", result.get("scheme", "N/A")],
                ["Base URL", result.get("base_url", "N/A")],
                ["IP Address", result.get("ip", "N/A")],
                ["Status Code", result.get("status_code", "N/A")],
            ]
            meta_table = Table(meta_data, colWidths=[120, 360])
            meta_table.setStyle(TableStyle([
                ("BOX", (0,0), (-1,-1), 1, colors.black),
                ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ]))
            elements.append(meta_table)
            elements.append(Spacer(1, 12))

            # HTTP Headers section
            if result.get("headers"):
                elements.append(Paragraph("📌 HTTP Headers", heading_style))
                headers = result.get("headers", {})
                headers_data = [["Header", "Value"]] + [[k, str(v)] for k, v in headers.items()]
                headers_table = Table(headers_data, colWidths=[200, 280])
                headers_table.setStyle(TableStyle([
                    ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
                    ("GRID", (0,0), (-1,-1), 0.25, colors.black),
                    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                ]))
                elements.append(headers_table)
                elements.append(Spacer(1, 12))

            # Footer callback
            def add_page(canvas, doc):
                canvas.saveState()
                # optional soft background (comment out if unwanted)
                # canvas.setFillColor(colors.HexColor("#f6f6f6"))
                # canvas.rect(0, 0, doc.pagesize[0], doc.pagesize[1], stroke=0, fill=1)

                footer_text = "www.orangetechnolab.com | +91 88660 68968 | sales@orangewebtech.com"
                canvas.setFont("Helvetica", 9)
                canvas.setFillColor(colors.black)
                canvas.drawCentredString(doc.pagesize[0]/2, 20, footer_text)
                canvas.restoreState()

            doc.build(elements, onFirstPage=add_page, onLaterPages=add_page)
            buffer.seek(0)

            filename = f"{domain}_report.pdf"
            return FileResponse(buffer, as_attachment=True, filename=filename)

        # Not a PDF request — return JSON and include DB id if created
        response_payload = {"scan_saved_id": scan_obj.id if scan_obj else None, "result": result}
        return JsonResponse(response_payload)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_GET
def past_scans(request):
    """
    GET /api/domainscanner/past/
    Returns latest domain scans (most recent first).
    """
    try:
        scans = DomainScan.objects.all().order_by("-created_at")[:50]
        data = [
            {
                "id": s.id,
                "domain": s.domain,
                "ip": s.ip,
                "status_code": s.status_code,
                "headers": s.results.get("headers") if isinstance(s.results, dict) else None,
                "created_at": s.created_at.isoformat(),
                "results": s.results,
            }
            for s in scans
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
