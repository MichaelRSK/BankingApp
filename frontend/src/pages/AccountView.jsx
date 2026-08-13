import { useState } from "react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Container,
  Stack,
  TextField,
  Typography,
} from "@mui/material";

import api from "../api/api";

function AccountView() {
  const [branchCode, setBranchCode] =
    useState("");
  const [minBalance, setMinBalance] =
    useState(0);

  const [accounts, setAccounts] =
    useState([]);
  const [searched, setSearched] =
    useState(false);

  const [loading, setLoading] =
    useState(false);
  const [error, setError] =
    useState("");

  // Separate state for the transfer form below. Kept apart from the search
  // state above (branchCode, minBalance, accounts) since search and
  // transfer are two independent features sharing this one page.
  const [fromAccount, setFromAccount] =
    useState("");
  const [toAccount, setToAccount] =
    useState("");
  const [transferAmount, setTransferAmount] =
    useState("");
  // Shown in a green Alert when a transfer succeeds.
  const [transferMessage, setTransferMessage] =
    useState("");
  // Shown in a red Alert when a transfer fails, empty string means no error.
  const [transferError, setTransferError] =
    useState("");

  const loadAccounts = async () => {
    if (!branchCode) {
      setError(
        "Please enter a branch code."
      );
      return;
    }

    setLoading(true);
    setError("");
    setSearched(true);

    try {
      const response = await api.get(
        "/api/v1/accounts",
        {
          params: {
            branch_code: branchCode,
            min_balance: minBalance,
          },
        }
      );

      setAccounts(response.data);
    } catch (err) {
      console.error(err);

      if (err.response?.status === 401) {
        setError(
          "You must be logged in to view accounts."
        );
      } else if (
        err.response?.status === 403
      ) {
        setError(
          "You do not have permission to view these accounts."
        );
      } else {
        setError(
          err.response?.data?.detail ||
            "Unable to load accounts."
        );
      }
    } finally {
      setLoading(false);
    }
  };

  // Sends the transfer to the backend and reports the result. Separate
  // from loadAccounts above since it's a different action entirely,
  // moving money rather than reading it.
  const handleTransfer = async () => {
    // Clear any previous result before trying again.
    setTransferMessage("");
    setTransferError("");

    try {
      const response = await api.post(
        "/api/v1/transactions/transfer",
        {
          // Form inputs are strings by default, the backend expects
          // numbers, so each one gets converted here before sending.
          from_account_id: Number(fromAccount),
          to_account_id: Number(toAccount),
          amount: Number(transferAmount),
        }
      );

      // The backend returns the updated source balance on success, shown
      // directly so the user can see the transfer actually went through.
      setTransferMessage(
        `Transfer successful. New balance: $${response.data.source_balance}`
      );
      // Reset the form now that the transfer completed.
      setFromAccount("");
      setToAccount("");
      setTransferAmount("");
    } catch (err) {
      console.error(err);

      // 403 specifically means the backend's ownership check rejected the
      // transfer, a CUSTOMER trying to move money out of an account that
      // isn't theirs. Anything else falls back to whatever detail message
      // the backend sent, or a generic message if there isn't one.
      if (err.response?.status === 403) {
        setTransferError(
          "Cannot transfer from an account you don't own."
        );
      } else {
        setTransferError(
          err.response?.data?.detail ||
            "Transfer failed."
        );
      }
    }
  };

  const totalBalance =
    accounts.reduce(
      (total, account) =>
        total + Number(account.balance),
      0
    );

  return (
    <Container
      maxWidth="lg"
      sx={{
        py: 4,
      }}
    >
      <Typography
        variant="h4"
        component="h1"
        sx={{
          fontWeight: 600,
          mb: 1,
        }}
      >
        Account View
      </Typography>

      <Typography
        variant="body1"
        sx={{
          color: "text.secondary",
          mb: 4,
        }}
      >
        Search for accounts by branch and minimum balance.
      </Typography>

      <Card
        variant="outlined"
        sx={{
          mb: 4,
        }}
      >
        <CardContent>
          <Typography
            variant="h6"
            sx={{
              mb: 2,
            }}
          >
            Account Search
          </Typography>

          <Stack
            direction={{
              xs: "column",
              md: "row",
            }}
            spacing={2}
          >
            <TextField
              label="Branch Code"
              type="number"
              value={branchCode}
              onChange={(event) =>
                setBranchCode(
                  event.target.value
                )
              }
              fullWidth
            />

            <TextField
              label="Minimum Balance"
              type="number"
              value={minBalance}
              onChange={(event) =>
                setMinBalance(
                  event.target.value
                )
              }
              fullWidth
            />

            <Button
              variant="contained"
              onClick={loadAccounts}
              sx={{
                minWidth: 130,
                backgroundColor: "#21b66f",
                color: "#ffffff",
                "&:hover": {
                  backgroundColor: "#18985b",
                },
              }}
            >
              SEARCH
            </Button>
          </Stack>
        </CardContent>
      </Card>

      {error && (
        <Alert
          severity="error"
          sx={{
            mb: 3,
          }}
        >
          {error}
        </Alert>
      )}

      {loading ? (
        <Box
          sx={{
            display: "flex",
            justifyContent: "center",
            py: 5,
          }}
        >
          <CircularProgress />
        </Box>
      ) : accounts.length > 0 ? (
        <>
          <Stack
            direction={{
              xs: "column",
              md: "row",
            }}
            spacing={3}
            sx={{
              mb: 3,
            }}
          >
            <Card
              variant="outlined"
              sx={{
                flex: 1,
              }}
            >
              <CardContent>
                <Typography
                  variant="overline"
                  color="text.secondary"
                >
                  TOTAL BALANCE
                </Typography>

                <Typography
                  variant="h4"
                  sx={{
                    mt: 1,
                    fontWeight: 600,
                  }}
                >
                  $
                  {totalBalance.toFixed(
                    2
                  )}
                </Typography>
              </CardContent>
            </Card>

            <Card
              variant="outlined"
              sx={{
                flex: 1,
              }}
            >
              <CardContent>
                <Typography
                  variant="overline"
                  color="text.secondary"
                >
                  ACCOUNTS
                </Typography>

                <Typography
                  variant="h4"
                  sx={{
                    mt: 1,
                    fontWeight: 600,
                  }}
                >
                  {accounts.length}
                </Typography>
              </CardContent>
            </Card>
          </Stack>

          <Stack spacing={2}>
            {accounts.map(
              (account) => (
                <Card
                  key={
                    account.account_number
                  }
                  variant="outlined"
                >
                  <CardContent>
                    {/* justifyContent goes in sx rather than being passed
                        as a prop. MUI dropped the system props it used to
                        accept directly on Stack, so the bare attribute was
                        silently ignored and the balance sat next to the
                        account details instead of at the far edge. */}
                    <Stack
                      direction={{
                        xs: "column",
                        md: "row",
                      }}
                      spacing={2}
                      sx={{
                        justifyContent:
                          "space-between",
                      }}
                    >
                      <Box>
                        <Typography
                          variant="overline"
                          color="text.secondary"
                        >
                          {
                            account.account_type
                          }
                        </Typography>

                        <Typography
                          variant="h6"
                          sx={{
                            mb: 1,
                          }}
                        >
                          Account #
                          {
                            account.account_number
                          }
                        </Typography>

                        <Typography variant="body2">
                          <strong>
                            Owner:
                          </strong>{" "}
                          {account.owner}
                        </Typography>

                        <Typography variant="body2">
                          <strong>
                            Owner ID:
                          </strong>{" "}
                          {
                            account.owner_id
                          }
                        </Typography>

                        <Typography variant="body2">
                          <strong>
                            Branch:
                          </strong>{" "}
                          {
                            account.branch_code
                          }
                        </Typography>
                      </Box>

                      <Box>
                        <Typography
                          variant="body2"
                          color="text.secondary"
                        >
                          Balance
                        </Typography>

                        <Typography
                          variant="h4"
                          sx={{
                            fontWeight: 600,
                          }}
                        >
                          $
                          {Number(
                            account.balance
                          ).toFixed(2)}
                        </Typography>
                      </Box>
                    </Stack>
                  </CardContent>
                </Card>
              )
            )}
          </Stack>
        </>
      ) : (
        <Card variant="outlined">
          <CardContent
            sx={{
              textAlign: "center",
              py: 6,
            }}
          >
            <Typography
              variant="h6"
              sx={{
                mb: 1,
              }}
            >
              {searched
                ? "No accounts found"
                : "No accounts loaded"}
            </Typography>

            <Typography
              color="text.secondary"
            >
              {searched
                ? "No accounts matched your search."
                : "Enter a branch code and select Search."}
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* Transfer form. Always visible below the search results, whether
          or not a search has actually been run, since it's a separate
          feature from account lookup. */}
      <Card
        variant="outlined"
        sx={{
          mt: 4,
        }}
      >
        <CardContent>
          <Typography
            variant="h6"
            sx={{
              mb: 2,
            }}
          >
            Transfer Money
          </Typography>

          {/* Success and error messages are mutually exclusive in
              practice, only one is ever set at a time by handleTransfer. */}
          {transferMessage && (
            <Alert
              severity="success"
              sx={{
                mb: 2,
              }}
            >
              {transferMessage}
            </Alert>
          )}

          {transferError && (
            <Alert
              severity="error"
              sx={{
                mb: 2,
              }}
            >
              {transferError}
            </Alert>
          )}

          <Stack spacing={2}>
            {/* Each field is a controlled input, tied directly to its own
                piece of state, same pattern the search fields above use. */}
            <TextField
              label="From Account Number"
              value={fromAccount}
              onChange={(event) =>
                setFromAccount(
                  event.target.value
                )
              }
              fullWidth
            />

            <TextField
              label="To Account Number"
              value={toAccount}
              onChange={(event) =>
                setToAccount(
                  event.target.value
                )
              }
              fullWidth
            />

            <TextField
              label="Amount"
              type="number"
              value={transferAmount}
              onChange={(event) =>
                setTransferAmount(
                  event.target.value
                )
              }
              fullWidth
            />

            <Button
              variant="contained"
              onClick={handleTransfer}
              sx={{
                backgroundColor: "#21b66f",
                color: "#ffffff",
                "&:hover": {
                  backgroundColor: "#18985b",
                },
              }}
            >
              TRANSFER
            </Button>
          </Stack>
        </CardContent>
      </Card>
    </Container>
  );
}

export default AccountView;