import axios from 'axios';

const api = axios.create({
  baseURL: "https://oqc6d32f7d.execute-api.us-east-1.amazonaws.com",
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

export default api;