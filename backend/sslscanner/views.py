# backend/sslscanner/views.py
import socket
import ssl
import datetime
import traceback
import io
import base64

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

# Try to import cryptography
try:
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.backends import default_backend
    HAS_CRYPTO = True
except Exception:
    HAS_CRYPTO = False

# PDF libraries
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet


def _normalize_domain(raw: str) -> str:
    if not isinstance(raw, str):
        return ""
    domain = raw.strip()
    if "://" in domain:
        domain = domain.split("://", 1)[1]
    domain = domain.split("/", 1)[0]
    return domain


def _connect_and_get_der(domain: str, port: int = 443, timeout: float = 6.0):
    """
    Try to connect (IPv4/IPv6) and return (der_bytes, tls_version).
    Raises ConnectionError on failure with last exception message.
    """
    last_exc = None
    try:
        infos = socket.getaddrinfo(domain, port, proto=socket.IPPROTO_TCP)
    except Exception as e:
        raise ConnectionError(f"DNS/getaddrinfo failed: {e}")

    for af, socktype, proto, canonname, sa in infos:
        sock = None
        ss = None
        try:
            sock = socket.socket(af, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            ss = ctx.wrap_socket(sock, server_hostname=domain)
            ss.connect(sa)
            der = ss.getpeercert(binary_form=True)
            tls_version = ss.version()
            try:
                ss.close()
            except Exception:
                pass
            return der, tls_version
        except Exception as e:
            last_exc = e
            try:
                if ss:
                    ss.close()
            except Exception:
                pass
            try:
                if sock:
                    sock.close()
            except Exception:
                pass
            continue

    raise ConnectionError(f"Could not connect to target ({last_exc})")


def _parse_cert_with_cryptography(der_bytes):
    """
    Returns parsed info including original datetime objects under keys:
      - not_before_dt, not_after_dt
    and ISO strings under not_before, not_after.
    """
    cert = x509.load_der_x509_certificate(der_bytes, default_backend())

    # Subject CN (if exists)
    subject_cn = ""
    try:
        vals = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
        subject_cn = vals[0].value if vals else ""
    except Exception:
        subject_cn = ""

    # Issuer
    issuer_name = ""
    try:
        vals = cert.issuer.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)
        issuer_name = vals[0].value if vals else ""
    except Exception:
        try:
            vals2 = cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)
            issuer_name = vals2[0].value if vals2 else ""
        except Exception:
            issuer_name = ""

    not_before_dt = cert.not_valid_before
    not_after_dt = cert.not_valid_after

    # SANs
    san = []
    try:
        ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
        san = ext.value.get_values_for_type(x509.DNSName)
    except Exception:
        san = []

    return {
        "subject_cn": subject_cn,
        "issuer": issuer_name,
        "not_before_dt": not_before_dt,
        "not_after_dt": not_after_dt,
        "not_before": not_before_dt.isoformat(),
        "not_after": not_after_dt.isoformat(),
        "san": san,
        "raw_cert": cert,
    }


def _parse_cert_fallback(pycert):
    """
    Fallback using ssl.getpeercert() dict. We keep strings and None for datetimes.
    """
    subject = pycert.get("subject", ())
    issuer = pycert.get("issuer", ())

    def extract_first_name(tuples):
        for t in tuples:
            if isinstance(t, (tuple, list)) and len(t) and isinstance(t[0], (tuple, list)):
                try:
                    return dict(t[0]).get("commonName") or dict(t[0]).get("organizationName") or ""
                except Exception:
                    continue
        return ""

    subject_cn = extract_first_name(subject)
    issuer_name = extract_first_name(issuer)
    not_before = pycert.get("notBefore")
    not_after = pycert.get("notAfter")
    san = [x[1] for x in pycert.get("subjectAltName", []) if x[0].lower() == "dnsname"]

    # parsed contains no datetime objects in fallback
    return {
        "subject_cn": subject_cn,
        "issuer": issuer_name,
        "not_before_dt": None,
        "not_after_dt": None,
        "not_before": not_before,
        "not_after": not_after,
        "san": san,
        "raw_cert": None,
    }


def _check_supported_tls_versions(domain: str, port: int = 443, timeout: float = 3.0):
    """
    Try to connect forcing specific TLS versions (best-effort). Returns list like ['TLSv1.3','TLSv1.2'].
    """
    supported = []
    candidates = []
    if hasattr(ssl, "TLSVersion"):
        tv = ssl.TLSVersion
        candidates = [
            (tv.TLSv1_3, "TLSv1.3"),
            (tv.TLSv1_2, "TLSv1.2"),
            (tv.TLSv1_1, "TLSv1.1"),
            (tv.TLSv1, "TLSv1.0"),
        ]
    else:
        # older Python fallback: we'll still attempt a normal connect (best-effort)
        candidates = [(None, "TLSv1.2"), (None, "TLSv1.1"), (None, "TLSv1.0")]

    for ver_obj, label in candidates:
        try:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            if ver_obj is not None and hasattr(ctx, "minimum_version"):
                ctx.minimum_version = ctx.maximum_version = ver_obj
            s = socket.create_connection((domain, port), timeout=timeout)
            ss = ctx.wrap_socket(s, server_hostname=domain)
            # if handshake succeeds, consider label supported
            ss.close()
            supported.append(label)
        except Exception:
            continue

    # keep order and uniqueness
    seen = set()
    out = []
    for v in supported:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


def _generate_vulns(parsed_cert, supported_tls_versions, domain):
    """
    Robust vulnerability derivation:
      - checks expiry (handles datetimes or ISO strings)
      - missing SAN
      - deprecated TLS versions
      - missing TLS1.3 (informational)
      - self-signed cert
    """
    vulns = []
    now = datetime.datetime.utcnow()

    # parse not_after (prefer datetime)
    not_after_dt = parsed_cert.get("not_after_dt")
    if not isinstance(not_after_dt, datetime.datetime):
        # try parse ISO string if present
        not_after_str = parsed_cert.get("not_after")
        if isinstance(not_after_str, str):
            try:
                not_after_dt = datetime.datetime.fromisoformat(not_after_str)
            except Exception:
                not_after_dt = None
        else:
            not_after_dt = None

    if isinstance(not_after_dt, datetime.datetime):
        days_left = (not_after_dt - now).days
        if days_left < 0:
            vulns.append({"id": "CERT-EXPIRED", "priority": "high", "desc": f"Certificate expired {abs(days_left)} days ago", "suggestion": "Renew certificate"})
        elif days_left <= 30:
            vulns.append({"id": "CERT-EXPIRES-SOON", "priority": "medium", "desc": f"Certificate expires in {days_left} days", "suggestion": "Rotate certificate soon"})

    # Deprecated TLS support
    for v in supported_tls_versions:
        if v in ("TLSv1.0", "TLSv1.1"):
            vulns.append({"id": "TLS-DEPRECATED", "priority": "high", "desc": f"Server accepts deprecated TLS version {v}", "suggestion": "Disable TLS 1.0/1.1"})

    # Inform if TLS1.3 missing (not a blocker, but useful)
    if "TLSv1.3" not in supported_tls_versions and "TLSv1.2" in supported_tls_versions:
        vulns.append({"id": "TLS-NO-1.3", "priority": "low", "desc": "Server supports TLSv1.2 but not TLSv1.3", "suggestion": "Consider enabling TLS1.3"})

    # missing SAN but has CN
    san = parsed_cert.get("san") or []
    subject_cn = parsed_cert.get("subject_cn") or ""
    if not san and subject_cn:
        # sometimes CN-only certs are older and not ideal
        vulns.append({"id": "CERT-NO-SAN", "priority": "low", "desc": "Certificate uses CN but has no SAN entries", "suggestion": "Reissue with SAN"})

    # self-signed detection (if cryptography raw_cert present)
    raw = parsed_cert.get("raw_cert")
    try:
        if raw is not None:
            if raw.issuer == raw.subject:
                vulns.append({"id": "CERT-SELF-SIGNED", "priority": "high", "desc": "Certificate appears to be self-signed", "suggestion": "Use CA-signed certificate"})
    except Exception:
        pass

    # hostname mismatch (best-effort): check if domain in SANs or equals CN (simple)
    mismatch = True
    if san:
        # check direct equality or wildcard simple match
        for s in san:
            if s == domain or (s.startswith("*.") and domain.endswith(s[2:])):
                mismatch = False
                break
    else:
        if subject_cn:
            if subject_cn == domain or (subject_cn.startswith("*.") and domain.endswith(subject_cn[2:])):
                mismatch = False

    if mismatch:
        # Not always a vulnerability (some servers use different names), but report as info/low
        vulns.append({"id": "CERT-HOST-MISMATCH", "priority": "low", "desc": "Certificate hostname does not match scanned domain", "suggestion": "Ensure certificate SAN/CN includes the domain"})

    return vulns

from rest_framework.response import Response
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# --- Update these paths to your local logo files ---
LOGO_LEFT_PATH = "/Users/darshitayar/Desktop/VaptManagement /frontend/src/assets/OTlogo.jpg"
LOGO_RIGHT_PATH = "/Users/darshitayar/Desktop/VaptManagement /frontend/src/assets/HomeIcon.png"

def _generate_pdf(domain, parsed, tls_version, supported_versions, vulns):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=40, bottomMargin=40
    )
    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    title_style = styles["Title"]
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
    elements.append(Spacer(1, 50))  # space below logos

    # --- Report Title ---
    elements.append(Paragraph(f"SSL Report: {domain}", title_style))
    elements.append(Spacer(1, 12))

    # --- Certificate Details Table ---
    cert_data = [
        ['Field', 'Value'],
        ['Issuer', parsed.get('issuer') or ''],
        ['Subject', parsed.get('subject_cn') or ''],
        ['Valid From', parsed.get('not_before') or 'N/A'],
        ['Valid To', parsed.get('not_after') or 'N/A'],
        ['Handshake TLS Version', tls_version or 'unknown'],
        ['Supported TLS Versions', ', '.join(supported_versions) or 'N/A'],
        ['Subject Alternative Names', ', '.join(parsed.get('san') or []) or 'N/A'],
    ]
    table = Table(cert_data, colWidths=[150, 350])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7f7f7')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 18))

    # --- Vulnerabilities ---
    elements.append(Paragraph("<b>Vulnerabilities:</b>", styles['Heading2']))
    if vulns:
        for v in vulns:
            elements.append(
                Paragraph(
                    f"<b>[{v.get('priority','INFO').upper()}]</b> {v.get('desc')}. Suggestion: {v.get('suggestion','-')}",
                    normal
                )
            )
            elements.append(Spacer(1, 6))
    else:
        elements.append(Paragraph("No vulnerabilities detected.", normal))

    # --- Footer & Background ---
    def add_page(canvas, doc):
        canvas.saveState()
        # background
        canvas.setFillColor(colors.HexColor("#f6f6f6"))
        canvas.rect(0, 0, doc.pagesize[0], doc.pagesize[1], stroke=0, fill=1)
        # footer
        footer_text = "www.orangetechnolab.com | +91 88660 68968 | sales@orangewebtech.com"
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(colors.black)
        canvas.drawCentredString(doc.pagesize[0]/2, 20, footer_text)
        canvas.restoreState()

    doc.build(elements, onFirstPage=add_page, onLaterPages=add_page)
    buffer.seek(0)
    return buffer


@api_view(["POST"])
def scan_ssl(request):
    import json
    import base64
    import traceback
    try:
        domain_raw = request.data.get("domain", "")
        if not domain_raw:
            return Response({"error": "Domain required"}, status=400)

        domain = domain_raw.strip()

        # --- Mock certificate parsing for example ---
        parsed = {
            "issuer": "Let's Encrypt",
            "subject_cn": domain,
            "not_before": "2025-01-01",
            "not_after": "2026-01-01",
            "san": [domain, f"www.{domain}"]
        }
        tls_version = "TLS 1.3"
        supported_versions = ["TLS 1.0", "TLS 1.1", "TLS 1.2", "TLS 1.3"]
        vulns = [
            {"priority": "high", "desc": "Weak cipher enabled", "suggestion": "Disable weak ciphers"}
        ]

        # --- Generate PDF ---
        # --- Generate PDF ---
        pdf_buffer = _generate_pdf(domain, parsed, tls_version, supported_versions, vulns)
        pdf_base64 = base64.b64encode(pdf_buffer.getvalue()).decode("utf-8")

        # --- Full readable result ---
        readable_result = {
            "domain": domain,
            "issuer": parsed.get("issuer"),
            "subject": parsed.get("subject_cn"),
            "subject_alt_names": parsed.get("san"),
            "valid_from": parsed.get("not_before"),
            "valid_to": parsed.get("not_after"),
            "tls_version": tls_version,
            "supported_tls_versions": supported_versions,
            "vulnerabilities": vulns
        }

        # --- Save history ---
        save_scan_history(domain, "success", readable_result, pdf_base64)

        # Return response with PDF for immediate download
        return Response({"result": readable_result, "pdf_base64": pdf_base64})


    except Exception as exc:
        traceback.print_exc()
        return Response({"error": f"Unexpected error: {exc}"}, status=500)


from .models import SSLScan
from .serializers import SSLScanSerializer

# 🧠 After your scan function successfully completes
def save_scan_history(domain, status, result_dict, pdf_base64):
    SSLScan.objects.create(
        domain=domain,
        status=status,
        expiry_date=result_dict.get("valid_to"),
        issuer=result_dict.get("issuer"),
        tls_version=result_dict.get("tls_version"),
        pdf_report=pdf_base64,          # store PDF as base64
        result_json=result_dict          # store full result
    )



# 🔍 API to get past scans
@api_view(["GET"])
def get_scan_history(request):
    scans = SSLScan.objects.all().order_by("-scan_date")[:20]  # last 20 scans
    serializer = SSLScanSerializer(scans, many=True)
    return Response(serializer.data)
