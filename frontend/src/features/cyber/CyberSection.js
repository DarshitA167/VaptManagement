// === CyberSection.js ===
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '../../styles/cyberSecurity.css';

const CyberSection = () => {
  const [email, setEmail] = useState('');
  const [result, setResult] = useState(null);
  const [cooldown, setCooldown] = useState(0);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let timer;
    if (cooldown > 0) {
      timer = setInterval(() => {
        setCooldown(prev => {
          if (prev <= 1) {
            clearInterval(timer);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [cooldown]);

  const handleCheck = async () => {
    if (!email) return alert("Enter your email, soldier!");
    if (cooldown > 0) return alert(`⏳ Cooldown active! Wait ${cooldown}s.`);

    setLoading(true);
    setResult(null);

    try {
      const res = await axios.post('http://localhost:8000/api/cyber/check/', { email });
      if (res.data.cooldown) {
        setCooldown(res.data.cooldown);
      } else {
        setResult(res.data);
      }
    } catch (err) {
      if (err.response?.status === 429 && err.response.data.cooldown) {
        setCooldown(err.response.data.cooldown);
      } else {
        console.error("Security check error:", err);
        alert("Something went wrong on the cyber battlefield.");
      }
    }
    setLoading(false);
  };

  const downloadPDF = async (filename) => {
    try {
      const res = await axios.get(`http://localhost:8000/api/cyber/download-report/${filename}`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error("Download failed:", err);
      alert("Couldn't download the PDF report.");
    }
  };

  return (
    <div className="cyber-container">
      <h2 className="cyber-title">🛡️ Data Leak & Phishing Scanner</h2>

      <input
        type="email"
        className="cyber-email-input"
        placeholder="Enter your email"
        value={email}
        onChange={e => setEmail(e.target.value)}
      />
      <button
        className="cyber-check-btn"
        onClick={handleCheck}
        disabled={loading || cooldown > 0}
      >
        {loading ? "Scanning..." : "Check Email Security"}
      </button>

      <div className="cyber-demo-button">
        <button
          onClick={() => setEmail('test@example.com')}
          className="cyber-btn-demo"
        >
          Use Sample Email
        </button>
      </div>

      {cooldown > 0 && (
        <div className="cyber-alert">
          ⏳ Too many requests! Wait {cooldown}s.
        </div>
      )}

      {result && (
        <div className="cyber-result-card">
          {result.breaches && result.breaches.length > 0 ? (
            <>
              <h3 className="cyber-breach-title">❌ Breaches Found: {result.breaches.length}</h3>
              <ul className="cyber-breach-list">
                {result.breaches.map((breach, index) => (
                  <li key={index}>
                    <strong>{breach.name}</strong>
                    {breach.date && <span> — <em>{breach.date}</em></span>}
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <h3 className="cyber-safe-text">✅ No breaches found. You're safe!</h3>
          )}

          {result.phishing && (
            <div className="cyber-phishing-result">
              <h3>🎓 Phishing Check</h3>
              {result.phishing?.error ? (
                <p><strong>Error:</strong> {result.phishing.error}</p>
              ) : (
                <>
                  <p><strong>IP:</strong> {result.phishing.ip || "Unknown"}</p>
                  <p><strong>Abuse Score:</strong> {result.phishing.abuseScore ?? "N/A"}</p>
                  <p><strong>Phishing Verdict:</strong> {result.phishing.isPhishing ? '⚠️ Suspicious' : '✅ Clean'}</p>
                </>
              )}
            </div>
          )}

          {result.pdf_filename && (
            <button className="cyber-download-btn" onClick={() => downloadPDF(result.pdf_filename)}>
              📄 Download PDF Report
            </button>
          )}
        </div>
      )}

      {result && (
        <div className="cyber-debug-json">
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

export default CyberSection;
