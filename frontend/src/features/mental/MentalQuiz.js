import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import '../../styles/mentalquiz.css';

const MentalQuiz = () => {
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState([]);
  const [analysis, setAnalysis] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    axios.get('/api/mental/questions/')
      .then(res => {
        setQuestions(res.data.questions);
        setAnswers(Array(res.data.questions.length).fill(''));
      })
      .catch(console.error);
  }, []);

  const handleChange = (i, value) => {
    const arr = [...answers];
    arr[i] = value;
    setAnswers(arr);
  };

  const handleSubmit = () => {
    const formatted = questions.map((q, i) => ({
      question: q.question,
      answer: answers[i] || ""
    }));

    axios.post('/api/mental/analyze/', { answers: formatted })
      .then(res => setAnalysis(res.data.analysis))
      .catch(err => console.error(err));
  };

  const goToChat = () => {
    navigate('/mental/chat', { state: { preamble: analysis } });
  };

  return (
    <div className="quiz-container">
      <h2 className="quiz-title">🧠 Mental Health Check-In</h2>

      {questions.map((q, i) => (
        <div key={i} className="question-block">
          <p className="question-text">{q.question}</p>
          {q.options ? (
            <select
              value={answers[i] || ''}
              onChange={e => handleChange(i, e.target.value)}
              className="quiz-select"
            >
              <option value="">Select an option</option>
              {q.options.map((opt, idx) => (
                <option key={idx} value={opt}>{opt}</option>
              ))}
            </select>
          ) : (
            <input
              type="text"
              value={answers[i] || ''}
              onChange={e => handleChange(i, e.target.value)}
              className="quiz-input"
              placeholder="Type your answer..."
            />
          )}
        </div>
      ))}

      <button onClick={handleSubmit} className="analyze-button">
        Analyze Me
      </button>

      {analysis && (
        <div className="analysis-block">
          <h3 className="analysis-title">🧾 Analysis</h3>
          <p className="analysis-text">{analysis}</p>
          <button onClick={goToChat} className="continue-button">
            Continue Chat
          </button>
        </div>
      )}
    </div>
  );
};

export default MentalQuiz;
