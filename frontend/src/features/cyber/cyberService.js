import axios from 'axios';

export const checkEmailSecurity = async (email) => {
  try {
    const res = await axios.post('/api/cyber/check/', { email });
    return res.data;
  } catch (err) {
    console.error("Cyber check failed", err);
    return null;
  }
};
