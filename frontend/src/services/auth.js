import axios from 'axios';

const BASE_URL = 'http://127.0.0.1:8000/api/accounts';  // ✅ all auth routes live under /accounts/

// Register new user
export const registerUser = async (data) => {
  return axios.post(`${BASE_URL}/register/`, data);
};

// Login user (JWT tokens)
export const loginUser = async (data) => {
  return axios.post(`${BASE_URL}/login/`, data);
};

// Get current logged-in user (requires token)
export const getCurrentUser = async (token) => {
  return axios.get(`${BASE_URL}/user/`, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  });
};
