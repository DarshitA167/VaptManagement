from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.http import FileResponse
from datetime import datetime
import subprocess, xmltodict, io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from .models import NetworkScan
from .serializers import NetworkScanSerializer

# ---- Network Scan ----
@csrf_exempt
@api_view(["POST"])
def scan_network(request):
    ip = request.data.get("ip") or "127.0.0.1"
    ports = request.data.get("ports") or "1-1024"

    def norm(val, is_bool=False):
        if is_bool: return bool(val)
        if val is None: return "-"
        s = str(val).strip()
        return "-" if s == "" or s.lower() in ("n/a", "unknown") else s

    # Calculate timeout
    port_count = 1
    if "-" in str(ports):
        try:
            start, end = map(int, ports.split("-"))
            port_count = max(1, end - start + 1)
        except: pass
    timeout_val = 60 + int(port_count / 500) * 30

    nmap_args = ["nmap", "-T4", "--min-rate", "500", "-p", ports, "-oX", "-", ip]

    try:
        result = subprocess.run(nmap_args, capture_output=True, text=True, timeout=timeout_val)
        if result.returncode != 0 or not result.stdout.strip():
            return Response({"error": f"Nmap failed: {result.stderr}"}, status=500)

        xml_output = xmltodict.parse(result.stdout)
        hosts = xml_output.get("nmaprun", {}).get("host")
        if isinstance(hosts, dict): hosts = [hosts]
        scan_results = []

        if hosts:
            for host in hosts:
                host_addr = norm(host.get("address", {}).get("@addr"))
                ports_node = host.get("ports", {}).get("port", [])
                if isinstance(ports_node, dict): ports_node = [ports_node]
                if not ports_node:
                    scan_results.append({
                        "host": host_addr, "port": "-", "status": "-", "service": "-", "vulnerable": False, "cve": "-"
                    })
                    continue
                for port in ports_node:
                    scan_results.append({
                        "host": host_addr,
                        "port": norm(port.get("@portid")),
                        "status": norm(port.get("state", {}).get("@state")),
                        "service": norm(port.get("service", {}).get("@name")),
                        "vulnerable": False,
                        "cve": "-"
                    })

        # Save history in session for immediate frontend display
        history = request.session.get("scan_history", [])
        new_entry = {
            "ip": ip, "ports": ports,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "results": scan_results
        }
        history.append(new_entry)
        request.session["scan_history"] = history[-20:]
        request.session["scan_results"] = scan_results

        # Save in DB
        new_scan = NetworkScan.objects.create(ip=ip, ports=ports, results=scan_results, status="finished")

        return Response({
    "results": scan_results,
    "history": history[-20:],
    "scan_id": new_scan.id  # <-- Add this line
})



    except subprocess.TimeoutExpired:
        return Response({"error": f"Nmap timed out after {timeout_val}s"}, status=500)
    except Exception as e:
        return Response({"error": str(e)}, status=500)



from rest_framework.decorators import api_view
from django.http import FileResponse
import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from .models import NetworkScan

@api_view(["GET"])
def download_pdf_report(request, scan_id):
    """
    Generate PDF report for a given network scan (from DB).
    """
    try:
        scan = NetworkScan.objects.get(id=scan_id)
        rows = scan.results  # assuming results is JSONField with list of dicts
    except NetworkScan.DoesNotExist:
        rows = []

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
    elements = []

    # Optional logos
    LOGO_LEFT_PATH = "/Users/darshitayar/Desktop/VaptManagement /frontend/src/assets/OTlogo.jpg"
    LOGO_RIGHT_PATH = "/Users/darshitayar/Desktop/VaptManagement /frontend/src/assets/HomeIcon.png"
    try:
        logo_left = Image(LOGO_LEFT_PATH, width=55, height=55)
        logo_right = Image(LOGO_RIGHT_PATH, width=70, height=70)
    except Exception:
        logo_left = Paragraph("", normal)
        logo_right = Paragraph("", normal)

    # Header table
    header_table = Table(
        [[logo_left,
          Paragraph("<b>Orange Technolab Pvt Ltd ISO 9001 & 27001 Certified Company<br/></b>", styles["Heading3"]),
          logo_right]],
        colWidths=[70, 360, 70]
    )
    header_table.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "MIDDLE")]))
    elements.append(header_table)
    elements.append(Spacer(1, 18))
    elements.append(Paragraph(f"Network Scan Report: {scan_id}", styles["Title"]))
    elements.append(Spacer(1, 12))

    # Build results table
    if not rows:
        elements.append(Paragraph("✅ No scan results found for this scan.", normal))
    else:
        data = [["Host", "Port", "Status", "Service", "Vulnerable", "CVE"]]
        for r in rows:
            data.append([
                Paragraph(str(r.get("host", "-")), normal),
                Paragraph(str(r.get("port", "-")), normal),
                Paragraph(str(r.get("status", "-")), normal),
                Paragraph(str(r.get("service", "-")), normal),
                Paragraph("Yes" if r.get("vulnerable") else "No", normal),
                Paragraph(str(r.get("cve", "-")), normal),
            ])
        table = Table(data, colWidths=[100, 40, 60, 100, 60, 100], repeatRows=1)
        style = TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0d1b2a")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
        ])
        table.setStyle(style)
        elements.append(table)

    # Footer
    def footer(canvas, doc):
        canvas.saveState()
        footer_text = "www.orangetechnolab.com"
        canvas.setFont("Helvetica", 9)
        canvas.drawCentredString(doc.pagesize[0]/2, 20, footer_text)
        canvas.restoreState()

    doc.build(elements, onFirstPage=footer, onLaterPages=footer)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"network_scan_report_{scan_id}.pdf")

# ---- Session History ----
@api_view(["GET"])
def get_scan_history(request):
    history = request.session.get("scan_history", []) or []
    return Response({"history": history})


# ---- Past scans from DB ----
@api_view(["GET"])
def past_network_scans(request):
    scans = NetworkScan.objects.filter(status="finished").order_by('-created_at')
    serializer = NetworkScanSerializer(scans, many=True)
    return Response(serializer.data)
