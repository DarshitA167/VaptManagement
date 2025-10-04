// frontend-fixed/src/features/sslscanner/SSLScanner.jsx
import React, { useState, useEffect } from "react";
import axios from "axios";
import "../../styles/sslscanner.css";
import GameModal from "../../components/Game/GameModal";

const SSLScanner = () => {
  const [domain, setDomain] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showGame, setShowGame] = useState(false);

  useEffect(() => {
    if (loading) {
      const timer = setTimeout(() => setShowGame(true), 5000);
      return () => clearTimeout(timer);
    }
  }, [loading]);

  const handleScan = async () => {
    if (!domain) return alert("Enter a domain (example.com)");
    setLoading(true);
    setResult(null);
    try {
      const res = await axios.post("http://127.0.0.1:8000/api/sslscanner/scan/", { domain });
      setResult(res.data);
    } catch (error) {
      setResult({ error: error.response?.data?.error || error.message });
    }
    setLoading(false);
  };

  const handleDownload = () => {
    if (!result?.pdf_base64) return alert("No PDF available");
    // convert base64 to blob and trigger download (safer for larger files)
    const binary = atob(result.pdf_base64);
    const len = binary.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    const blob = new Blob([bytes], { type: "application/pdf" });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `${domain.replace(/\./g,'_')}_ssl_report.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="scanner-container">
      <h2>🔒 SSL Scanner</h2>
      <div className="scanner-form">
        <input
          type="text"
          placeholder="Enter domain (example.com)"
          value={domain}
          onChange={(e) => setDomain(e.target.value)}
        />
        <button onClick={handleScan} disabled={loading}>
          {loading ? "Scanning..." : "Scan"}
        </button>
      </div>

      {result && (
        <div className="result">
          {result.error ? (
            <div style={{ color: "crimson" }}>{result.error}</div>
          ) : (
            <>
              <h3>Result</h3>
              <table style={{ borderCollapse: "collapse", width: "100%" }}>
                <tbody>
                  <tr>
                    <td style={{ fontWeight: "bold", width: 200 }}>Domain</td>
                    <td>{result.result.domain}</td>
                  </tr>
                  <tr>
                    <td style={{ fontWeight: "bold" }}>Issuer</td>
                    <td>{result.result.issuer}</td>
                  </tr>
                  <tr>
                    <td style={{ fontWeight: "bold" }}>Subject</td>
                    <td>{result.result.subject}</td>
                  </tr>
                  <tr>
                    <td style={{ fontWeight: "bold" }}>Valid From</td>
                    <td>{result.result.valid_from}</td>
                  </tr>
                  <tr>
                    <td style={{ fontWeight: "bold" }}>Valid To</td>
                    <td>{result.result.valid_to}</td>
                  </tr>
                  <tr>
                    <td style={{ fontWeight: "bold" }}>Handshake TLS</td>
                    <td>{result.result.tls_version}</td>
                  </tr>
                  <tr>
                    <td style={{ fontWeight: "bold" }}>Supported TLS</td>
                    <td>{(result.result.supported_tls_versions || []).join(", ")}</td>
                  </tr>
                  <tr>
                    <td style={{ fontWeight: "bold" }}>SANs</td>
                    <td>{(result.result.subject_alt_names || []).join(", ") || "N/A"}</td>
                  </tr>
                </tbody>
              </table>

              <h4 style={{ marginTop: 12 }}>Vulnerabilities</h4>
              {result.result.vulnerabilities && result.result.vulnerabilities.length ? (
                <ul>
                  {result.result.vulnerabilities.map((v, idx) => (
                    <li key={idx}>
                      <b>[{(v.priority || "info").toUpperCase()}]</b> {v.desc} {v.suggestion ? ` — ${v.suggestion}` : ""}
                    </li>
                  ))}
                </ul>
              ) : (
                <div>No vulnerabilities detected.</div>
              )}

              <button onClick={handleDownload} style={{ marginTop: 12 }}>
                📥 Download PDF Report
              </button>
            </>
          )}
        </div>
      )}

      <GameModal open={showGame} onClose={() => setShowGame(false)} />
    </div>
  );
};

export default SSLScanner;
