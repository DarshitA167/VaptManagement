import React, { useState } from 'react';

const PasswordCard = ({ entry, onEdit, onDelete }) => {
  const [showPassword, setShowPassword] = useState(false);

  return (
    <div className="password-card">
      <h2>{entry.service_name}</h2>
      <p><strong>Username:</strong> {entry.username}</p>
      <p>
        <strong>Password:</strong> {showPassword ? entry.password : '••••••••'}
        <span onClick={() => setShowPassword(!showPassword)} className="toggle-btn">
          {showPassword ? 'Hide' : 'Show'}
        </span>
      </p>
      {entry.notes && <p className="notes">📜 {entry.notes}</p>}
      <div className="password-actions">
        <button onClick={onEdit} className="edit-btn">Edit</button>
        <button onClick={onDelete} className="delete-btn">Delete</button>
      </div>
    </div>
  );
};

export default PasswordCard;
