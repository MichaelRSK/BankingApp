// useEffect fetches the dashboard data once when the page loads, useState
// holds it once it comes back.
import { useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  CircularProgress,
  Container,
  Divider,
  Grid,
  Typography,
} from '@mui/material';
// Same shared Axios instance every other page uses, already attaches the
// JWT to every request via its interceptor.
import api from '../api/api';
// Gives access to the current auth state, the raw JWT string.
import { useAuth } from '../context/AuthContext';
// Turns that raw JWT string into a usable object (sub, email, roles).
import { decodeToken } from '../utils/decodeToken';

function Dashboard() {
  const { user } = useAuth();

  // Holds the accounts and transactions once they're fetched, both start
  // empty so the page has something safe to render before data arrives.
  const [accounts, setAccounts] = useState([]);
  const [transactions, setTransactions] = useState([]);
  // True while the initial fetch is in flight, shows a spinner instead of
  // stale placeholder numbers.
  const [loading, setLoading] = useState(true);
  // Holds an error message if any of the fetches fail.
  const [error, setError] = useState('');

  useEffect(() => {
    async function loadDashboardData() {
      try {
        // The token carries sub (this customer's id). GET /accounts
        // requires a branch_code and there is no "just give me my own
        // accounts" endpoint yet, so the customer's own record is looked
        // up first to find which branch they belong to.
        const payload = decodeToken(user);
        const customerId = payload?.sub;

        const customerResponse = await api.get(`/api/v1/customers/${customerId}`);
        const branchCode = customerResponse.data.branch_code;

        // The backend already filters this down to only this customer's
        // own accounts when the caller has the CUSTOMER role, min_balance:
        // 0 means "show everything, don't filter by amount."
        const accountsResponse = await api.get('/api/v1/accounts', {
          params: { branch_code: branchCode, min_balance: 0 },
        });
        setAccounts(accountsResponse.data);

        // GET /transactions only filters by one type at a time (TRANSFER,
        // DEPOSIT, or WITHDRAWAL), there's no "all types" option. A
        // meaningful "recent activity" view needs all three, so each type
        // is fetched in parallel and the results are merged afterward.
        const types = ['TRANSFER', 'DEPOSIT', 'WITHDRAWAL'];
        const responses = await Promise.all(
          types.map((type) =>
            api.get('/api/v1/transactions', {
              params: { start_date: '2020-01-01', type },
            })
          )
        );

        // Flatten the three separate response arrays into one list.
        const merged = responses.flatMap((response) => response.data);
        // Newest first, so the most recent activity shows up top.
        merged.sort(
          (a, b) => new Date(b.timestamp) - new Date(a.timestamp)
        );
        // Only the 5 most recent are actually shown on the dashboard.
        setTransactions(merged.slice(0, 5));
      } catch (err) {
        console.error(err);
        setError('Unable to load dashboard data.');
      } finally {
        // Runs whether the fetch succeeded or failed, so the spinner
        // always goes away.
        setLoading(false);
      }
    }

    loadDashboardData();
    // Re-runs if the logged-in user changes (e.g. a different login),
    // so the dashboard doesn't keep showing the previous user's data.
  }, [user]);

  // Computed from the real fetched accounts, replaces the old hardcoded
  // "$--,---.--" placeholder.
  const totalBalance = accounts.reduce(
    (total, account) => total + Number(account.balance),
    0
  );

  // Same three summary cards as before, but now built from real numbers
  // instead of placeholder strings.
  const summaryCards = [
    {
      title: 'Total Balance',
      value: `$${totalBalance.toFixed(2)}`,
      caption: 'Across all linked accounts',
    },
    {
      title: 'Recent Activity',
      value: `${transactions.length} transactions`,
      caption: 'Most recent on record',
    },
    {
      title: 'Accounts',
      value: `${accounts.length}`,
      caption: 'Open checking and savings accounts',
    },
  ];

  // Shows a spinner instead of the page while the fetches are still in
  // flight, avoids a flash of zeroed-out cards before real data arrives.
  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4, textAlign: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Welcome back
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Here&apos;s a snapshot of your accounts.
      </Typography>

      {error && (
        <Typography color="error" sx={{ mb: 3 }}>
          {error}
        </Typography>
      )}

      {/* Responsive summary cards: 1 per row on mobile, 2 on tablet, 3 on desktop */}
      <Grid container spacing={3}>
        {summaryCards.map((card) => (
          <Grid key={card.title} size={{ xs: 12, sm: 6, md: 4 }}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Typography
                  variant="overline"
                  color="text.secondary"
                  gutterBottom
                  component="div"
                >
                  {card.title}
                </Typography>
                <Typography variant="h5" component="p" sx={{ mb: 1 }}>
                  {card.value}
                </Typography>
                <Divider sx={{ mb: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  {card.caption}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Real transaction rows now, replacing the old "no data yet" text */}
      <Box sx={{ mt: 4 }}>
        <Card>
          <CardContent>
            <Typography variant="h6" component="h2" gutterBottom>
              Recent Transactions
            </Typography>

            {transactions.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                No transactions yet.
              </Typography>
            ) : (
              transactions.map((t) => (
                <Box
                  key={t.id}
                  sx={{ display: 'flex', justifyContent: 'space-between', py: 1 }}
                >
                  <Typography variant="body2">{t.type}</Typography>
                  <Typography variant="body2">${Number(t.amount).toFixed(2)}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {new Date(t.timestamp).toLocaleDateString()}
                  </Typography>
                </Box>
              ))
            )}
          </CardContent>
        </Card>
      </Box>
    </Container>
  );
}

export default Dashboard;