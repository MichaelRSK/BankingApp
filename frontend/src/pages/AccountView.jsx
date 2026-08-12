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
                    <Stack
                      direction={{
                        xs: "column",
                        md: "row",
                      }}
                      justifyContent="space-between"
                      spacing={2}
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
    </Container>
  );
}

export default AccountView;