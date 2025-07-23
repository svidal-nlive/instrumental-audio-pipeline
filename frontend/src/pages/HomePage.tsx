import React from 'react';
import { 
  Container, 
  Typography, 
  Grid, 
  Card, 
  CardContent, 
  Button,
  Box 
} from '@mui/material';
import { 
  CloudUpload, 
  QueueMusic, 
  Settings, 
  MusicNote 
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

const HomePage: React.FC = () => {
  const navigate = useNavigate();

  const features = [
    {
      title: 'Upload Files',
      description: 'Upload single tracks or entire albums for processing',
      icon: <CloudUpload fontSize="large" />,
      action: () => navigate('/upload')
    },
    {
      title: 'View Queue',
      description: 'Monitor processing queue and job status',
      icon: <QueueMusic fontSize="large" />,
      action: () => navigate('/queue')
    },
    {
      title: 'Browse Jobs',
      description: 'View completed jobs and download results',
      icon: <MusicNote fontSize="large" />,
      action: () => navigate('/jobs')
    },
    {
      title: 'System Status',
      description: 'Check system health and configuration',
      icon: <Settings fontSize="large" />,
      action: () => navigate('/system')
    }
  ];

  return (
    <Container maxWidth="lg">
      <Box sx={{ textAlign: 'center', mb: 6 }}>
        <Typography variant="h2" component="h1" gutterBottom>
          🎵 Instrumental Maker 2.0
        </Typography>
        <Typography variant="h5" color="text.secondary" paragraph>
          Create instrumental versions of your favorite songs using AI-powered stem separation
        </Typography>
      </Box>

      <Grid container spacing={4}>
        {features.map((feature, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card 
              sx={{ 
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                cursor: 'pointer',
                '&:hover': {
                  elevation: 8,
                  transform: 'translateY(-2px)',
                  transition: 'all 0.3s'
                }
              }}
              onClick={feature.action}
            >
              <CardContent sx={{ flexGrow: 1, textAlign: 'center' }}>
                <Box sx={{ color: 'primary.main', mb: 2 }}>
                  {feature.icon}
                </Box>
                <Typography variant="h6" component="h2" gutterBottom>
                  {feature.title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {feature.description}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Box sx={{ mt: 6, textAlign: 'center' }}>
        <Typography variant="h6" gutterBottom>
          How it works
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          1. Upload your audio files (MP3, WAV, FLAC, etc.)
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          2. Our AI models separate the vocals from the instrumental tracks
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          3. Download your clean instrumental versions
        </Typography>
      </Box>
    </Container>
  );
};

export default HomePage;
