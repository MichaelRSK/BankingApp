import { useState } from 'react';

import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Container,
  Grid,
  Stack,
  TextField,
  Typography,
} from '@mui/material';

import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import SearchIcon from '@mui/icons-material/Search';

import api from '../api/api';


function AccountView() {
  const [branchCode, setBranchCode] = useState('');
  const [minBalance, setMinBalance] = useState(0);

  const [accounts, setAccounts] = useState([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');


  const loadAccounts = async () => {
    if (!branchCode) {
      setError('Please enter a branch code.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await api.get('/api/v1/accounts', {
        params: {
          branch_code: branchCode,
          min_balance: minBalance,
        },
      });

      setAccounts(response.data);
    } catch (err) {
      console.error(err);

      if (err.response?.status === 401) {
        setError('You must be logged in to view accounts.');
      } else {
        setError(
          err.response?.data?.detail ||
          'Unable to load accounts.'
        );
      }
    } finally {
      setLoading(false);
    }
  };


  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography
        variant="h4"
        component="h1"
        sx={{ fontWeight: 600, mb: 1 }}
      >
        Account View
      </Typography>

      <Typography
        variant="body1"
        color="text.secondary"
        sx={{ mb: 4 }}
      >
        Search for accounts by branch and minimum balance.
      </Typography>


      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography
            variant="h6"
            sx={{ mb: 2 }}
          >
            Account Search
          </Typography>

          <Stack
            direction={{ xs: 'column', md: 'row' }}
            spacing={2}
          >
            <TextField
              label="Branch Code"
              type="number"
              value={branchCode}
              onChange={(event) =>
                setBranchCode(event.target.value)
              }
              fullWidth
            />

            <TextField
              label="Minimum Balance"
              type="number"
              value={minBalance}
              onChange={(event) =>
                setMinBalance(event.target.value)
              }
              fullWidth
            />

            <Button
              variant="contained"
              startIcon={<SearchIcon />}
              onClick={loadAccounts}
              sx={{
                minWidth: 130,
              }}
            >
              Search
            </Button>
          </Stack>
        </CardContent>
      </Card>


      {error && (
        <Alert
          severity="error"
          sx={{ mb: 3 }}
        >
          {error}
        </Alert>
      )}


      {loading ? (
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            py: 6,
          }}
        >
          <CircularProgress />
        </Box>
      ) : accounts.length === 0 ? (
        <Card>
          <CardContent
            sx={{
              textAlign: 'center',
              py: 6,
            }}
          >
            <AccountBalanceWalletIcon
              sx={{
                fontSize: 50,
                color: 'text.secondary',
                mb: 1,
              }}
            />

            <Typography
              variant="h6"
              color="text.secondary"
            >
              No accounts loaded
            </Typography>

            <Typography color="text.secondary">
              Enter a branch code and select Search.
            </Typography>
          </CardContent>
        </Card>
      ) : (
        <Grid
          container
          spacing={3}
        >
          {accounts.map((account) => (
            <Grid
              key={account.account_number}
              size={{
                xs: 12,
                sm: 6,
                md: 4,
              }}
            >
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Stack
                    direction="row"
                    spacing={1}
                    alignItems="center"
                    sx={{ mb: 2 }}
                  >
                    <AccountBalanceWalletIcon color="primary" />

                    <Typography
                      variant="h6"
                      sx={{ fontWeight: 600 }}
                    >
                      {account.account_type}
                    </Typography>
                  </Stack>


                  <Typography
                    variant="body2"
                    color="text.secondary"
                  >
                    Account Number
                  </Typography>

                  <Typography
                    variant="body1"
                    sx={{ mb: 2 }}
                  >
                    {account.account_number}
                  </Typography>


                  <Typography
                    variant="body2"
                    color="text.secondary"
                  >
                    Balance
                  </Typography>

                  <Typography
                    variant="h4"
                    color="primary"
                    sx={{
                      fontWeight: 600,
                      mb: 2,
                    }}
                  >
                    ${Number(account.balance).toFixed(2)}
                  </Typography>


                  <Typography variant="body2">
                    <strong>Owner:</strong> {account.owner}
                  </Typography>

                  <Typography variant="body2">
                    <strong>Owner ID:</strong> {account.owner_id}
                  </Typography>

                  <Typography variant="body2">
                    <strong>Branch:</strong> {account.branch_code}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Container>
  );
}

export default AccountView;