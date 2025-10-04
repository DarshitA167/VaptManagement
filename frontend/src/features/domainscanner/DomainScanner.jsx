import React, { useState, useEffect } from "react";
import axios from "axios";
import "../../styles/domainscanner.css";
import GameModal from "../../components/Game/GameModal";

const DomainScanner = () => {
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
    setLoading(true);
    setResult(null);
    try {
      const res = await axios.post("http://127.0.0.1:8000/api/domainscanner/scan/", { domain });
      setResult(res.data);
    } catch (error) {
      setResult({ error: error.message });
    }
    setLoading(false);
  };

  const handleDownload = async () => {
    try {
      const res = await axios.post(
        "http://127.0.0.1:8000/api/domainscanner/scan/",
        { domain, download_pdf: true },
        { responseType: "blob" }
      );
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `${domain}_report.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch {
      alert("Failed to download PDF");
    }
  };

  return (
    <div className="scanner-container">
      <h2> Domain Scanner</h2>
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
          <pre>{JSON.stringify(result, null, 2)}</pre>
          <button onClick={handleDownload}>📥 Download PDF Report</button>
        </div>
      )}

      <GameModal open={showGame} onClose={() => setShowGame(false)} />
    </div>
  );
};

export default DomainScanner;
