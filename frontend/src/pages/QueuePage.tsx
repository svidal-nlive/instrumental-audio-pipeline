import React, { useState, useEffect } from 'react';
import { apiConfig } from '../config/api';
import {
  Typography,
  Box,
  Card,
  CardContent,
  Button,
  Chip,
  LinearProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Grid,
  Paper
} from '@mui/material';
import {
  PlayArrow,
  Pause,
  Queue as QueueIcon,
  Schedule,
  Settings,
  CheckCircle,
  Error as ErrorIcon,
  Refresh
} from '@mui/icons-material';

interface QueueStats {
  pending: number;
  processing: number;
  completed: number;
  failed: number;
  total: number;
}

interface QueueJob {
  id: string;
  filename: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  splitter: string;
  created_at: string;
  position?: number;
}

const QueuePage: React.FC = () => {
  const [jobs, setJobs] = useState<QueueJob[]>([]);
  const [stats, setStats] = useState<QueueStats>({
    pending: 0,
    processing: 0,
    completed: 0,
    failed: 0,
    total: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [queueRunning, setQueueRunning] = useState(true);

  const fetchQueueData = async () => {
    try {
      setLoading(true);
      
      // Fetch all jobs
      const response = await fetch(`${apiConfig.endpoints.jobs}?limit=100`);
      if (!response.ok) {
        throw new Error('Failed to fetch queue data');
      }
      
      const allJobs = await response.json();
      
      // Calculate stats
      const newStats = allJobs.reduce((acc: QueueStats, job: QueueJob) => {
        acc[job.status as keyof QueueStats]++;
        acc.total++;
        return acc;
      }, { pending: 0, processing: 0, completed: 0, failed: 0, total: 0 });
      
      // Sort jobs: processing first, then pending, then others by date
      const sortedJobs = allJobs.sort((a: QueueJob, b: QueueJob) => {
        const statusOrder = { processing: 1, pending: 2, completed: 3, failed: 4 };
        if (a.status !== b.status) {
          return statusOrder[a.status] - statusOrder[b.status];
        }
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      });
      
      // Add position for pending jobs
      let pendingPosition = 1;
      const jobsWithPosition = sortedJobs.map((job: QueueJob) => {
        if (job.status === 'pending') {
          return { ...job, position: pendingPosition++ };
        }
        return job;
      });
      
      setJobs(jobsWithPosition);
      setStats(newStats);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch queue data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueueData();
  }, []);

  useEffect(() => {
    // Auto-refresh every 3 seconds
    const interval = setInterval(() => {
      fetchQueueData();
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending': return <Schedule color="warning" />;
      case 'processing': return <Settings color="primary" />;
      case 'completed': return <CheckCircle color="success" />;
      case 'failed': return <ErrorIcon color="error" />;
      default: return <QueueIcon />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'processing': return 'primary';
      case 'pending': return 'warning';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const currentlyProcessing = jobs.filter(job => job.status === 'processing');
  const pendingJobs = jobs.filter(job => job.status === 'pending');
  const recentCompleted = jobs.filter(job => job.status === 'completed' || job.status === 'failed').slice(0, 5);

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" gutterBottom>
          Processing Queue
        </Typography>
        <Box display="flex" gap={2}>
          <Chip
            icon={queueRunning ? <PlayArrow /> : <Pause />}
            label={queueRunning ? 'Queue Running' : 'Queue Paused'}
            color={queueRunning ? 'success' : 'warning'}
          />
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={fetchQueueData}
            disabled={loading}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {loading && <LinearProgress sx={{ mb: 3 }} />}

      {/* Queue Statistics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={6} sm={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h4" color="warning.main">
              {stats.pending}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Pending
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h4" color="primary.main">
              {stats.processing}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Processing
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h4" color="success.main">
              {stats.completed}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Completed
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h4" color="error.main">
              {stats.failed}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Failed
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Currently Processing */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Currently Processing
              </Typography>
              {currentlyProcessing.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  No jobs currently processing
                </Typography>
              ) : (
                <List>
                  {currentlyProcessing.map((job) => (
                    <ListItem key={job.id}>
                      <ListItemIcon>
                        {getStatusIcon(job.status)}
                      </ListItemIcon>
                      <ListItemText
                        primary={job.filename}
                        secondary={
                          <Box>
                            <Typography variant="body2" component="span">
                              {job.splitter} • {formatDate(job.created_at)}
                            </Typography>
                            <LinearProgress
                              variant="determinate"
                              value={job.progress}
                              sx={{ mt: 1 }}
                            />
                            <Typography variant="caption">
                              {job.progress}% complete
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Queue */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Queue ({pendingJobs.length} pending)
              </Typography>
              {pendingJobs.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  No jobs in queue
                </Typography>
              ) : (
                <List>
                  {pendingJobs.slice(0, 10).map((job) => (
                    <ListItem key={job.id}>
                      <ListItemIcon>
                        <Chip
                          label={job.position}
                          size="small"
                          color="warning"
                        />
                      </ListItemIcon>
                      <ListItemText
                        primary={job.filename}
                        secondary={`${job.splitter} • ${formatDate(job.created_at)}`}
                      />
                    </ListItem>
                  ))}
                  {pendingJobs.length > 10 && (
                    <ListItem>
                      <ListItemText
                        primary={`... and ${pendingJobs.length - 10} more jobs`}
                        sx={{ fontStyle: 'italic', color: 'text.secondary' }}
                      />
                    </ListItem>
                  )}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Activity
              </Typography>
              {recentCompleted.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  No recent activity
                </Typography>
              ) : (
                <List>
                  {recentCompleted.map((job, index) => (
                    <React.Fragment key={job.id}>
                      <ListItem>
                        <ListItemIcon>
                          {getStatusIcon(job.status)}
                        </ListItemIcon>
                        <ListItemText
                          primary={job.filename}
                          secondary={
                            <Box display="flex" justifyContent="space-between" alignItems="center">
                              <Typography variant="body2">
                                {job.splitter} • {formatDate(job.created_at)}
                              </Typography>
                              <Chip
                                label={job.status}
                                size="small"
                                color={getStatusColor(job.status) as any}
                              />
                            </Box>
                          }
                        />
                      </ListItem>
                      {index < recentCompleted.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default QueuePage;
