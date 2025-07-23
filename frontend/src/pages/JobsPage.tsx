import React, { useState, useEffect } from 'react';
import { apiConfig } from '../config/api';
import {
  Typography,
  Box,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  Grid,
  IconButton,
  LinearProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  Pagination
} from '@mui/material';
import {
  Refresh,
  Delete,
  Download,
  Visibility,
  Replay
} from '@mui/icons-material';

interface Job {
  id: string;
  filename: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  splitter: string;
  stems_to_keep: string[];
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  output_path?: string;
}

const JobsPage: React.FC = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [page, setPage] = useState(1);
  const [totalJobs, setTotalJobs] = useState(0);
  const itemsPerPage = 10;

  const fetchJobs = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${apiConfig.endpoints.jobs}?limit=${itemsPerPage}&offset=${(page - 1) * itemsPerPage}`);
      if (!response.ok) {
        throw new Error('Failed to fetch jobs');
      }
      const data = await response.json();
      setJobs(data);
      // For now, assume total count is the length of returned data
      setTotalJobs(data.length + (page - 1) * itemsPerPage);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch jobs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, [page]);

  useEffect(() => {
    // Auto-refresh every 5 seconds for active jobs
    const interval = setInterval(() => {
      if (jobs.some(job => job.status === 'processing' || job.status === 'pending')) {
        fetchJobs();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [jobs]);

  const deleteJob = async (jobId: string) => {
    try {
      const response = await fetch(`${apiConfig.endpoints.jobs}${jobId}/`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error('Failed to delete job');
      }
      fetchJobs();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete job');
    }
  };

  const retryJob = async (jobId: string) => {
    try {
      const response = await fetch(`${apiConfig.endpoints.jobs}${jobId}/retry/`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error('Failed to retry job');
      }
      fetchJobs();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to retry job');
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

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" gutterBottom>
          Jobs
        </Typography>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={fetchJobs}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {loading ? (
        <LinearProgress />
      ) : (
        <>
          <Grid container spacing={2}>
            {jobs.map((job) => (
              <Grid item xs={12} md={6} lg={4} key={job.id}>
                <Card>
                  <CardContent>
                    <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                      <Typography variant="h6" component="div" noWrap>
                        {job.filename}
                      </Typography>
                      <Chip
                        label={job.status}
                        color={getStatusColor(job.status) as any}
                        size="small"
                      />
                    </Box>
                    
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Splitter: {job.splitter}
                    </Typography>
                    
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Stems: {job.stems_to_keep.join(', ')}
                    </Typography>
                    
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Created: {formatDate(job.created_at)}
                    </Typography>

                    {job.status === 'processing' && (
                      <Box mt={2}>
                        <Typography variant="body2" gutterBottom>
                          Progress: {job.progress}%
                        </Typography>
                        <LinearProgress variant="determinate" value={job.progress} />
                      </Box>
                    )}

                    {job.error_message && (
                      <Alert severity="error" sx={{ mt: 2 }}>
                        {job.error_message}
                      </Alert>
                    )}
                  </CardContent>
                  
                  <CardActions>
                    <IconButton
                      size="small"
                      onClick={() => setSelectedJob(job)}
                      title="View Details"
                    >
                      <Visibility />
                    </IconButton>
                    
                    {job.status === 'completed' && job.output_path && (
                      <IconButton
                        size="small"
                        title="Download Results"
                      >
                        <Download />
                      </IconButton>
                    )}
                    
                    {job.status === 'failed' && (
                      <IconButton
                        size="small"
                        onClick={() => retryJob(job.id)}
                        title="Retry Job"
                      >
                        <Replay />
                      </IconButton>
                    )}
                    
                    <IconButton
                      size="small"
                      onClick={() => deleteJob(job.id)}
                      title="Delete Job"
                      color="error"
                    >
                      <Delete />
                    </IconButton>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>

          {jobs.length === 0 && !loading && (
            <Box textAlign="center" py={4}>
              <Typography variant="h6" color="text.secondary">
                No jobs found
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Upload some audio files to get started!
              </Typography>
            </Box>
          )}

          {totalJobs > itemsPerPage && (
            <Box display="flex" justifyContent="center" mt={3}>
              <Pagination
                count={Math.ceil(totalJobs / itemsPerPage)}
                page={page}
                onChange={(_, newPage) => setPage(newPage)}
              />
            </Box>
          )}
        </>
      )}

      {/* Job Details Dialog */}
      <Dialog
        open={!!selectedJob}
        onClose={() => setSelectedJob(null)}
        maxWidth="md"
        fullWidth
      >
        {selectedJob && (
          <>
            <DialogTitle>
              Job Details: {selectedJob.filename}
            </DialogTitle>
            <DialogContent>
              <List>
                <ListItem>
                  <ListItemText primary="Job ID" secondary={selectedJob.id} />
                </ListItem>
                <ListItem>
                  <ListItemText primary="Status" secondary={selectedJob.status} />
                </ListItem>
                <ListItem>
                  <ListItemText primary="Splitter" secondary={selectedJob.splitter} />
                </ListItem>
                <ListItem>
                  <ListItemText primary="Stems" secondary={selectedJob.stems_to_keep.join(', ')} />
                </ListItem>
                <ListItem>
                  <ListItemText primary="Progress" secondary={`${selectedJob.progress}%`} />
                </ListItem>
                <ListItem>
                  <ListItemText primary="Created" secondary={formatDate(selectedJob.created_at)} />
                </ListItem>
                {selectedJob.started_at && (
                  <ListItem>
                    <ListItemText primary="Started" secondary={formatDate(selectedJob.started_at)} />
                  </ListItem>
                )}
                {selectedJob.completed_at && (
                  <ListItem>
                    <ListItemText primary="Completed" secondary={formatDate(selectedJob.completed_at)} />
                  </ListItem>
                )}
                {selectedJob.output_path && (
                  <ListItem>
                    <ListItemText primary="Output Path" secondary={selectedJob.output_path} />
                  </ListItem>
                )}
                {selectedJob.error_message && (
                  <ListItem>
                    <ListItemText primary="Error" secondary={selectedJob.error_message} />
                  </ListItem>
                )}
              </List>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setSelectedJob(null)}>Close</Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Box>
  );
};

export default JobsPage;
