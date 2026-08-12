import { createContext, useState, useEffect, useContext } from 'react';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check if a session exists on app mount.
  //
  // No JSON.parse here. The stored value is the raw JWT string, not an
  // object, and parsing it would throw on anything that is not valid JSON,
  // which would leave loading stuck at true and render an empty app.
  useEffect(() => {
    const storedToken = localStorage.getItem('access_token');
    if (storedToken) {
      setUser(storedToken);
    }
    setLoading(false);
  }, []);

  // Login handler. Takes the raw JWT string from the login response.
  //
  // Stored verbatim, without JSON.stringify. Stringifying wraps the token in
  // literal double quotes, and api.js reads this value straight into the
  // Authorization header, so the server would receive Bearer "eyJ..." and
  // reject every authenticated request.
  const login = (accessToken) => {
    setUser(accessToken);
    localStorage.setItem('access_token', accessToken);
  };

  // Logout handler
  const logout = () => {
    setUser(null);
    localStorage.removeItem('access_token');
  };

  // Pack states and functions together
  const value = {
    user,
    isAuthenticated: !!user,
    login,
    logout,
    loading
  };

  return (
    <AuthContext value={value}>
      {!loading && children}
    </AuthContext>
  );
};

// 3. Custom hook for easier context consumption
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};