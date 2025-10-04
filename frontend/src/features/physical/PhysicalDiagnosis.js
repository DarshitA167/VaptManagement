import React, { useState } from "react";
import "../../styles/physical.css";
// @ts-ignore
import { diagnoseDisease } from "../../services/physicalHealth";

const PhysicalDiagnosis = () => {
  const [symptoms, setSymptoms] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!symptoms.trim()) return;
    setLoading(true);
    const data = await diagnoseDisease(symptoms);
    setResult(data);
    setLoading(false);
  };

  return (
    <div className="physical-container">
      <h2 className="physical-title">🩺 Physical Security — Disease Diagnosis</h2>
      
      <input
        className="symptom-input"
        type="text"
        value={symptoms}
        onChange={(e) => setSymptoms(e.target.value)}
        placeholder="Enter symptoms (e.g., cough, fever)"
      />

      <button
        className="diagnose-button"
        onClick={handleSubmit}
        disabled={loading}
      >
        {loading ? "Scanning..." : "Check Disease"}
      </button>

      {result && (
        <div className="result-box">
          <p><strong>Disease:</strong> {result.disease}</p>
          <p><strong>Advice:</strong> {result.advice}</p>
        </div>
      )}
    </div>
  );
};

export default PhysicalDiagnosis;
