import React, { useState, useEffect, useRef } from "react";
import "../../styles/webappscanner.css";
import { useScan } from "../../context/ScanContext";
import GameModal from "../../components/Game/GameModal";

const prettyStageLabel = {
  open_url: "Open URL",
  spider: "Spider",
  active_scan: "Active Scan",
};

const WebAppScanner = () => {
  const { setScanRunning, setScanId } = useScan();
  const [targetUrl, setTargetUrl] = useState("");
  const [scanId, localSetScanId] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [message, setMessage] = useState("");
  const [progress, setProgress] = useState({});
  const pollRef = useRef(null);

  // Game modal
  const [showGame, setShowGame] = useState(false);

  // Confirm modal
  const [showConfirmLeave, setShowConfirmLeave] = useState(false);
  const leaveEventRef = useRef(null);

  useEffect(() => {
    if (!loading) return;

    // Show popup after 5s
    const gameTimer = setTimeout(() => {
      setShowGame(true);
    }, 5000);

    const onBeforeUnload = (e) => {
      e.preventDefault();
      e.returnValue = "A scan is in progress. Are you sure you want to leave?";
    };
    window.addEventListener("beforeunload", onBeforeUnload);

    const clickInterceptor = (e) => {
      const a = e.target.closest && e.target.closest("a");
      if (!a) return;
      e.preventDefault();
      leaveEventRef.current = e;
      setShowConfirmLeave(true);
    };

    document.addEventListener("click", clickInterceptor, true);

    return () => {
      clearTimeout(gameTimer);
      window.removeEventListener("beforeunload", onBeforeUnload);
      document.removeEventListener("click", clickInterceptor, true);

      // 🛑 cleanup polling if component unmounts
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [loading]);

  const handleConfirmLeave = () => {
    setShowConfirmLeave(false);
    const e = leaveEventRef.current;
    if (e) {
      window.location.href = e.target.href || "#";
    }
  };

  const handleCancelLeave = () => {
    setShowConfirmLeave(false);
    leaveEventRef.current = null;
  };

  const updateProgressSafely = (newProgressMap) => {
    setProgress((prev) => {
      const next = { ...prev };
      for (const k of Object.keys(newProgressMap)) {
        const raw = newProgressMap[k];
        let reported = 0;
        if (raw === "done") reported = 100;
        else {
          const parsed = parseInt(String(raw).replace("%", "").trim()) || 0;
          reported = parsed;
        }
        const prevVal = parseInt(next[k] || 0);
        next[k] = Math.max(prevVal, reported);
      }
      return next;
    });
  };

  const startPolling = (id) => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      try {
        const r = await fetch(`http://localhost:8000/api/webappscanner/status/${id}/`);
        if (!r.ok) return;
        const d = await r.json();
        if (d.progress)
          updateProgressSafely(
            d.progress.reduce((acc, p) => {
              acc[p.stage] = p.status;
              return acc;
            }, {})
          );
        if (d.status === "finished") {
          setResults(d.results || []);
          setMessage(`✅ Scan finished: ${d.results ? d.results.length : 0} alerts`);
          setLoading(false);
          setScanRunning(false);
          clearInterval(pollRef.current);
          pollRef.current = null;
        } else if (d.status === "error") {
          setMessage(`❌ Scan error: ${d.details}`);
          setLoading(false);
          setScanRunning(false);
          clearInterval(pollRef.current);
          pollRef.current = null;
        }
      } catch (err) {
        // ignore transient
      }
    }, 1500);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!targetUrl) {
      setMessage("Please enter a URL to scan.");
      return;
    }
    setLoading(true);
    setMessage("⚠️ Don’t switch tabs or let the screen turn off!");
    setResults([]);
    setProgress({ open_url: 0, spider: 0, active_scan: 0 });

    try {
      const res = await fetch("http://localhost:8000/api/webappscanner/scan/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target: targetUrl }),
        credentials: "include",
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to start scan");
      setScanId(data.scan_id);
      localSetScanId(data.scan_id);
      setScanRunning(true);
      startPolling(data.scan_id);
    } catch (err) {
      setMessage(err.message || "Could not start scan");
      setLoading(false);
      setScanRunning(false);
    }
  };

  const handleDownload = () => {
    if (scanId) {
      window.open(`http://localhost:8000/api/webappscanner/download-pdf/${scanId}/`, "_blank");
    }
  };

  // 🛑 NEW: stop scan manually
  const handleStop = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
    setLoading(false);
    setScanRunning(false);
    setMessage("⏹️ Scan stopped by user.");
  };

  return (
    <div className="webapp-container">
      <h1>WebApp Scanner</h1>
      <form onSubmit={handleSubmit}>
        <div className="form-row">
          <label>Target URL:</label>
          <input
            type="text"
            value={targetUrl}
            onChange={(e) => setTargetUrl(e.target.value)}
            placeholder="https://example.com"
          />
        </div>

        <div className="form-row" style={{ display: "flex", gap: 8 }}>
          <button type="submit" disabled={loading}>
            {loading ? "Scanning..." : "Start Scan"}
          </button>
          <button type="button" onClick={handleDownload} disabled={!results.length}>
            Download PDF
          </button>
          {loading && (
            <button type="button" onClick={handleStop} style={{ backgroundColor: "red", color: "#fff" }}>
              Stop Scan
            </button>
          )}
        </div>
      </form>

      {message && (
        <p className={message.toLowerCase().includes("error") ? "error" : "success"}>{message}</p>
      )}

      {/* Progress */}
      <div className="progress-section" style={{ marginTop: 18 }}>
        {Object.keys(progress).length > 0 && <h3 class="ananana">Scan Progress</h3>}
        {Object.keys(progress).map((stageKey) => {
          const pct = parseInt(progress[stageKey] || 0);
          const pctDisplay = pct >= 100 ? 100 : Math.min(100, pct);
          return (
            <div key={stageKey} className="progress-bar-container">
              <label>{prettyStageLabel[stageKey] || stageKey}:</label>
              <div className="progress-bar">
                <div className="progress-bar-fill" style={{ width: `${pctDisplay}%` }} />
              </div>
              <span style={{ minWidth: 48, textAlign: "right" }}>
                {pctDisplay === 100 ? "done" : `${pctDisplay}%`}
              </span>
            </div>
          );
        })}
      </div>

      {/* Results */}
      {results.length > 0 && (
        <div className="results-table centered-table">
          <h2>Alerts</h2>
          <table className="zap-table">
            <thead>
              <tr>
                <th>Alert</th>
                <th>Risk</th>
                <th>URL</th>
                <th>Param</th>
                <th>CWE</th>
                <th>Suggestion</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r, i) => (
                <tr key={i}>
                  <td>{r.alert}</td>
                  <td>{r.risk}</td>
                  <td style={{ maxWidth: 300, wordBreak: "break-all" }}>{r.url}</td>
                  <td>{r.param}</td>
                  <td>{r.cweid}</td>
                  <td style={{ maxWidth: 300 }}>{r.suggestion}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Confirm modal */}
      {showConfirmLeave && (
        <div className="modal-backdrop">
          <div className="modal">
            <p>A scan is running. Leaving will stop it. Continue?</p>
            <button onClick={handleConfirmLeave}>Yes</button>
            <button onClick={handleCancelLeave}>No</button>
          </div>
        </div>
      )}

      {/* Game modal */}
      <GameModal open={showGame} onClose={() => setShowGame(false)} />
    </div>
  );
};

export default WebAppScanner;
