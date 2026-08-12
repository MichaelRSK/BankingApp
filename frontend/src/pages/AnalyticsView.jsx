import { useMemo, useState } from "react";

import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Container,
  MenuItem,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";

import AnalyticsIcon from "@mui/icons-material/Analytics";
import PaidIcon from "@mui/icons-material/Paid";
import ReceiptLongIcon from "@mui/icons-material/ReceiptLong";

import api from "../api/api";

function AnalyticsView() {
  const [startDate, setStartDate] = useState("2026-01-01");
  const [transactionType, setTransactionType] = useState("TRANSFER");

  const [transactions, setTransactions] = useState([]);
  const [searched, setSearched] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const totalAmount = useMemo(() => {
    return transactions.reduce(
      (total, transaction) =>
        total + Number(transaction.amount),
      0
    );
  }, [transactions]);

  const averageAmount = useMemo(() => {
    if (transactions.length === 0) {
      return 0;
    }

    return totalAmount / transactions.length;
  }, [transactions, totalAmount]);

  const loadTransactions = async () => {
    setLoading(true);
    setError("");
    setSearched(true);

    try {
      const response = await api.get("/api/v1/transactions", {
        params: {
          start_date: startDate,
          type: transactionType,
        },
      });

      setTransactions(response.data);
    } catch (err) {
      console.error(err);

      if (err.response?.status === 401) {
        setError("You must be logged in to view analytics.");
      } else if (err.response?.status === 403) {
        setError("You do not have permission to view this information.");
      } else {
        setError(
          err.response?.data?.detail ||
            "Unable to load transaction information."
        );
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* PAGE TITLE */}
      <Typography
        variant="h4"
        component="h1"
        sx={{
          fontWeight: 600,
          mb: 1,
        }}
      >
        Analytics View
      </Typography>

      <Typography
        variant="body1"
        sx={{
          color: "text.secondary",
          mb: 4,
        }}
      >
        Search transaction activity and review account activity statistics.
      </Typography>

      {/* SEARCH AREA */}
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
            Transaction Search
          </Typography>

          <Stack
            direction={{
              xs: "column",
              md: "row",
            }}
            spacing={2}
          >
            <TextField
              label="Start Date"
              type="date"
              value={startDate}
              onChange={(event) => setStartDate(event.target.value)}
              InputLabelProps={{
                shrink: true,
              }}
              fullWidth
            />

            <TextField
              select
              label="Transaction Type"
              value={transactionType}
              onChange={(event) => setTransactionType(event.target.value)}
              fullWidth
            >
              <MenuItem value="TRANSFER">
                Transfer
              </MenuItem>

              <MenuItem value="DEPOSIT">
                Deposit
              </MenuItem>

              <MenuItem value="WITHDRAWAL">
                Withdrawal
              </MenuItem>
            </TextField>

            <Button
              variant="contained"
              onClick={loadTransactions}
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

      {/* ERROR MESSAGE */}
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

      {/* ANALYTICS CARDS */}
      <Stack
        direction={{
          xs: "column",
          md: "row",
        }}
        spacing={3}
        sx={{
          mb: 4,
        }}
      >
        {/* TRANSACTIONS */}
        <Card
          variant="outlined"
          sx={{
            flex: 1,
          }}
        >
          <CardContent>
            <Stack
              direction="row"
              spacing={2}
              alignItems="center"
            >
              <ReceiptLongIcon
                sx={{
                  fontSize: 36,
                  color: "#21b66f",
                }}
              />

              <Box>
                <Typography
                  variant="body1"
                  sx={{
                    mb: 1,
                  }}
                >
                  Transactions
                </Typography>

                <Typography
                  variant="h4"
                  sx={{
                    fontWeight: 600,
                  }}
                >
                  {transactions.length}
                </Typography>
              </Box>
            </Stack>
          </CardContent>
        </Card>

        {/* TOTAL AMOUNT */}
        <Card
          variant="outlined"
          sx={{
            flex: 1,
          }}
        >
          <CardContent>
            <Stack
              direction="row"
              spacing={2}
              alignItems="center"
            >
              <PaidIcon
                sx={{
                  fontSize: 36,
                  color: "#21b66f",
                }}
              />

              <Box>
                <Typography
                  variant="body1"
                  sx={{
                    mb: 1,
                  }}
                >
                  Total Amount
                </Typography>

                <Typography
                  variant="h4"
                  sx={{
                    fontWeight: 600,
                  }}
                >
                  ${totalAmount.toFixed(2)}
                </Typography>
              </Box>
            </Stack>
          </CardContent>
        </Card>

        {/* AVERAGE AMOUNT */}
        <Card
          variant="outlined"
          sx={{
            flex: 1,
          }}
        >
          <CardContent>
            <Stack
              direction="row"
              spacing={2}
              alignItems="center"
            >
              <AnalyticsIcon
                sx={{
                  fontSize: 36,
                  color: "#21b66f",
                }}
              />

              <Box>
                <Typography
                  variant="body1"
                  sx={{
                    mb: 1,
                  }}
                >
                  Average Amount
                </Typography>

                <Typography
                  variant="h4"
                  sx={{
                    fontWeight: 600,
                  }}
                >
                  ${averageAmount.toFixed(2)}
                </Typography>
              </Box>
            </Stack>
          </CardContent>
        </Card>
      </Stack>

      {/* LOADING */}
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
      ) : (
        /* TRANSACTION TABLE */
        <Card variant="outlined">
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>ID</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>From Account</TableCell>
                  <TableCell>To Account</TableCell>
                  <TableCell align="right">
                    Amount
                  </TableCell>
                  <TableCell>Date</TableCell>
                </TableRow>
              </TableHead>

              <TableBody>
                {transactions.length > 0 ? (
                  transactions.map((transaction) => (
                    <TableRow
                      key={transaction.id}
                      hover
                    >
                      <TableCell>
                        {transaction.id}
                      </TableCell>

                      <TableCell>
                        {transaction.type}
                      </TableCell>

                      <TableCell>
                        {transaction.from_account_id ?? "--"}
                      </TableCell>

                      <TableCell>
                        {transaction.to_account_id ?? "--"}
                      </TableCell>

                      <TableCell align="right">
                        ${Number(transaction.amount).toFixed(2)}
                      </TableCell>

                      <TableCell>
                        {transaction.timestamp
                          ? new Date(
                              transaction.timestamp
                            ).toLocaleString()
                          : "--"}
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell
                      colSpan={6}
                      align="center"
                      sx={{
                        py: 5,
                        color: "text.secondary",
                      }}
                    >
                      {searched
                        ? "No transactions matched your search."
                        : "No transactions loaded."}
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Card>
      )}
    </Container>
  );
}

export default AnalyticsView;