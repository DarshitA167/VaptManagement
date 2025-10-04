import React, { useState, useEffect } from "react";
import "../../styles/networkscanner.css";

function NetworkScanner() {
  const [ip, setIp] = useState("");
  const [ports, setPorts] = useState("1-1024");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleScan = async () => {
    setLoading(true);
    setError("");
    setResults([]);

    try {
      const response = await fetch("http://localhost:8000/api/networkscanner/scan/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ip: ip || "127.0.0.1", ports })
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Scan failed");
      setResults(data.results || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPDF = () => {
    window.open("http://localhost:8000/api/networkscanner/download-pdf/", "_blank");
  };

  return (
    <div className="networkscanner-container">
      <h1>Network Scanner</h1>
      <div className="scanner-form">
        <input
          type="text"
          placeholder="Enter IP address"
          value={ip}
          onChange={(e) => setIp(e.target.value)}
        />
        <input
          type="text"
          placeholder="Ports (e.g., 1-1024)"
          value={ports}
          onChange={(e) => setPorts(e.target.value)}
        />
        <button onClick={handleScan} disabled={loading}>
          {loading ? "Scanning..." : "Scan"}
        </button>
        {results.length > 0 && (
          <button onClick={handleDownloadPDF} className="download-btn">
            Download PDF Report
          </button>
        )}
      </div>

      {error && <p className="error-message">{error}</p>}

      {results.length > 0 && (
        <div className="results-table">
          <h2>Scan Results</h2>
          <table>
            <thead>
              <tr>
                <th>Host</th>
                <th>Port</th>
                <th>Status</th>
                <th>Service</th>
                <th>Vulnerable</th>
                <th>CVE ID</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r, idx) => (
                <tr key={idx}>
                  <td>{r.host}</td>
                  <td>{r.port}</td>
                  <td>{r.status}</td>
                  <td>{r.service}</td>
                  <td>{r.vulnerable ? "Yes" : "No"}</td>
                  <td>{r.cve}</td>
                  <td>{r.date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default NetworkScanner;
