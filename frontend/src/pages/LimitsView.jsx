// useEffect loads the limits once when the page mounts, useState holds
// them once they come back.
import { useEffect, useState } from "react";

import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Container,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  LinearProgress,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from "@mui/material";

import api from "../api/api";

// The three kinds the backend accepts, paired with the label shown on
// screen. Kept as one list so the dropdown below and the card headings
// read from the same place, rather than formatting the raw "DAILY" string
// in two spots that could drift apart.
const LIMIT_TYPES = [
  { value: "PER_TRANSACTION", label: "Per Transaction Limit" },
  { value: "DAILY", label: "Daily Limit" },
  { value: "MONTHLY", label: "Monthly Limit" },
];

// Turns the stored value into its display label. Falls back to whatever the
// backend sent if a fourth kind is ever added there before it is added here,
// so an unknown limit still renders instead of showing an empty heading.
function formatLimitType(limitType) {
  const match = LIMIT_TYPES.find((type) => type.value === limitType);

  return match ? match.label : limitType;
}

// PER_TRANSACTION caps a single transfer and never accumulates, so its
// current_period_used stays at zero and a usage bar would always read empty.
// Only the two period limits get one.
function accumulates(limitType) {
  return limitType === "DAILY" || limitType === "MONTHLY";
}

function LimitsView() {
  const [limits, setLimits] = useState([]);

  // True while the first load is in flight. Starts true because this page
  // fetches on mount rather than waiting for a search, so the spinner shows
  // instead of a flash of the empty state.
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Separate state for the create form below. Kept apart from the list
  // state above since a failed create should not wipe the limits already
  // on screen.
  const [newType, setNewType] = useState("PER_TRANSACTION");
  const [newAmount, setNewAmount] = useState("");
  const [createMessage, setCreateMessage] = useState("");
  const [createError, setCreateError] = useState("");

  // The limit currently open in the edit dialog, null when it's closed.
  // Holding the whole object rather than just an id means the dialog can
  // show which limit is being edited without looking it up again.
  const [editingLimit, setEditingLimit] = useState(null);
  const [editAmount, setEditAmount] = useState("");
  const [editError, setEditError] = useState("");

  // Loads the signed-in user's own limits. The backend decides whose they
  // are from the token, so there is nothing to pass here.
  //
  // Used both on mount and after a successful create. loading only ever
  // goes from true to false, so the refresh after a create does not flash
  // the whole page back to a spinner.
  const loadLimits = async () => {
    setError("");

    try {
      const response = await api.get("/api/v1/limits");

      setLimits(response.data);
    } catch (err) {
      console.error(err);

      if (err.response?.status === 401) {
        setError("You must be logged in to view your limits.");
      } else if (err.response?.status === 403) {
        setError("You do not have permission to view these limits.");
      } else {
        setError(
          err.response?.data?.detail || "Unable to load your limits."
        );
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLimits();
    // Runs once on mount. There is nothing to re-run on, the token the
    // request interceptor attaches is read fresh from localStorage each
    // time a request goes out.
  }, []);

  // Creates a new limit, then reloads the list so the new card appears
  // without the user refreshing the page.
  const handleCreate = async () => {
    // Clear any previous result before trying again.
    setCreateMessage("");
    setCreateError("");

    // Checked here as well as on the server. The backend answers with a 400
    // either way, but catching it locally saves a round trip and gives the
    // user the same message straight away.
    if (!newAmount || Number(newAmount) <= 0) {
      setCreateError("Max amount must be greater than zero.");
      return;
    }

    try {
      await api.post("/api/v1/limits", {
        limit_type: newType,
        // The form input is a string, the backend expects a number, so it
        // gets converted here before sending.
        max_amount: Number(newAmount),
      });

      setCreateMessage(`${formatLimitType(newType)} created.`);
      // Reset the amount but leave the type selected, since setting a
      // couple of limits in a row is the common case.
      setNewAmount("");

      await loadLimits();
    } catch (err) {
      console.error(err);

      if (err.response?.status === 401) {
        setCreateError("You must be logged in to set a limit.");
      } else {
        // Shows the backend's own wording, so a rejected max_amount reads
        // exactly as the API described it.
        setCreateError(
          err.response?.data?.detail || "Unable to create the limit."
        );
      }
    }
  };

  // Opens the edit dialog for one limit, pre-filled with its current
  // ceiling so the user is editing the real value rather than a blank box.
  const openEditDialog = (limit) => {
    setEditingLimit(limit);
    setEditAmount(String(limit.max_amount));
    setEditError("");
  };

  const closeEditDialog = () => {
    setEditingLimit(null);
    setEditAmount("");
    setEditError("");
  };

  // Saves the new ceiling for the limit open in the dialog.
  //
  // Only max_amount can change. The kind of limit and who owns it are what
  // the row IS, and the backend accepts nothing else in the body.
  const handleSaveEdit = async () => {
    setEditError("");

    if (!editAmount || Number(editAmount) <= 0) {
      setEditError("Max amount must be greater than zero.");
      return;
    }

    try {
      const response = await api.put(
        `/api/v1/limits/${editingLimit.id}`,
        {
          max_amount: Number(editAmount),
        }
      );

      // Swap just the edited limit for the version the backend returned,
      // rather than reloading everything. The response is the updated row,
      // so the card is showing saved data and not a hopeful guess.
      setLimits((previous) =>
        previous.map((limit) =>
          limit.id === response.data.id ? response.data : limit
        )
      );

      closeEditDialog();
    } catch (err) {
      console.error(err);

      // 403 means the limit exists but belongs to someone else, 404 that it
      // is gone entirely, most likely deleted in another tab. Both are
      // reported inside the dialog so the user sees why the save failed
      // without losing what they typed.
      if (err.response?.status === 403) {
        setEditError("You can only edit your own limits.");
      } else if (err.response?.status === 404) {
        setEditError("That limit no longer exists.");
      } else {
        setEditError(
          err.response?.data?.detail || "Unable to update the limit."
        );
      }
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
        Transfer Limits
      </Typography>

      <Typography
        variant="body1"
        sx={{
          color: "text.secondary",
          mb: 4,
        }}
      >
        Set your own caps on outgoing transfers and see how much of each one
        you have used.
      </Typography>

      {/* CREATE FORM */}
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
            Set a New Limit
          </Typography>

          {/* Success and error messages are mutually exclusive in practice,
              only one is ever set at a time by handleCreate. */}
          {createMessage && (
            <Alert
              severity="success"
              sx={{
                mb: 2,
              }}
            >
              {createMessage}
            </Alert>
          )}

          {createError && (
            <Alert
              severity="error"
              sx={{
                mb: 2,
              }}
            >
              {createError}
            </Alert>
          )}

          <Stack
            direction={{
              xs: "column",
              md: "row",
            }}
            spacing={2}
          >
            <TextField
              select
              label="Limit Type"
              value={newType}
              onChange={(event) => setNewType(event.target.value)}
              fullWidth
            >
              {LIMIT_TYPES.map((type) => (
                <MenuItem key={type.value} value={type.value}>
                  {type.label}
                </MenuItem>
              ))}
            </TextField>

            <TextField
              label="Max Amount"
              type="number"
              value={newAmount}
              onChange={(event) => setNewAmount(event.target.value)}
              fullWidth
            />

            <Button
              variant="contained"
              onClick={handleCreate}
              sx={{
                minWidth: 130,
                backgroundColor: "#21b66f",
                color: "#ffffff",
                "&:hover": {
                  backgroundColor: "#18985b",
                },
              }}
            >
              ADD LIMIT
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
      ) : limits.length > 0 ? (
        /* LIMIT CARDS */
        <Stack spacing={2}>
          {limits.map((limit) => {
            const maxAmount = Number(limit.max_amount);
            const used = Number(limit.current_period_used);

            // Capped at 100 so a bar can never overflow its track. The
            // figures above it still show the real numbers.
            const usagePercent =
              maxAmount > 0
                ? Math.min(100, (used / maxAmount) * 100)
                : 0;

            // Turns red once the period is spent, so a maxed-out limit is
            // obvious at a glance rather than just a full green bar.
            const barColour = used >= maxAmount ? "#d32f2f" : "#21b66f";

            return (
              <Card key={limit.id} variant="outlined">
                <CardContent>
                  {/* justifyContent goes in sx rather than being passed as a
                      prop. MUI dropped the system props it used to accept
                      directly on Stack, so the bare attribute is silently
                      ignored and the Edit button ends up next to the amount
                      instead of at the far edge of the card. */}
                  <Stack
                    direction={{
                      xs: "column",
                      md: "row",
                    }}
                    spacing={2}
                    sx={{
                      justifyContent: "space-between",
                    }}
                  >
                    <Box>
                      <Typography
                        variant="overline"
                        color="text.secondary"
                      >
                        {formatLimitType(limit.limit_type)}
                      </Typography>

                      <Typography
                        variant="h4"
                        sx={{
                          fontWeight: 600,
                        }}
                      >
                        ${maxAmount.toFixed(2)}
                      </Typography>

                      {/* PER_TRANSACTION has no running total, so it gets a
                          plain description of what it does instead of a
                          "used X of Y" line that would always read $0.00. */}
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{
                          mt: 1,
                        }}
                      >
                        {accumulates(limit.limit_type)
                          ? `$${used.toFixed(2)} of $${maxAmount.toFixed(
                              2
                            )} used`
                          : "Applies to each single transfer"}
                      </Typography>
                    </Box>

                    <Box>
                      <Button
                        variant="outlined"
                        onClick={() => openEditDialog(limit)}
                        sx={{
                          minWidth: 130,
                          color: "#21b66f",
                          borderColor: "#21b66f",
                          "&:hover": {
                            borderColor: "#18985b",
                            backgroundColor: "rgba(33, 182, 111, 0.08)",
                          },
                        }}
                      >
                        EDIT
                      </Button>
                    </Box>
                  </Stack>

                  {/* USAGE BAR */}
                  {accumulates(limit.limit_type) && (
                    <Box
                      sx={{
                        mt: 2,
                      }}
                    >
                      <LinearProgress
                        variant="determinate"
                        value={usagePercent}
                        sx={{
                          height: 8,
                          borderRadius: 4,
                          backgroundColor: "rgba(0, 0, 0, 0.08)",
                          "& .MuiLinearProgress-bar": {
                            backgroundColor: barColour,
                            borderRadius: 4,
                          },
                        }}
                      />

                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{
                          mt: 1,
                        }}
                      >
                        {usagePercent.toFixed(0)}% used since{" "}
                        {new Date(
                          limit.period_start
                        ).toLocaleDateString()}
                      </Typography>
                    </Box>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </Stack>
      ) : (
        /* EMPTY STATE */
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
              No limits set
            </Typography>

            <Typography color="text.secondary">
              Add a limit above to cap how much you can transfer.
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* EDIT DIALOG */}
      <Dialog
        open={editingLimit !== null}
        onClose={closeEditDialog}
        fullWidth
        maxWidth="xs"
      >
        <DialogTitle>
          {/* editingLimit is null while the dialog is closed, and MUI keeps
              the children mounted through the closing animation, so the
              title is guarded rather than read straight off the object. */}
          Edit {editingLimit ? formatLimitType(editingLimit.limit_type) : ""}
        </DialogTitle>

        <DialogContent>
          {editError && (
            <Alert
              severity="error"
              sx={{
                mb: 2,
              }}
            >
              {editError}
            </Alert>
          )}

          <TextField
            label="Max Amount"
            type="number"
            value={editAmount}
            onChange={(event) => setEditAmount(event.target.value)}
            fullWidth
            // Without this the label sits on top of the pre-filled value
            // for the first moment the dialog is open.
            sx={{
              mt: 1,
            }}
          />
        </DialogContent>

        <DialogActions
          sx={{
            px: 3,
            pb: 2,
          }}
        >
          <Button onClick={closeEditDialog}>CANCEL</Button>

          <Button
            variant="contained"
            onClick={handleSaveEdit}
            sx={{
              backgroundColor: "#21b66f",
              color: "#ffffff",
              "&:hover": {
                backgroundColor: "#18985b",
              },
            }}
          >
            SAVE
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}

export default LimitsView;
