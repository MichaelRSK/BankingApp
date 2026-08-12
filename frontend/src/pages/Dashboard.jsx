import {
  Box,
  Card,
  CardContent,
  Container,
  Divider,
  Grid,
  Typography,
} from '@mui/material';

/*
 * ============================================================
 * API calls and real data go here.
 * ============================================================
 * Replace the hard-coded `summaryCards` values below with data
 * fetched from the backend (see app/ for the FastAPI routes).
 * Nothing in this file talks to the network yet, by design.
 */
const summaryCards = [
  {
    title: 'Total Balance',
    value: '$--,---.--',
    caption: 'Across all linked accounts',
  },
  {
    title: 'Recent Activity',
    value: '-- transactions',
    caption: 'In the last 30 days',
  },
  {
    title: 'Accounts',
    value: '--',
    caption: 'Open checking and savings accounts',
  },
];

function Dashboard() {
  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Welcome back
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Here&apos;s a snapshot of your accounts.
      </Typography>

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

      {/* Placeholder for a wider panel, e.g. a transactions table or chart */}
      <Box sx={{ mt: 4 }}>
        <Card>
          <CardContent>
            <Typography variant="h6" component="h2" gutterBottom>
              Recent Transactions
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {/* API calls and real data go here */}
              No data yet — this panel will list recent transactions once the
              backend is wired up.
            </Typography>
          </CardContent>
        </Card>
      </Box>
    </Container>
  );
}

export default Dashboard;