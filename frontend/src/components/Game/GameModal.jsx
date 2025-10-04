import React, { useEffect, useRef, useState } from "react";
import FlappyGame from "./FlappyBird";   // make sure file name is FlappyGame.jsx
import "./flappy.css";

/**
 * GameModal:
 * - waits for `scanStarted` event
 * - after 5s shows confirm modal (Yes/No)
 * - Yes → show FlappyGame
 * - No → close
 */
const GameModal = () => {
  const [confirmVisible, setConfirmVisible] = useState(false);
  const [showGame, setShowGame] = useState(false);
  const timerRef = useRef(null);

  useEffect(() => {
    const onScan = () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      // after 5s show confirm
      timerRef.current = setTimeout(() => setConfirmVisible(true), 5000);
    };
    window.addEventListener("scanStarted", onScan);

    return () => {
      window.removeEventListener("scanStarted", onScan);
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  const closeAll = () => {
    setConfirmVisible(false);
    setShowGame(false);
  };

  if (!confirmVisible && !showGame) return null;

  return (
    <div className="game-modal-overlay" role="dialog" aria-modal="true">
      <div className="game-modal-box">
        {confirmVisible && !showGame && (
          <>
            <h3>⚡ Scan is running...</h3>
            <p>Wanna play a game while waiting?</p>
            <div className="game-modal-actions">
              <button
                onClick={() => {
                  setShowGame(true);
                  setConfirmVisible(false);
                }}
              >
                Yes 🎮
              </button>
              <button onClick={() => setConfirmVisible(false)}>No 🙅</button>
            </div>
          </>
        )}

        {showGame && (
          <>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <h3 style={{ margin: 0 }}>Flappy Game</h3>
              <button onClick={closeAll} className="game-close-btn">
                ✕
              </button>
            </div>
            <div style={{ marginTop: 12 }}>
              <FlappyGame width={520} height={380} onClose={closeAll} />
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default GameModal;
