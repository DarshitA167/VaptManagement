import socket
import requests
from urllib.parse import urlparse
from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
import json, io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

@csrf_exempt
def scan_domain(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        raw_domain = data.get("domain")

        if not raw_domain:
            return JsonResponse({"error": "Domain is required"}, status=400)

        # --- Normalize domain ---
        parsed = urlparse(raw_domain if "://" in raw_domain else f"http://{raw_domain}")
        scheme = parsed.scheme or "http"
        domain = parsed.netloc or parsed.path
        base_url = f"{scheme}://{domain}"

        result = {"input": raw_domain, "domain": domain, "scheme": scheme, "base_url": base_url}

        # --- Get IP address ---
        try:
            ip = socket.gethostbyname(domain)
            result["ip"] = ip
        except Exception as e:
            result["ip_error"] = str(e)

        # --- Get HTTP headers ---
        try:
            response = requests.get(base_url, timeout=5)
            result["status_code"] = response.status_code
            result["headers"] = dict(response.headers)
        except Exception as e:
            result["http_error"] = str(e)

        # --- PDF Generation ---
        if data.get("download_pdf"):
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter,
                                    rightMargin=30, leftMargin=30, topMargin=40, bottomMargin=40)
            styles = getSampleStyleSheet()
            normal = styles["Normal"]
            title_style = styles["Title"]
            heading_style = styles["Heading2"]

            elements = []

            # HEADER: logos + tagline
            logo_left_path = "/Users/darshitayar/Desktop/VaptManagement /frontend/src/assets/OTlogo.jpg"
            logo_right_path = "/Users/darshitayar/Desktop/VaptManagement /frontend/src/assets/HomeIcon.png"

            try:
                logo_left = Image(logo_left_path, width=55, height=55)
            except Exception as e:
                print(f"Left logo not loaded: {e}")
                logo_left = Paragraph("", normal)

            try:
                logo_right = Image(logo_right_path, width=70, height=70)
            except Exception as e:
                print(f"Right logo not loaded: {e}")
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
            elements.append(Spacer(1, 60))  # space below logos

            # Report title & meta
            elements.append(Paragraph("🌐 Domain Scan Report", title_style))
            elements.append(Spacer(1, 12))

            info_data = [
                ["Input", result.get("input", "N/A")],
                ["Domain", result.get("domain", "N/A")],
                ["Scheme", result.get("scheme", "N/A")],
                ["Base URL", result.get("base_url", "N/A")],
                ["IP Address", result.get("ip", "N/A")],
                ["Status Code", result.get("status_code", "N/A")],
            ]
            table = Table(info_data, colWidths=[120, 400])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0d1b2a")),
                ("TEXTCOLOR", (0,0), (-1,0), colors.white),
                ("BOX", (0,0), (-1,-1), 1, colors.black),
                ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 20))

            # HTTP Headers
            if "headers" in result:
                elements.append(Paragraph("📌 HTTP Headers", heading_style))
                headers_data = [["Header", "Value"]] + [[k, v] for k, v in result["headers"].items()]
                headers_table = Table(headers_data, colWidths=[200, 320])
                headers_table.setStyle(TableStyle([
                    ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
                    ("GRID", (0,0), (-1,-1), 0.25, colors.black),
                    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                ]))
                elements.append(headers_table)

            # Footer & background
            def add_page(canvas, doc):
                canvas.saveState()
                # Background
                canvas.setFillColor(colors.HexColor("#f6f6f6"))
                canvas.rect(0, 0, doc.pagesize[0], doc.pagesize[1], stroke=0, fill=1)
                # Footer
                footer_text = "www.orangetechnolab.com | +91 88660 68968 | sales@orangewebtech.com"
                canvas.setFont("Helvetica", 9)
                canvas.setFillColor(colors.black)
                canvas.drawCentredString(doc.pagesize[0]/2, 20, footer_text)
                canvas.restoreState()

            doc.build(elements, onFirstPage=add_page, onLaterPages=add_page)
            buffer.seek(0)
            return FileResponse(buffer, as_attachment=True, filename=f"{domain}_report.pdf")

        return JsonResponse(result)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
