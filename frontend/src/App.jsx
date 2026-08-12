import { Navigate, Route, Routes } from 'react-router-dom';
import { Box, CssBaseline } from '@mui/material';
import NavBar from './components/NavBar';
import Dashboard from './pages/Dashboard';
import AnalyticsView from './pages/AnalyticsView';
import AccountView from './pages/AccountView';
import LoginView from './pages/LoginView';

function App() {
  return (
    <>
      <CssBaseline />
      <NavBar />
      <Box component="main">
        <Routes>
          {/* Land on the dashboard by default */}
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/analytics" element={<AnalyticsView />} />
          <Route path="/accounts" element={<AccountView />} />
          <Route path="/login" element={<LoginView />} />
          {/* Unknown paths fall back to the login */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </Box>
    </>
  );
}

export default App;