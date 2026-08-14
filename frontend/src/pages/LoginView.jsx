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
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import VisibilityIcon from "@mui/icons-material/Visibility";
import VisibilityOffIcon from "@mui/icons-material/VisibilityOff";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";

// Same shared Axios instance every other page uses, already attaches the
// JWT to every request via its interceptor.
import api from "../api/api";

// Gives access to login(), which stores the token in AuthContext once a
// login request succeeds.
import { useAuth } from "../context/AuthContext.jsx";

// useNavigate sends the user to the dashboard after a successful login.
// RouterLink (aliased so it doesn't clash with MUI's own Link component
// below) wires the "Sign up" text to the real /signup route instead of
// the old dead href="#".
import { useNavigate, Link as RouterLink } from 'react-router-dom';

// Color palette for this page, shared with SignUpView.jsx so the two
// pages read as one flow rather than two different screens.
const ACCENT = "#21b66f";
// Hover shade for the accent button. The same darker green the buttons on
// AccountView, AnalyticsView and LimitsView already use, so every primary
// button in the app darkens to the same colour on hover.
const ACCENT_HOVER = "#18985b";
const BG = "#101418";
const PANEL = "#171B21";
const BORDER = "#242931";
const TEXT = "#F2EFEA";
const SUBTEXT = "#8A8F98";


// Static FAQ content shown below the login form. Plain hardcoded text, no
// backend call involved, just something a visitor can scroll down to read.
const FAQS = [
  {
    question: "How do I create an account?",
    answer:
      "Click \"Sign up\" below the login form. You'll need a full name, username, email, branch code, and password. A $0 Checking account is opened for you automatically.",
  },
  {
    question: "I forgot my password, what do I do?",
    answer:
      "Password resets aren't available yet through the site. Contact your branch directly for help regaining access.",
  },
  {
    question: "What can I do once I'm logged in?",
    answer:
      "Customers can view their account balances and recent activity on the Dashboard, search accounts, and transfer money between accounts. Branch managers and admins see branch performance metrics instead.",
  },
  {
    question: "Is my information secure?",
    answer:
      "Passwords are never stored in plain text, and every page that shows account data requires you to be signed in first.",
  },
];

export default function LoginView() {
  // Controlled inputs for the two fields on this form.
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  // Toggles the password field between hidden and plain text.
  const [showPassword, setShowPassword] = useState(false);
  // Holds an error message to display, empty string means no error.
  const [error, setError] = useState("");
  // Disables the submit button and swaps its label while a request is
  // in flight, so a slow network can't produce a double submission.
  const [submitting, setSubmitting] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    
    // Stops the browser from doing a full page reload on form submit,
    // which would wipe out the component state above.
    e.preventDefault();
    setError("");

    // Simple required-field check before any network call, so an empty
    // form never even reaches the backend.
    if (!username || !password) {
      setError("Enter your username and password to continue.");
      return;
    }

    setSubmitting(true);

    try {
      const response = await api.post('/api/v1/login', {
        username: username,
        password: password
      });

      // Stores the token from AuthContext, then sends the user straight
      // to their dashboard. replace: true so the login page isn't left
      // sitting in browser history behind them.
      login(response.data.access_token);
      navigate('/dashboard', { replace: true });
    } catch (err) {
      
      // 401 specifically means bad credentials, deliberately vague about
      // which one was wrong, same reasoning as the backend's attempt_login.
      // Anything else with a response is an unexpected server error, and no
      // response at all means the request never reached the backend.
      if (err.response?.status === 401) {
        setError("Invalid username or password.");
      } else if (err.response) {
        setError("Something went wrong signing you in. Please try again.");
      } else {
        setError("Could not reach the server. Is the backend running?");
      }
    } finally {
     
      // Always runs, so a failed attempt cannot leave the button stuck
      // on "Signing in...".
      setSubmitting(false);
    }
  };

  // Shared styling for every text field on this form.
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
    // Full-height dark background, form centered both ways.
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
        {/* Header: logo dot, title, subtitle. */}
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

        {/* The form itself lives in a Paper card. onSubmit is on the
            Paper (not the button) so pressing Enter in either field
            submits the form too, not just clicking Sign in. */}
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
            Username
          </Typography>
          <TextField
            id="username"
            type="username"
            fullWidth
            size="small"
            placeholder="XxJontronxX"
            autoComplete="username"
            value={username}
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
             
              // Eye icon inside the field that flips showPassword,
              // swapping which icon is shown and what the field's type is.
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

          {/* Not wired to anything yet, purely visual for now. */}
          <Box sx={{ display: "flex", justifyContent: "flex-end", mb: 2.5 }}>
            <Link
              href="#"
              underline="none"
              sx={{ fontSize: "0.75rem", color: SUBTEXT, "&:hover": { color: TEXT } }}
            >
              Forgot password?
            </Link>
          </Box>

          {/* Only rendered once handleSubmit has actually set an error. */}
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

          {/* Submit button, disabled and relabeled while submitting is
              true so the user gets feedback instead of a dead click. */}
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
              "&:hover": { backgroundColor: ACCENT_HOVER },
              "&.Mui-disabled": { backgroundColor: `${ACCENT}99`, color: BG },
            }}
          >
            {submitting ? "Signing in..." : "Sign in"}
          </Button>
        </Paper>

        {/* Footer link to /signup, the mirror image of the "Already have
            an account? Sign in" link on SignUpView.jsx. */}
        <Typography sx={{ textAlign: "center", mt: 3, fontSize: "0.875rem", color: "#565C66" }}>
          Don't have an account?{" "}
          {/* Was href="#", pointed nowhere. Now routes to the actual sign-up page. */}
          <Link component={RouterLink} to="/signup" underline="none" sx={{ color: TEXT, "&:hover": { color: ACCENT } }}>
            Sign up
          </Link>
        </Typography>
        
        {/* FAQ section, sits below the fold so it's reached by scrolling
            rather than crowding the login form itself. */}
        <Box sx={{ mt: 6, mb: 4 }}>
          <Typography
            variant="h6"
            sx={{ color: TEXT, fontWeight: 600, mb: 2, textAlign: "center" }}
          >
            Frequently Asked Questions
          </Typography>

          {FAQS.map((faq, index) => (
            <Accordion
              key={index}
              disableGutters
              sx={{
                backgroundColor: PANEL,
                border: `1px solid ${BORDER}`,
                color: TEXT,
                mb: 1,
                "&:before": { display: "none" },
              }}
            >
              <AccordionSummary
                expandIcon={<ExpandMoreIcon sx={{ color: SUBTEXT }} />}
              >
                <Typography sx={{ fontSize: "0.875rem", fontWeight: 600 }}>
                  {faq.question}
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Typography sx={{ fontSize: "0.8125rem", color: SUBTEXT }}>
                  {faq.answer}
                </Typography>
              </AccordionDetails>
            </Accordion>
          ))}
        </Box>
      </Box>
    </Box>
  );
}