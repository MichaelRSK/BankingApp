import axios from 'axios';

// The deployed backend, behind nginx on the EC2 instance.
//
// https, not http, and no port. nginx listens on 443 and proxies to uvicorn
// on 8000 internally. The plain http://54.80.133.45:8000 form still answers,
// but a page served over https cannot call it: browsers block that as mixed
// content before the request is even sent, whatever CORS allows.
//
// The hostname is 54.80.133.45.nip.io rather than a bare IP because Let's
// Encrypt will not issue a certificate for an IP address. nip.io resolves
// <ip>.nip.io straight back to that address, so it is a real name with no
// DNS to manage, and it is tied to the instance's Elastic IP.
const api = axios.create({
  baseURL: 'https://54.80.133.45.nip.io',
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