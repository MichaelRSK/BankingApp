import { useState } from 'react';
import { Link as RouterLink, NavLink } from 'react-router-dom';
import {
  AppBar,
  Box,
  Button,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  SvgIcon,
  Toolbar,
  Typography,
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';

const APP_NAME = 'QMMO Bank';

// Palette lifted from the shield favicon: navy plate, green shield, cream detail.
const NAVY = '#122A47';
const GREEN = '#2F9E63';
const CREAM = '#F3EAE0';

const NAV_LINKS = [
  { label: 'Dashboard', path: '/dashboard' },
  { label: 'Analytics', path: '/analytics' },
  { label: 'Accounts', path: '/accounts' },
];

// The shield mark from public/favicon.svg. The navy backing plate is dropped
// since the mark already sits on the navy app bar.
function ShieldIcon(props) {
  return (
    <SvgIcon viewBox="14 10 36 43.5" {...props}>
      <path
        d="M32 12 48 17.5V33c0 9.5-6.8 15.6-16 18.5C22.8 48.6 16 42.5 16 33V17.5Z"
        fill={GREEN}
      />
      <g
        fill="none"
        stroke={CREAM}
        strokeWidth="3.1"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M32 18.6v25.8" />
        <path d="M37.3 26.3c0-3.5-2.4-5.3-5.3-5.3s-5.3 1.8-5.3 4.6c0 2.8 2.5 4 5.3 4.8s5.6 2.1 5.6 5.2c0 3-2.5 5-5.6 5s-5.6-1.8-5.6-5" />
      </g>
    </SvgIcon>
  );
}

function NavBar() {
  const [mobileOpen, setMobileOpen] = useState(false);

  const toggleDrawer = () => setMobileOpen((prev) => !prev);

  // Contents of the mobile drawer. Clicking any link closes the drawer.
  const drawer = (
    <Box onClick={toggleDrawer} sx={{ textAlign: 'center', height: '100%' }}>
      <Typography variant="h6" sx={{ my: 2, fontWeight: 600 }}>
        {APP_NAME}
      </Typography>
      <Divider sx={{ borderColor: GREEN }} />
      <List>
        {NAV_LINKS.map((link) => (
          <ListItem key={link.path} disablePadding>
            <ListItemButton
              component={NavLink}
              to={link.path}
              sx={{
                textAlign: 'center',
                color: CREAM,
                '&.active': { color: GREEN, bgcolor: 'rgba(47, 158, 99, 0.16)' },
              }}
            >
              <ListItemText primary={link.label} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Box>
  );

  return (
    <>
      <AppBar
        component="nav"
        position="static"
        sx={{ bgcolor: NAVY, color: CREAM, borderBottom: `3px solid ${GREEN}` }}
      >
        <Toolbar>
          {/* Hamburger: visible only below the md breakpoint */}
          <IconButton
            color="inherit"
            aria-label="open navigation menu"
            edge="start"
            onClick={toggleDrawer}
            sx={{ mr: 2, display: { xs: 'flex', md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>

          {/* Logo / app name on the left, links back to the dashboard */}
          <ShieldIcon sx={{ mr: 1, display: { xs: 'none', sm: 'flex' } }} />
          <Typography
            variant="h6"
            component={RouterLink}
            to="/dashboard"
            sx={{
              flexGrow: 1,
              color: 'inherit',
              textDecoration: 'none',
              fontWeight: 600,
            }}
          >
            {APP_NAME}
          </Typography>

          {/* Full nav links on the right: visible from md and up */}
          <Box sx={{ display: { xs: 'none', md: 'flex' }, gap: 1 }}>
            {NAV_LINKS.map((link) => (
              <Button
                key={link.path}
                component={NavLink}
                to={link.path}
                sx={{
                  color: CREAM,
                  '&:hover': { bgcolor: 'rgba(47, 158, 99, 0.16)' },
                  '&.active': {
                    color: GREEN,
                    borderBottom: `2px solid ${GREEN}`,
                    borderRadius: 0,
                  },
                }}
              >
                {link.label}
              </Button>
            ))}
          </Box>
        </Toolbar>
      </AppBar>

      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={toggleDrawer}
        ModalProps={{ keepMounted: true }} // better open performance on mobile
        sx={{
          display: { xs: 'block', md: 'none' },
          '& .MuiDrawer-paper': {
            boxSizing: 'border-box',
            width: 240,
            bgcolor: NAVY,
            color: CREAM,
          },
        }}
      >
        {drawer}
      </Drawer>
    </>
  );
}

export default NavBar;