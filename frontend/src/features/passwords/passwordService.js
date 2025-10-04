import axios from 'axios';

const BASE_URL = 'http://localhost:8000/api/security/passwords/';

export const fetchPasswords = async (token) => {
  const res = await axios.get(BASE_URL, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return res.data;
};

export const addPassword = async (data, token) => {
  const res = await axios.post(BASE_URL, data, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return res.data;
};

export const editPassword = async (id, data, token) => {
  const res = await axios.put(`${BASE_URL}${id}/`, data, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return res.data;
};

export const deletePassword = async (id, token) => {
  await axios.delete(`${BASE_URL}${id}/`, {
    headers: { Authorization: `Bearer ${token}` }
  });
};
