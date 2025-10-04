from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from django.http import FileResponse, JsonResponse
import subprocess, xmltodict, io, datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

RESULT_FIELDS = ("host", "port", "status", "service", "vulnerable", "cve", "date")

# global cache (instead of session)
LATEST_RESULTS = []

@csrf_exempt
@api_view(["POST"])
def scan_network(request):
    target = request.data.get("ip") or "127.0.0.1"
    ports = request.data.get("ports") or "1-1024"

    def norm(value):
        if value is None:
            return "-"
        s = str(value).strip()
        return "-" if s in ("", "n/a", "unknown") else s

    try:
        result = subprocess.run(
            ["nmap", "-p", ports, "-oX", "-", target],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode != 0 or not result.stdout.strip():
            return Response({"error": f"Nmap failed: {result.stderr}"}, status=500)

        xml_output = xmltodict.parse(result.stdout)
        hosts = xml_output.get("nmaprun", {}).get("host")
        if not hosts:
            return Response({"results": []})

        if isinstance(hosts, dict):
            hosts = [hosts]

        all_results = []
        for host in hosts:
            host_addr = "-"
            if "address" in host:
                if isinstance(host["address"], list):
                    host_addr = host["address"][0].get("@addr", "-")
                else:
                    host_addr = host["address"].get("@addr", "-")

            ports_node = host.get("ports", {}).get("port", [])
            if isinstance(ports_node, dict):
                ports_node = [ports_node]

            if not ports_node:
                all_results.append({
                    "host": host_addr,
                    "port": "-",
                    "status": "-",
                    "service": "-",
                    "vulnerable": False,
                    "cve": "-",
                    "date": str(datetime.date.today())
                })
                continue

            for port in ports_node:
                all_results.append({
                    "host": host_addr,
                    "port": norm(port.get("@portid")),
                    "status": norm(port.get("state", {}).get("@state")),
                    "service": norm(port.get("service", {}).get("@name")),
                    "vulnerable": False,
                    "cve": "-",
                    "date": str(datetime.date.today())
                })

        global LATEST_RESULTS
        LATEST_RESULTS = all_results
        return Response({"results": all_results})

    except subprocess.TimeoutExpired:
        return Response({"error": "Nmap timed out"}, status=500)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import FileResponse
import io, datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from .views import LATEST_RESULTS  # make sure this imports the global results from your scan_network view


@api_view(["GET"])
def download_pdf_report(request):
    results = LATEST_RESULTS or []
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=30, leftMargin=30, topMargin=40, bottomMargin=40)

    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    title_style = styles["Title"]
    heading_style = styles["Heading2"]

    elements = []

    # HEADER: logos + company
    logo_left_path = "/Users/darshitayar/Desktop/VaptManagement /frontend/src/assets/OTlogo.jpg"
    logo_right_path = "/Users/darshitayar/Desktop/VaptManagement /frontend/src/assets/HomeIcon.png"

    try:
        logo_left = Image(logo_left_path, width=55, height=55)
    except Exception:
        logo_left = Paragraph("", normal)
    try:
        logo_right = Image(logo_right_path, width=70, height=70)
    except Exception:
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

    # Title
    elements.append(Paragraph("🖧 Network Scan Report", title_style))
    elements.append(Spacer(1, 12))

    if not results:
        elements.append(Paragraph("No scan results available. Please run a scan first.", normal))
    else:
        # Table header
        data = [["Host", "Port", "Status", "Service", "Vulnerable", "CVE ID", "Date"]]
        for r in results:
            data.append([
                r.get("host", "-"),
                r.get("port", "-"),
                r.get("status", "-"),
                r.get("service", "-"),
                "Yes" if r.get("vulnerable") else "No",
                r.get("cve", "-"),
                r.get("date", "-"),
            ])

        col_widths = [80, 50, 60, 90, 60, 80, 80]
        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0d1b2a")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,0), 10),
            ("BOTTOMPADDING", (0,0), (-1,0), 6),
            ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
        ]))
        elements.append(table)

    # Footer + background
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
    return FileResponse(buffer, as_attachment=True, filename="network_scan_report.pdf")
