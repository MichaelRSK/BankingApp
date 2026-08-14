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

// Same shared Axios instance every other page uses, already attaches the
// JWT to every request via its interceptor.
import api from "../api/api";

// Gives access to login(), which stores the token after registration
// succeeds so the new customer doesn't have to sign in a second time.
import { useAuth } from "../context/AuthContext.jsx";

// useNavigate sends the user to the dashboard after signup, RouterLink
// (aliased so it doesn't clash with MUI's own Link component below) wires
// the "Already have an account?" text to the real /login route.
import { useNavigate, Link as RouterLink } from 'react-router-dom';

// Same palette as LoginView.jsx, kept in sync so the two pages read as one
// flow rather than two different screens.
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

export default function SignUpView() {
 
    // One piece of state per form field, same controlled-input pattern
  // AccountView.jsx and LoginView.jsx both use.
  const [name, setName] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [branchCode, setBranchCode] = useState("");
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
    // which would wipe out all the component state above.
    e.preventDefault();
    setError("");

    // Simple required-field check before any network call, so an
    // incomplete form never even reaches the backend.
    if (!name || !username || !email || !branchCode || !password) {
      setError("Fill in every field to create an account.");
      return;
    }

    setSubmitting(true);

    try {
      
        // roles is fixed to CUSTOMER here, this page only ever creates
      // customer accounts. sub is left out entirely, the backend derives
      // it from the customers row it creates alongside this user.
      await api.post('/api/v1/registration', {
        username: username,
        password: password,
        roles: 'CUSTOMER',
        email: email,
        name: name,
       
        // Sent as typed, not converted. Branch codes are shown as "BR001"
        // and the backend accepts that form as well as a plain number, so
        // Number() here would turn "BR001" into NaN and the field would
        // arrive empty. This is the one place that deliberately differs
        // from AccountView.jsx, which still converts its transfer amounts.
        branch_code: branchCode.trim(),
      });

      // Registration only creates the account, it doesn't hand back a
      // token, so logging in right after is what actually gets the new
      // customer onto their dashboard without a second manual step.
      const loginResponse = await api.post('/api/v1/login', {
        username: username,
        password: password,
      });

      
      // Stores the token from AuthContext, then sends the user straight
      // to their dashboard. replace: true so the signup page isn't left
      // sitting in browser history behind them.
      login(loginResponse.data.access_token);
      navigate('/dashboard', { replace: true });
    } catch (err) {
      
    // Different status codes mean different things here: 409 is a
      // duplicate username/email, 400 is a validation problem the
      // backend caught (e.g. missing name/branch_code), anything else
      // with a response is an unexpected server error, and no response
      // at all means the request never reached the backend.
      if (err.response?.status === 409) {
        setError("That username or email is already registered.");
      } else if (err.response?.status === 400) {
        setError(err.response.data?.detail || "Check the form and try again.");
      } else if (err.response) {
        setError("Something went wrong creating your account. Please try again.");
      } else {
        setError("Could not reach the server. Is the backend running?");
      }
    } finally {
      
        // Always runs, so a failed attempt cannot leave the button stuck
      // on "Creating account...".
      setSubmitting(false);
    }
  };

  // Shared styling for every text field on this form, same dark-input
  // look as LoginView.jsx so the two pages match.
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

  // Same label-above-field pattern as LoginView.jsx, pulled into a helper
  // here since this form has five fields instead of two. label is the
  // text shown above the field, htmlFor doubles as both the field's id
  // and the label's htmlFor so the two stay linked, props is spread onto
  // the TextField itself (type, placeholder, value, onChange, etc).
  const labeledField = (label, htmlFor, props) => (
    <>
      <Typography
        component="label"
        htmlFor={htmlFor}
        sx={{ display: "block", fontSize: "0.75rem", color: SUBTEXT, mb: 0.75 }}
      >
        {label}
      </Typography>
      <TextField
        id={htmlFor}
        fullWidth
        size="small"
        sx={{ ...fieldSx, mb: 2 }}
        {...props}
      />
    </>
  );

  return (
    
    // Full-height dark background, form centered both ways, same shell
    // as LoginView.jsx. Extra py: 4 here since this form is taller (five
    // fields instead of two) and needs breathing room on short screens.
    <Box
      sx={{
        minHeight: "100vh",
        width: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: BG,
        px: 2,
        py: 4,
      }}
    >
      <Box sx={{ width: "100%", maxWidth: 380 }}>
        {/* Header: logo dot, title, subtitle. Same layout as LoginView.jsx. */}
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
            Create your account
          </Typography>
          <Typography variant="body2" sx={{ color: SUBTEXT, mt: 0.5 }}>
            Sign up to start managing your accounts.
          </Typography>
        </Box>

        {/* The form itself lives in a Paper card, same as LoginView.jsx.
            onSubmit on the Paper (not the button) so pressing Enter in any
            field submits the form too, not just clicking Sign up. */}
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
          {/* Four of the five fields are built with the labeledField
              helper above, since they're all plain text/number inputs
              with nothing extra going on. */}
          {labeledField("Full Name", "name", {
            placeholder: "Jane Doe",
            autoComplete: "name",
            value: name,
            onChange: (e) => setName(e.target.value),
          })}

          {labeledField("Username", "username", {
            placeholder: "XxJontronxX",
            autoComplete: "username",
            value: username,
            onChange: (e) => setUsername(e.target.value),
          })}

          {labeledField("Email", "email", {
            type: "email",
            placeholder: "jane@example.com",
            autoComplete: "email",
            value: email,
            onChange: (e) => setEmail(e.target.value),
          })}

          {/* type is text rather than number so "BR001" can be typed at
              all. A number input silently refuses non-digits, which would
              make the branch code look impossible to enter. */}
          {labeledField("Branch Code", "branchCode", {
            type: "text",
            placeholder: "BR001",
            value: branchCode,
            onChange: (e) => setBranchCode(e.target.value),
          })}

          {/* Password is written out by hand instead of using the helper,
              since it needs the show/hide toggle button the other four
              fields don't have. */}
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
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            sx={{ ...fieldSx, mb: 2.5 }}
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

          {/* Only rendered once handleSubmit has actually set an error,
              styled with the same accent-tinted look as LoginView.jsx's
              error alert. */}
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
            {submitting ? "Creating account..." : "Sign up"}
          </Button>
        </Paper>

        {/* Footer link back to /login, the mirror image of the "Don't
            have an account? Sign up" link on LoginView.jsx. */}
        <Typography sx={{ textAlign: "center", mt: 3, fontSize: "0.875rem", color: "#565C66" }}>
          Already have an account?{" "}
          <Link component={RouterLink} to="/login" underline="none" sx={{ color: TEXT, "&:hover": { color: ACCENT } }}>
            Sign in
          </Link>
        </Typography>
      </Box>
    </Box>
  );
}