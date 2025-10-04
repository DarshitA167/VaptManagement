// === PasswordVault.js ===
import React, { useEffect, useState } from 'react';
import { fetchPasswords, deletePassword } from './passwordService';
import { useAuth } from '../../context/AuthContext';
import { Navigate } from 'react-router-dom';

import AddPasswordModal from './AddPasswordModal';
import EditPasswordModal from './EditPasswordModal';
import PasswordCard from './PasswordCard';
import '../../styles/passwordvault.css';

const PasswordVault = () => {
  const { token } = useAuth();
  const [passwords, setPasswords] = useState([]);
  const [editingEntry, setEditingEntry] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);

  useEffect(() => {
    if (token) loadPasswords();
  }, [token]);

  const loadPasswords = async () => {
    const data = await fetchPasswords(token);
    setPasswords(data);
  };

  const handleDelete = async (id) => {
    await deletePassword(id, token);
    loadPasswords();
  };

  if (token === undefined) return null;
  if (!token) return <Navigate to="/" replace />;

  return (
    <div className="vault-container">
      <h1 >🔐 Your Password Vault</h1>
      <button onClick={() => setShowAddModal(true)} className="add-button">+ Add New</button>

      <div className="password-grid">
        {passwords.map((p) => (
          <PasswordCard
            key={p.id}
            entry={p}
            onEdit={() => setEditingEntry(p)}
            onDelete={() => handleDelete(p.id)}
          />
        ))}
      </div>

      {showAddModal && (
        <AddPasswordModal
          onClose={() => {
            setShowAddModal(false);
            loadPasswords();
          }}
        />
      )}

      {editingEntry && (
        <EditPasswordModal
          entry={editingEntry}
          onClose={() => {
            setEditingEntry(null);
            loadPasswords();
          }}
        />
      )}
    </div>
  );
};

export default PasswordVault;