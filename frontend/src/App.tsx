import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Container, AppBar, Toolbar, Typography } from '@mui/material';
import HomePage from './pages/HomePage';
import UploadPage from './pages/UploadPage';
import JobsPage from './pages/JobsPage';
import QueuePage from './pages/QueuePage';
import SystemPage from './pages/SystemPage';
import Navigation from './components/Navigation';

function App() {
  return (
    <div className="App">
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            🎵 Instrumental Maker 2.0
          </Typography>
        </Toolbar>
      </AppBar>
      
      <Navigation />
      
      <Container maxWidth="lg" sx={{ mt: 3, mb: 3 }}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/jobs" element={<JobsPage />} />
          <Route path="/queue" element={<QueuePage />} />
          <Route path="/system" element={<SystemPage />} />
        </Routes>
      </Container>
    </div>
  );
}

export default App;
