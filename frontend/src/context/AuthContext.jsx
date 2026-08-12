import { createContext, useState, useEffect, useContext } from 'react';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check if a user session exists on app mount
  useEffect(() => {
    const storedUser = localStorage.getItem('access_token');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
    setLoading(false);
  }, []);

  // Login handler
  const login = (userData) => {
    setUser(userData);
    localStorage.setItem('access_token', JSON.stringify(userData));
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