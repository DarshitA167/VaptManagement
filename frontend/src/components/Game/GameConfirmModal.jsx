import React from "react";

const GameConfirmModal = ({ open, onYes, onNo }) => {
  if (!open) return null;

  return (
    <div className="modal-backdrop">
      <div className="modal">
        <p>⚡ Scan is running... Wanna play a game while waiting?</p>
        <div style={{ marginTop: "10px", display: "flex", gap: "10px" }}>
          <button onClick={onYes}>Yes 🎮</button>
          <button onClick={onNo}>No 🙅</button>
        </div>
      </div>
    </div>
  );
};

export default GameConfirmModal;
