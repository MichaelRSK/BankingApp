import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';

// Gate for routes that require a signed-in user.
//
// AuthProvider holds back rendering until it has read localStorage, so
// isAuthenticated is already settled by the time this runs and there is no
// flash of a redirect on a hard refresh.
export default function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return children;
}