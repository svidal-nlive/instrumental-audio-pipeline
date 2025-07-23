import React from 'react';
import { 
  Tabs, 
  Tab, 
  Box 
} from '@mui/material';
import { useLocation, useNavigate } from 'react-router-dom';

const Navigation: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const routes = [
    { label: 'Home', path: '/' },
    { label: 'Upload', path: '/upload' },
    { label: 'Jobs', path: '/jobs' },
    { label: 'Queue', path: '/queue' },
    { label: 'System', path: '/system' }
  ];

  const currentTab = routes.findIndex(route => route.path === location.pathname);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    navigate(routes[newValue].path);
  };

  return (
    <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
      <Tabs 
        value={currentTab === -1 ? 0 : currentTab} 
        onChange={handleTabChange}
        centered
      >
        {routes.map((route, index) => (
          <Tab key={index} label={route.label} />
        ))}
      </Tabs>
    </Box>
  );
};

export default Navigation;
