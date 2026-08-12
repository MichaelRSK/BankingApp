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
  Toolbar,
  Typography,
} from '@mui/material';
import AccountBalanceIcon from '@mui/icons-material/AccountBalance';
import MenuIcon from '@mui/icons-material/Menu';

const APP_NAME = 'BankingApp';

const NAV_LINKS = [
  { label: 'Dashboard', path: '/dashboard' },
  { label: 'Analytics', path: '/analytics' },
  { label: 'Accounts', path: '/accounts' },
];

function NavBar() {
  const [mobileOpen, setMobileOpen] = useState(false);

  const toggleDrawer = () => setMobileOpen((prev) => !prev);

  // Contents of the mobile drawer. Clicking any link closes the drawer.
  const drawer = (
    <Box onClick={toggleDrawer} sx={{ textAlign: 'center' }}>
      <Typography variant="h6" sx={{ my: 2 }}>
        {APP_NAME}
      </Typography>
      <Divider />
      <List>
        {NAV_LINKS.map((link) => (
          <ListItem key={link.path} disablePadding>
            <ListItemButton
              component={NavLink}
              to={link.path}
              sx={{
                textAlign: 'center',
                '&.active': { bgcolor: 'action.selected' },
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
      <AppBar component="nav" position="static">
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
          <AccountBalanceIcon sx={{ mr: 1, display: { xs: 'none', sm: 'flex' } }} />
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
                  color: 'inherit',
                  '&.active': {
                    borderBottom: '2px solid',
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
          '& .MuiDrawer-paper': { boxSizing: 'border-box', width: 240 },
        }}
      >
        {drawer}
      </Drawer>
    </>
  );
}

export default NavBar;