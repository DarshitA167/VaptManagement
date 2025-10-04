import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useLocation } from 'react-router-dom';
import '../../styles/mentalchat.css';

const MentalChatBot = () => {
  const { state } = useLocation();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    const initial = [];
    if (state?.preamble) {
      initial.push({
        role: 'user',
        content: `Here is what you said about me:\n${state.preamble}\nCan we discuss next steps?`,
      });
    } else {
      initial.push({ role: 'user', content: "Hello, I’d like to talk about my mental state." });
    }
    setMessages(initial);
    sendBot(initial);
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendBot = async (msgList) => {
    setLoading(true);
    try {
      const res = await axios.post('/api/mental/chat/', { messages: msgList });
      const reply = res?.data?.response || "⚠️ went mute. Try again.";
      setMessages([...msgList, { role: 'assistant', content: reply }]);
    } catch (err) {
      console.error("error:", err);
      setMessages([...msgList, { role: 'assistant', content: "AI is tripping, let's try again." }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = () => {
    if (!input.trim()) return;
    const userMsg = { role: 'user', content: input };
    const updated = [...messages, userMsg];
    setMessages(updated);
    setInput('');
    sendBot(updated);
  };

  return (
    <div className="mentalchat-container">
      <h2 className="mentalchat-title">🧠 Mental Wellness Chat</h2>

      <div className="chat-box">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`message ${m.role === 'user' ? 'user-message' : 'bot-message'}`}
          >
            <p>{m.content}</p>
          </div>
        ))}
        <div ref={chatEndRef} />
      </div>

      <div className="input-section">
        <input
          className="message-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Your message…"
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
        />
        <button className="send-button" onClick={handleSend} disabled={loading}>
          {loading ? '...' : 'Send'}
        </button>
      </div>
    </div>
  );
};

export default MentalChatBot;
