import React, { useState, useEffect } from "react";
import "../../styles/apiscanner.css";
import { useScan } from "../../context/ScanContext";
import GameModal from "../../components/Game/GameModal";

const API_BASE = "http://localhost:8000/api/apiscanner";

export default function ApiScanner() {
  const { setScanRunning, setScanId } = useScan();
  const [targetUrl, setTargetUrl] = useState("");
  const [scanId, localSetScanId] = useState("");
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState([]);
  const [results, setResults] = useState([]);
  const [message, setMessage] = useState("");
  const [showGame, setShowGame] = useState(false);

  useEffect(() => {
    if (loading) {
      const timer = setTimeout(() => setShowGame(true), 5000);
      return () => clearTimeout(timer);
    }
  }, [loading]);

  useEffect(() => {
    let poll;
    if (scanId) {
      poll = setInterval(async () => {
        try {
          const res = await fetch(`${API_BASE}/status/${scanId}/`);
          const d = await res.json();
          if (res.ok) {
            setProgress(d.progress || []);
            if (d.status === "finished") {
              const rr = await fetch(`${API_BASE}/results/${scanId}/`);
              const rd = await rr.json();
              setResults(rd.results || []);
              setMessage(`Scan finished: ${rd.results.length} alerts`);
              setLoading(false);
              setScanRunning(false);
              clearInterval(poll);
            } else if (d.status === "error") {
              setMessage(`Scan error: ${d.error || "unknown"}`);
              setLoading(false);
              setScanRunning(false);
              clearInterval(poll);
            } else {
              setMessage("Scan running...");
            }
          } else {
            setMessage(d.error || "Failed to get status");
            setLoading(false);
            setScanRunning(false);
            clearInterval(poll);
          }
        } catch (err) {
          setMessage("Network error while polling status.");
          setLoading(false);
          setScanRunning(false);
          clearInterval(poll);
        }
      }, 2000);
    }
    return () => clearInterval(poll);
  }, [scanId]);

  const startScan = async (e) => {
    e.preventDefault();
    if (!targetUrl.trim()) {
      setMessage("Please enter an API base URL to scan.");
      return;
    }
    setLoading(true);
    setMessage("⚠️ Don't switch tabs or let the screen turn off during scan.");
    setResults([]);
    setProgress([]);
    setScanRunning(true);

    try {
      const res = await fetch(`${API_BASE}/scan/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target: targetUrl }),
      });
      const d = await res.json();
      if (!res.ok) {
        setMessage(d.error || "Failed to start scan");
        setLoading(false);
        setScanRunning(false);
        return;
      }
      localSetScanId(d.scan_id);
      setScanId && setScanId(d.scan_id);
    } catch (err) {
      setMessage("Network error starting scan");
      setLoading(false);
      setScanRunning(false);
    }
  };

  const downloadPdf = () => {
    if (!scanId) return;
    window.open(`${API_BASE}/download-pdf/${scanId}/`, "_blank");
  };

  const getPercent = () => {
    if (!progress || progress.length === 0) return 0;
    const active = progress.find(p => p.stage === "active_scan");
    const spider = progress.find(p => p.stage === "spider");
    const pick = active || spider || progress[progress.length-1];
    const val = (pick && pick.status) ? pick.status : "0%";
    return val === "done" ? 100 : parseInt(String(val).replace("%","")) || 0;
  };

  return (
    <div className="apiscanner-container">
      <h1>API Scanner</h1>
      <form onSubmit={startScan} className="apiscanner-form">
        <label>API Base URL</label>
        <input value={targetUrl} onChange={(e) => setTargetUrl(e.target.value)} placeholder="https://api.example.com" />
        <div className="buttons">
          <button type="submit" disabled={loading}>{loading ? "Scanning..." : "Start Scan"}</button>
          <button type="button" onClick={downloadPdf} disabled={!results.length}>Download PDF</button>
        </div>
      </form>

      {message && <div className={message.toLowerCase().includes("error") ? "error" : "info"}>{message}</div>}

      <div className="progress-area">
        <label>Overall progress</label>
        <div className="progress-line">
          <div className="progress-line-fill" style={{ width: `${getPercent()}%` }} />
        </div>
        <div className="progress-percent">{getPercent()}%</div>
      </div>

      <div className="progress-details">
        {progress.map((p, i) => (
          <div className="progress-row" key={i}>
            <strong>{p.stage}</strong> — <span>{p.status}</span>
          </div>
        ))}
      </div>

      <div className="results-wrapper">
        {results.length > 0 && (
          <>
            <h2>Vulnerabilities</h2>
            <table className="results-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Vulnerability</th>
                  <th>CVE</th>
                  <th>Priority</th>
                  <th>Path/URL</th>
                  <th>Suggestion</th>
                </tr>
              </thead>
              <tbody>
                {results.map((r, idx) => (
                  <tr key={idx}>
                    <td>{new Date().toLocaleString()}</td>
                    <td>{r.alert}</td>
                    <td>{r.cve || "-"}</td>
                    <td className={`priority ${r.priority}`}>{r.priority}</td>
                    <td className="wrap">{r.url}</td>
                    <td className="wrap">{r.suggestion}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
      </div>

      {/* Game modal */}
      <GameModal open={showGame} onClose={() => setShowGame(false)} />
    </div>
  );
}
