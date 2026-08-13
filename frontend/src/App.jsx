import { Navigate, Route, Routes } from 'react-router-dom';
import { Box, CssBaseline } from '@mui/material';
import NavBar from './components/NavBar';
import ProtectedRoute from './components/ProtectedRoute';
import Dashboard from './pages/Dashboard';
import AnalyticsView from './pages/AnalyticsView';
import AccountView from './pages/AccountView';
import LimitsView from './pages/LimitsView';
import LoginView from './pages/LoginView';

// The public sign-up page, no ProtectedRoute wrapper since a new customer
// isn't logged in yet when they land here.
import SignUpView from './pages/SignUpView';

// The new manager-only page, gets rendered instead of the regular
// Dashboard when the logged-in user's role calls for it.
import ManagerDashboard from './pages/ManagerDashboard';

// Gives access to the current auth state (the raw JWT string) from
// wherever it's called, no need to pass it down through props.
import { useAuth } from './context/AuthContext';

// Turns that raw JWT string into a usable object (sub, email, roles),
// since AuthContext only stores it as-is, it doesn't decode it.
import { decodeToken } from './utils/decodeToken';


// Reads the role straight off the token rather than threading it through
// props, decodeToken returns null for a missing/invalid token so
// role-checks below fail closed instead of throwing.
function useUserRole() {
  const { user } = useAuth();
  const payload = decodeToken(user);
  // roles is stored as a list on the token, a customer or teller only
  // ever has one entry in it.
  return payload?.roles?.[0] ?? null;
}

// Picks which dashboard to render based on the logged-in user's role.
function DashboardRouter() {
  const role = useUserRole();
  return role === 'BRANCH_MANAGER' || role === 'ADMIN'
    ? <ManagerDashboard />
    : <Dashboard />;
}


function App() {
  return (
    <>
      <CssBaseline />
      <NavBar />
      <Box component="main">
        <Routes>
          {/* Land on the dashboard by default */}
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardRouter />
              </ProtectedRoute>
            }
          />
          <Route
            path="/analytics"
            element={
              <ProtectedRoute>
                <AnalyticsView />
              </ProtectedRoute>
            }
          />
          <Route
            path="/accounts"
            element={
              <ProtectedRoute>
                <AccountView />
              </ProtectedRoute>
            }
          />
          <Route
            path="/limits"
            element={
              <ProtectedRoute>
                <LimitsView />
              </ProtectedRoute>
            }
          />
          <Route path="/login" element={<LoginView />} />
          <Route path="/signup" element={<SignUpView />} />
          {/* Unknown paths fall back to the login */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </Box>
    </>
  );
}

export default App;