import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  Alert,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Button,
  IconButton,
  Collapse,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  Storage as StorageIcon,
  Folder as FolderIcon,
  InsertDriveFile as FileIcon,
  Check as CheckIcon,
  Close as CloseIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Memory as MemoryIcon,
  Speed as SpeedIcon,
  DeviceThermostat as ThermalIcon,
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import TreeView from '@mui/lab/TreeView';
import TreeItem from '@mui/lab/TreeItem';
import { apiConfig } from '../config/api';

interface DirectoryInfo {
  path: string;
  exists: boolean;
  readable: boolean;
  writable: boolean;
  size: number;
  file_count?: number;
  subdirs?: string[];
  recent_files?: string[];
}

interface StorageInfo {
  input_directory?: DirectoryInfo;
  output_directory?: DirectoryInfo;
  archive_directory?: DirectoryInfo;
  logs_directory?: DirectoryInfo;
  models_directory?: DirectoryInfo;
}

interface ServiceStatus {
  name: string;
  status: string;
  container_id?: string;
  image?: string;
  created?: string;
  state?: string;
  health?: string;
  uptime?: string;
  version?: string;
  running?: boolean;
  id?: string;
}

interface SystemStats {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  gpu_available?: boolean;
  gpu_usage?: number;
  uptime: string;
  jobs_processed_today?: number;
  total_files_processed?: number;
}

interface SystemInfo {
  system: {
    platform: string;
    python_version: string;
    hostname: string;
    cpu_count: number;
  };
  pipeline_config: {
    input_dir: string;
    output_dir: string;
    archive_dir: string;
    logs_dir: string;
    file_stability_threshold: number;
    directory_stability_threshold: number;
    stems_to_keep: string[];
    processing_engine: string;
    splitter_model: string;
  };
  storage: StorageInfo;
  services: ServiceStatus[];
  stats: SystemStats;
}

const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const formatUptime = (seconds: number): string => {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  return `${days}d ${hours}h ${minutes}m`;
};

function SystemPage() {
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    system: true,
    storage: true,
    services: true,
    stats: true,
    config: false,
  });

  const { data: systemInfo, isLoading, error, refetch } = useQuery<SystemInfo>(
    'systemInfo',
    async () => {
      console.log("Fetching system data from:", apiConfig.endpoints.system);
      try {
        const response = await fetch(apiConfig.endpoints.system);
        if (!response.ok) {
          console.error("API response error:", response.status, response.statusText);
          throw new Error(`Failed to fetch system info: ${response.status} ${response.statusText}`);
        }
        const data = await response.json();
        console.log("System data received:", data);
        return data;
      } catch (err) {
        console.error("Error fetching system data:", err);
        throw err;
      }
    },
    {
      refetchInterval: 10000, // Refresh every 10 seconds
      retry: 3,
      retryDelay: 1000,
      onError: (err) => {
        console.error("React Query error handler:", err);
      }
    }
  );

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const renderDirectoryInfo = (dir: DirectoryInfo | undefined, title: string) => {
    if (!dir) {
      return (
        <Card variant="outlined" sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              {title}
            </Typography>
            <Alert severity="warning">Directory information not available</Alert>
          </CardContent>
        </Card>
      );
    }

    return (
      <Card variant="outlined" sx={{ mb: 2 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <FolderIcon sx={{ mr: 1 }} />
            <Typography variant="h6" sx={{ flexGrow: 1 }}>
              {title}
            </Typography>
            <Box>
              {dir.exists ? (
                <Chip
                  icon={<CheckIcon />}
                  label="Exists"
                  color="success"
                  size="small"
                  sx={{ mr: 1 }}
                />
              ) : (
                <Chip
                  icon={<CloseIcon />}
                  label="Missing"
                  color="error"
                  size="small"
                  sx={{ mr: 1 }}
                />
              )}
              {dir.readable && (
                <Chip label="R" color="primary" size="small" sx={{ mr: 0.5 }} />
              )}
              {dir.writable && (
                <Chip label="W" color="primary" size="small" />
              )}
            </Box>
          </Box>

                    <Typography variant="body2" color="text.secondary" gutterBottom>
            {dir.path || 'Unknown path'}
          </Typography>

          {dir.exists && (
            <>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
                <Typography variant="body2">
                  Size: {formatBytes(dir.size || 0)}
                </Typography>
                {typeof dir.file_count !== 'undefined' && (
                  <Typography variant="body2">
                    Files: {dir.file_count}
                  </Typography>
                )}
              </Box>

              {dir.recent_files && dir.recent_files.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Recent Files:
                  </Typography>
                  <List dense>
                    {dir.recent_files.slice(0, 5).map((file, index) => (
                      <ListItem key={index} disableGutters>
                        <ListItemIcon sx={{ minWidth: 30 }}>
                          <FileIcon fontSize="small" />
                        </ListItemIcon>
                        <ListItemText
                          primary={file}
                          primaryTypographyProps={{
                            variant: 'body2',
                            noWrap: true,
                          }}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}
            </>
          )}
        </CardContent>
      </Card>
    );
  };

  const renderServiceStatus = (services: ServiceStatus[] | undefined) => {
    if (!services || services.length === 0) {
      return (
        <Alert severity="info">No services information available</Alert>
      );
    }

    // Safe check for image splitting - let's debug services to console
    console.log("Services data:", services);

    return (
      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Service</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Container ID</TableCell>
              <TableCell>Health</TableCell>
              <TableCell>Details</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {services.map((service, index) => {
              // Safe image extraction to prevent errors
              let imageName = 'N/A';
              let imageTag = 'latest';
              try {
                if (service.image) {
                  const parts = service.image.split(':');
                  imageName = parts[0];
                  if (parts.length > 1) {
                    imageTag = parts[1];
                  }
                }
              } catch (err) {
                console.error(`Error processing image for service ${service.name}:`, err);
              }
              
              // Safe date formatting
              let createdDate = service.created || 'N/A';
              if (createdDate !== 'N/A') {
                try {
                  // Check if it's already formatted (Jan 01, 2023)
                  if (!createdDate.includes(',')) {
                    createdDate = new Date(createdDate).toLocaleString();
                  }
                } catch (err) {
                  console.error(`Error formatting date for service ${service.name}:`, err);
                }
              }
              
              // Container ID format - if it's id, use that, otherwise container_id
              const containerId = service.id || service.container_id || 'N/A';
              
              return (
                <TableRow key={index}>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                        {service.name || 'Unknown'}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={service.status || 'unknown'}
                      color={
                        service.status === 'running' ? 'success' : 
                        (service.running === true) ? 'success' :
                        service.status === 'stopped' ? 'error' :
                        service.status === 'error' ? 'warning' : 'default'
                      }
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
                      {containerId && containerId !== 'N/A' ? containerId.substring(0, 12) : 'N/A'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {service.health && (
                      <Chip
                        label={service.health}
                        color={
                          service.health === 'healthy' ? 'success' : 
                          service.health === 'unhealthy' ? 'error' : 
                          'warning'
                        }
                        size="small"
                      />
                    )}
                  </TableCell>
                  <TableCell>
                    <Box>
                      <Typography variant="caption" display="block" color="text.secondary">
                        Image: {service.image || 'N/A'}
                      </Typography>
                      <Typography variant="caption" display="block" color="text.secondary">
                        Created: {createdDate}
                      </Typography>
                      {service.state && service.state !== service.status && (
                        <Typography variant="caption" display="block" color="text.secondary">
                          State: {service.state}
                        </Typography>
                      )}
                      {service.uptime && (
                        <Typography variant="caption" display="block" color="text.secondary">
                          Uptime: {service.uptime}
                        </Typography>
                      )}
                      {service.version && (
                        <Typography variant="caption" display="block" color="text.secondary">
                          Version: {service.version}
                        </Typography>
                      )}
                    </Box>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Failed to load system information: {error instanceof Error ? error.message : 'Unknown error'}
        </Alert>
        <Button
          startIcon={<RefreshIcon />}
          onClick={() => refetch()}
          sx={{ mt: 2 }}
        >
          Retry
        </Button>
      </Box>
    );
  }

  if (!systemInfo) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="warning">No system information available</Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ flexGrow: 1 }}>
          System Information
        </Typography>
        <IconButton onClick={() => refetch()} size="large">
          <RefreshIcon />
        </IconButton>
      </Box>

      {/* System Overview */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            System Overview
          </Typography>
          <IconButton onClick={() => toggleSection('system')} size="small">
            {expandedSections.system ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </Box>
        <Collapse in={expandedSections.system}>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="subtitle2" color="text.secondary">
                Platform
              </Typography>
              <Typography variant="body1">
                {systemInfo?.system?.platform || 'Unknown'}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="subtitle2" color="text.secondary">
                Python Version
              </Typography>
              <Typography variant="body1">
                {systemInfo?.system?.python_version || 'Unknown'}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="subtitle2" color="text.secondary">
                Hostname
              </Typography>
              <Typography variant="body1">
                {systemInfo?.system?.hostname || 'Unknown'}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="subtitle2" color="text.secondary">
                CPU Cores
              </Typography>
              <Typography variant="body1">
                {systemInfo?.system?.cpu_count || 0}
              </Typography>
            </Grid>
          </Grid>
        </Collapse>
      </Paper>

      {/* System Stats */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            System Statistics
          </Typography>
          <IconButton onClick={() => toggleSection('stats')} size="small">
            {expandedSections.stats ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </Box>
        <Collapse in={expandedSections.stats}>
          {systemInfo?.stats ? (
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Box sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <SpeedIcon sx={{ mr: 1 }} />
                    <Typography variant="subtitle1">
                      CPU Usage: {systemInfo.stats.cpu_usage?.toFixed(1) || 0}%
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={systemInfo.stats.cpu_usage || 0}
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                </Box>
              </Grid>

              <Grid item xs={12} md={6}>
                <Box sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <MemoryIcon sx={{ mr: 1 }} />
                    <Typography variant="subtitle1">
                      Memory Usage: {systemInfo.stats.memory_usage?.toFixed(1) || 0}%
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={systemInfo.stats.memory_usage || 0}
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                  <Typography variant="caption" color="text.secondary">
                    Memory utilization
                  </Typography>
                </Box>
              </Grid>

              <Grid item xs={12} md={6}>
                <Box sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <StorageIcon sx={{ mr: 1 }} />
                    <Typography variant="subtitle1">
                      Disk Usage: {systemInfo.stats.disk_usage?.toFixed(1) || 0}%
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={systemInfo.stats.disk_usage || 0}
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                  <Typography variant="caption" color="text.secondary">
                    System disk utilization
                  </Typography>
                </Box>
              </Grid>

              <Grid item xs={12} md={6}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">
                      Jobs Processed Today
                    </Typography>
                    <Typography variant="h6">
                      {systemInfo.stats.jobs_processed_today || 0}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">
                      Total Files Processed
                    </Typography>
                    <Typography variant="h6">
                      {systemInfo.stats.total_files_processed || 0}
                    </Typography>
                  </Box>
                </Box>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">
                      Uptime
                    </Typography>
                    <Typography variant="h6">
                      {systemInfo.stats.uptime || "Unknown"}
                    </Typography>
                  </Box>
                </Box>
              </Grid>
              
              {systemInfo.stats.gpu_available && (
                <Grid item xs={12} md={6}>
                  <Box sx={{ mb: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <ThermalIcon sx={{ mr: 1 }} />
                      <Typography variant="subtitle1">
                        GPU Usage: {systemInfo.stats.gpu_usage?.toFixed(1) || 0}%
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={systemInfo.stats.gpu_usage || 0}
                      sx={{ height: 8, borderRadius: 4 }}
                    />
                    <Typography variant="caption" color="text.secondary">
                      GPU acceleration available
                    </Typography>
                  </Box>
                </Grid>
              )}
            </Grid>
          ) : (
            <Alert severity="info">System statistics not available</Alert>
          )}
        </Collapse>
      </Paper>

      {/* Storage Information */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Storage Directories
          </Typography>
          <IconButton onClick={() => toggleSection('storage')} size="small">
            {expandedSections.storage ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </Box>
        <Collapse in={expandedSections.storage}>
          {systemInfo?.storage ? (
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                {renderDirectoryInfo(systemInfo.storage.input_directory, 'Input Directory')}
              </Grid>
              <Grid item xs={12} md={6}>
                {renderDirectoryInfo(systemInfo.storage.output_directory, 'Output Directory')}
              </Grid>
              <Grid item xs={12} md={6}>
                {renderDirectoryInfo(systemInfo.storage.archive_directory, 'Archive Directory')}
              </Grid>
              <Grid item xs={12} md={6}>
                {renderDirectoryInfo(systemInfo.storage.logs_directory, 'Logs Directory')}
              </Grid>
              {systemInfo.storage.models_directory && (
                <Grid item xs={12} md={6}>
                  {renderDirectoryInfo(systemInfo.storage.models_directory, 'Models Directory')}
                </Grid>
              )}
            </Grid>
          ) : (
            <Alert severity="info">Storage information not available</Alert>
          )}
        </Collapse>
      </Paper>

      {/* Services Status */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Services Status
          </Typography>
          <IconButton onClick={() => toggleSection('services')} size="small">
            {expandedSections.services ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </Box>
        <Collapse in={expandedSections.services}>
          {renderServiceStatus(systemInfo?.services)}
        </Collapse>
      </Paper>

      {/* Pipeline Configuration */}
      <Paper sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Pipeline Configuration
          </Typography>
          <IconButton onClick={() => toggleSection('config')} size="small">
            {expandedSections.config ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </Box>
        <Collapse in={expandedSections.config}>
          {systemInfo?.pipeline_config ? (
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={4}>
                <Card variant="outlined" sx={{ height: '100%' }}>
                  <CardContent>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      Processing Engine
                    </Typography>
                    <Typography variant="h6">
                      {systemInfo.pipeline_config.processing_engine || 'Not configured'}
                    </Typography>
                    <Box sx={{ mt: 2 }}>
                      <Chip 
                        icon={<SpeedIcon />}
                        label={`Model: ${systemInfo.pipeline_config.splitter_model || 'Default'}`} 
                        color="primary" 
                        variant="outlined" 
                      />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} sm={6} md={4}>
                <Card variant="outlined" sx={{ height: '100%' }}>
                  <CardContent>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      Stems to Keep
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                      {systemInfo.pipeline_config.stems_to_keep && systemInfo.pipeline_config.stems_to_keep.length > 0 ? (
                        systemInfo.pipeline_config.stems_to_keep.map((stem, idx) => (
                          <Chip 
                            key={idx} 
                            label={stem} 
                            color="success" 
                            size="small" 
                            icon={<CheckIcon />} 
                          />
                        ))
                      ) : (
                        <Typography variant="body2" color="text.secondary">No stems configured</Typography>
                      )}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} sm={6} md={4}>
                <Card variant="outlined" sx={{ height: '100%' }}>
                  <CardContent>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      File Processing Thresholds
                    </Typography>
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="body2" display="flex" justifyContent="space-between">
                        <span>File Stability:</span> 
                        <span><b>{systemInfo.pipeline_config.file_stability_threshold || 0}</b> seconds</span>
                      </Typography>
                      <Typography variant="body2" display="flex" justifyContent="space-between">
                        <span>Directory Stability:</span> 
                        <span><b>{systemInfo.pipeline_config.directory_stability_threshold || 0}</b> seconds</span>
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          ) : (
            <Alert severity="info">Pipeline configuration not available</Alert>
          )}
        </Collapse>
      </Paper>
    </Box>
  );
}

export default SystemPage;