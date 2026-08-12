import { useState } from "react";
import {
  Box,
  Paper,
  Typography,
  TextField,
  InputAdornment,
  IconButton,
  Button,
  Alert,
  Link,
} from "@mui/material";
import VisibilityIcon from "@mui/icons-material/Visibility";
import VisibilityOffIcon from "@mui/icons-material/VisibilityOff";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";
import axios from "axios";

const ACCENT = "#E8664A";
const BG = "#101418";
const PANEL = "#171B21";
const BORDER = "#242931";
const TEXT = "#F2EFEA";
const SUBTEXT = "#8A8F98";

export default function LoginView() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!username || !password) {
      setError("Enter your username and password to continue.");
      return;
    }

    setSubmitting(true);
    // Mock auth call — replace with your real request.

    const response = await axios.post('localhost:8000/api/v1/login', {
      username: username,
      password: password
    });

    if(response.token) {
      useAuth(response.token);
    }
  };

  const fieldSx = {
    "& .MuiOutlinedInput-root": {
      backgroundColor: BG,
      borderRadius: "8px",
      color: TEXT,
      fontSize: "0.875rem",
      "& fieldset": { borderColor: "#2A2F38" },
      "&:hover fieldset": { borderColor: "#3A414D" },
      "&.Mui-focused fieldset": { borderColor: ACCENT, borderWidth: "2px" },
    },
    "& .MuiInputBase-input::placeholder": { color: "#565C66", opacity: 1 },
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        width: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: BG,
        px: 2,
      }}
    >
      <Box sx={{ width: "100%", maxWidth: 380 }}>
        <Box sx={{ textAlign: "center", mb: 4 }}>
          <Box
            sx={{
              mx: "auto",
              mb: 2,
              height: 36,
              width: 36,
              borderRadius: "50%",
              backgroundColor: ACCENT,
            }}
          />
          <Typography
            variant="h5"
            sx={{ color: TEXT, fontWeight: 600, letterSpacing: "-0.02em" }}
          >
            Welcome back
          </Typography>
          <Typography variant="body2" sx={{ color: SUBTEXT, mt: 0.5 }}>
            Sign in to keep going where you left off.
          </Typography>
        </Box>

        <Paper
          component="form"
          onSubmit={handleSubmit}
          elevation={0}
          sx={{
            backgroundColor: PANEL,
            border: `1px solid ${BORDER}`,
            borderRadius: "12px",
            p: 3,
          }}
        >
          <Typography
            component="label"
            htmlFor="username"
            sx={{ display: "block", fontSize: "0.75rem", color: SUBTEXT, mb: 0.75 }}
          >
            Email
          </Typography>
          <TextField
            id="username"
            type="username"
            fullWidth
            size="small"
            placeholder="XxJontronxX"
            autoComplete="username"
            value={email}
            onChange={(e) => setUsername(e.target.value)}
            sx={{ ...fieldSx, mb: 2 }}
          />

          <Typography
            component="label"
            htmlFor="password"
            sx={{ display: "block", fontSize: "0.75rem", color: SUBTEXT, mb: 0.75 }}
          >
            Password
          </Typography>
          <TextField
            id="password"
            type={showPassword ? "text" : "password"}
            fullWidth
            size="small"
            placeholder="••••••••"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            sx={{ ...fieldSx, mb: 0.5 }}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => setShowPassword((v) => !v)}
                    edge="end"
                    size="small"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                    sx={{ color: "#565C66", "&:hover": { color: SUBTEXT } }}
                  >
                    {showPassword ? (
                      <VisibilityOffIcon fontSize="small" />
                    ) : (
                      <VisibilityIcon fontSize="small" />
                    )}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          <Box sx={{ display: "flex", justifyContent: "flex-end", mb: 2.5 }}>
            <Link
              href="#"
              underline="none"
              sx={{ fontSize: "0.75rem", color: SUBTEXT, "&:hover": { color: TEXT } }}
            >
              Forgot password?
            </Link>
          </Box>

          {error && (
            <Alert
              severity="error"
              sx={{
                mb: 2,
                backgroundColor: `${ACCENT}1A`,
                border: `1px solid ${ACCENT}33`,
                color: ACCENT,
                fontSize: "0.75rem",
                py: 0.5,
                "& .MuiAlert-icon": { color: ACCENT },
              }}
            >
              {error}
            </Alert>
          )}

          <Button
            type="submit"
            fullWidth
            disabled={submitting}
            endIcon={!submitting && <ArrowForwardIcon sx={{ fontSize: 16 }} />}
            sx={{
              backgroundColor: ACCENT,
              color: BG,
              fontWeight: 600,
              fontSize: "0.875rem",
              textTransform: "none",
              borderRadius: "8px",
              py: 1.1,
              "&:hover": { backgroundColor: "#f0785d" },
              "&.Mui-disabled": { backgroundColor: `${ACCENT}99`, color: BG },
            }}
          >
            {submitting ? "Signing in..." : "Sign in"}
          </Button>
        </Paper>

        <Typography sx={{ textAlign: "center", mt: 3, fontSize: "0.875rem", color: "#565C66" }}>
          Don't have an account?{" "}
          <Link href="#" underline="none" sx={{ color: TEXT, "&:hover": { color: ACCENT } }}>
            Sign up
          </Link>
        </Typography>
      </Box>
    </Box>
  );
}