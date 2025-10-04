// src/features/mental/MentalSection.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const MentalSection = () => {
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState([]);
  const [analysis, setAnalysis] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    axios.get("/api/mental/questions")
      .then(res => {
        setQuestions(res.data.questions);
        setAnswers(Array(res.data.questions.length).fill(""));  // auto size based on question count
      })
      .catch(err => console.error("Failed to load questions", err));
  }, []);

  const handleChange = (index, value) => {
    const updated = [...answers];
    updated[index] = value;
    setAnswers(updated);
  };

  const handleSubmit = async () => {
  if (answers.includes("")) {
    alert("Please answer all questions.");
    return;
  }

  const payload = questions.map((q, i) => ({
    question: q.question,
    answer: answers[i]
  }));

    setLoading(true);
    try {
      const res = await axios.post('/api/mental/analyze/', { answers });
      setAnalysis(res.data.analysis);
    } catch (err) {
      console.error("Analysis failed", err);
    }
    setLoading(false);
  };

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">🧠 Mental Health Check</h2>
      {questions.length > 0 ? (
        questions.map((q, idx) => (
          <div key={idx} className="mb-6">
            <p className="font-medium mb-2">{q.question}</p>

            {q.options && q.options.length > 0 ? (
              q.options.map((opt, i) => (
                <label key={i} className="block mb-1">
                  <input
                    type="radio"
                    name={`question-${idx}`}
                    value={opt}
                    checked={answers[idx] === opt}
                    onChange={() => handleChange(idx, opt)}
                    className="mr-2"
                  />
                  {opt}
                </label>
              ))
            ) : (
              <input
                type="text"
                className="w-full p-2 border rounded"
                value={answers[idx]}
                onChange={(e) => handleChange(idx, e.target.value)}
              />
            )}
          </div>
        ))
      ) : (
        <p>Loading questions...</p>
      )}

      <button
        onClick={handleSubmit}
        className="bg-blue-600 text-white px-4 py-2 rounded mt-4"
        disabled={loading}
      >
        {loading ? "Analyzing..." : "Submit"}
      </button>

      {analysis && (
        <div className="mt-6 p-4 border border-green-600 bg-green-50 rounded">
          <h3 className="text-xl font-semibold mb-2">🧘‍♂️ Suggestions</h3>
          <p>{analysis}</p>
        </div>
      )}
    </div>
  );
};

export default MentalSection;
