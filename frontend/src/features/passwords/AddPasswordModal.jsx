import React, { useState } from 'react';
import { addPassword } from './passwordService';
import { useAuth } from '../../context/AuthContext';

const AddPasswordModal = ({ onClose }) => {
  const { token } = useAuth();

  const [form, setForm] = useState({
    service_name: '',
    username: '',
    password: '',
    notes: '',
  });

  const handleChange = e => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async e => {
    e.preventDefault();
    await addPassword(form, token);
    onClose();
  };

  return (
    <div className="modal-container">
      <div className="modal-content">
        <h2 className="text-2xl font-bold mb-4">➕ Add New Password</h2>
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <input type="text" name="service_name" placeholder="Service Name" value={form.service_name} onChange={handleChange} required />
          <input type="text" name="username" placeholder="Username" value={form.username} onChange={handleChange} required />
          <input type="password" name="password" placeholder="Password" value={form.password} onChange={handleChange} required />
          <textarea name="notes" placeholder="Notes (optional)" value={form.notes} onChange={handleChange} />
          <div className="modal-actions">
            <button type="button" onClick={onClose} className="cancel-btn">Cancel</button>
            <button type="submit" className="save-btn">Save</button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddPasswordModal;