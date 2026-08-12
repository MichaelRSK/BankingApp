import { Navigate, Route, Routes } from 'react-router-dom';
import { Box, CssBaseline } from '@mui/material';
import NavBar from './components/NavBar';
import Dashboard from './pages/Dashboard';
import AnalyticsView from './pages/AnalyticsView';
import AccountView from './pages/AccountView';

function App() {
  return (
    <>
      <CssBaseline />
      <NavBar />
      <Box component="main">
        <Routes>
          {/* Land on the dashboard by default */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/analytics" element={<AnalyticsView />} />
          <Route path="/accounts" element={<AccountView />} />
          {/* Unknown paths fall back to the dashboard */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Box>
    </>
  );
}

export default App;