// useState manages this component's local UI state (search input, fetched
// metrics, error message).
import { useState } from 'react';
import { Container, TextField, Button, Alert, Grid, Card, CardContent, Typography } from '@mui/material';

// DataGrid is the table component that renders the metrics once loaded.
import { DataGrid } from '@mui/x-data-grid';

// Same shared Axios instance every other page uses, already attaches the
// JWT to every request via its interceptor.
import api from '../api/api';


function ManagerDashboard() {
  // The branch code typed into the search box.
  const [branchCode, setBranchCode] = useState('');
  // Holds the metrics object once the API call succeeds, null means
  // nothing has been loaded yet.
  const [metrics, setMetrics] = useState(null);
  // Holds an error message to display, empty string means no error.
  const [error, setError] = useState('');

  // Fetches the metrics for whatever branch code is currently typed in.
  const loadMetrics = async () => {
    setError('');

    try {
      // This is the endpoint built in Step 3 of the backend, restricted to
      // BRANCH_MANAGER and ADMIN, everyone else gets a 403 here.
      const response = await api.get(`/api/v1/branches/${branchCode}/metrics`);
      setMetrics(response.data);
    } catch (err) {
      if (err.response?.status === 403) {
        setError('You do not have permission to view branch metrics.');
      } else {
        setError(err.response?.data?.detail || 'Unable to load branch metrics.');
      }
    }
  };

  // The data grid needs an array of rows, even for a single branch, each
  // row needs a unique id, DataGrid requires that field by default.
  // metrics is a flat object from the backend, this reshapes it into one
  // row per field so DataGrid has something to render.
  const rows = metrics
    ? [
        { id: 1, metric: 'Location', value: metrics.location },
        { id: 2, metric: 'Customers', value: metrics.customer_count },
        { id: 3, metric: 'Accounts', value: metrics.account_count },
        { id: 4, metric: 'Total Balance', value: `$${metrics.total_balance}` },
        { id: 5, metric: 'Staff Count', value: metrics.staff_count },
        { id: 6, metric: 'Staff-to-Manager Ratio', value: metrics.staff_to_manager_ratio },
      ]
    : [];

  // Column definitions for the grid, just two columns since each row is
  // already a single metric/value pair.
  const columns = [
    { field: 'metric', headerName: 'Metric', flex: 1 },
    { field: 'value', headerName: 'Value', flex: 1 },
  ];

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom>Branch Performance</Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {/* Search bar: type a branch code, click Load Metrics */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6 }}>
          <TextField
            label="Branch Code"
            fullWidth
            value={branchCode}
            onChange={(e) => setBranchCode(e.target.value)}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Button variant="contained" onClick={loadMetrics} fullWidth sx={{ height: '100%' }}>
            Load Metrics
          </Button>
        </Grid>
      </Grid>

      {/* Only renders once metrics has actually loaded, nothing shows on
          first render or after a failed request. */}
      {metrics && (
        <Card>
          <CardContent sx={{ height: 350 }}>
            <DataGrid rows={rows} columns={columns} hideFooter />
          </CardContent>
        </Card>
      )}
    </Container>
  );
}

export default ManagerDashboard;