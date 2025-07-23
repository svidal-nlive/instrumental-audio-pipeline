import React, { useState, useCallback } from 'react';
import { apiConfig } from '../config/api';
import {
  Typography,
  Box,
  Paper,
  Button,
  LinearProgress,
  Alert,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormGroup,
  FormControlLabel,
  Checkbox,
  Card,
  CardContent,
  Grid,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton
} from '@mui/material';
import {
  CloudUpload,
  AudioFile,
  Delete,
  CheckCircle,
  Error as ErrorIcon
} from '@mui/icons-material';

interface UploadFile {
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'completed' | 'error';
  error?: string;
  id: string;
}

const UploadPage: React.FC = () => {
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const [splitter, setSplitter] = useState('DEMUCS');
  const [stemsToKeep, setStemsToKeep] = useState(['drums', 'bass', 'other']);
  const [uploading, setUploading] = useState(false);

  const generateId = () => Math.random().toString(36).substr(2, 9);

  const isValidAudioFile = (file: File) => {
    const validTypes = ['audio/mpeg', 'audio/wav', 'audio/flac', 'audio/ogg', 'audio/mp4'];
    return validTypes.includes(file.type) || file.name.match(/\.(mp3|wav|flac|ogg|m4a)$/i);
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    
    const droppedFiles = Array.from(e.dataTransfer.files);
    const audioFiles = droppedFiles.filter(isValidAudioFile);
    
    const newFiles: UploadFile[] = audioFiles.map(file => ({
      file,
      progress: 0,
      status: 'pending',
      id: generateId()
    }));
    
    setFiles(prev => [...prev, ...newFiles]);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setDragOver(false);
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files);
      const audioFiles = selectedFiles.filter(isValidAudioFile);
      
      const newFiles: UploadFile[] = audioFiles.map(file => ({
        file,
        progress: 0,
        status: 'pending',
        id: generateId()
      }));
      
      setFiles(prev => [...prev, ...newFiles]);
    }
  };

  const removeFile = (id: string) => {
    setFiles(prev => prev.filter(f => f.id !== id));
  };

  const uploadFile = async (uploadFile: UploadFile) => {
    const formData = new FormData();
    formData.append('file', uploadFile.file);
    formData.append('splitter', splitter);
    formData.append('stems_to_keep', JSON.stringify(stemsToKeep));

    try {
      setFiles(prev => prev.map(f => 
        f.id === uploadFile.id 
          ? { ...f, status: 'uploading', progress: 0 }
          : f
      ));

      const response = await fetch(`${apiConfig.endpoints.upload}single/`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      const result = await response.json();
      
      setFiles(prev => prev.map(f => 
        f.id === uploadFile.id 
          ? { ...f, status: 'completed', progress: 100 }
          : f
      ));

      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Upload failed';
      setFiles(prev => prev.map(f => 
        f.id === uploadFile.id 
          ? { ...f, status: 'error', error: errorMessage }
          : f
      ));
      throw error;
    }
  };

  const handleUploadAll = async () => {
    if (files.length === 0) return;
    
    setUploading(true);
    
    try {
      const pendingFiles = files.filter(f => f.status === 'pending');
      
      for (const file of pendingFiles) {
        await uploadFile(file);
      }
    } catch (error) {
      console.error('Upload error:', error);
    } finally {
      setUploading(false);
    }
  };

  const handleStemToggle = (stem: string) => {
    setStemsToKeep(prev => 
      prev.includes(stem) 
        ? prev.filter(s => s !== stem)
        : [...prev, stem]
    );
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle color="success" />;
      case 'error':
        return <ErrorIcon color="error" />;
      case 'uploading':
        return <CloudUpload color="primary" />;
      default:
        return <AudioFile />;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Upload Files
      </Typography>
      
      <Grid container spacing={3}>
        {/* Upload Area */}
        <Grid item xs={12} md={8}>
          <Paper
            sx={{
              p: 4,
              border: `2px dashed ${dragOver ? 'primary.main' : 'grey.300'}`,
              backgroundColor: dragOver ? 'action.hover' : 'background.paper',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              '&:hover': {
                borderColor: 'primary.main',
                backgroundColor: 'action.hover'
              }
            }}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
          >
            <Box textAlign="center">
              <CloudUpload sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                Drag & drop audio files here
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                or click to select files
              </Typography>
              <input
                type="file"
                multiple
                accept="audio/*,.mp3,.wav,.flac,.ogg,.m4a"
                onChange={handleFileSelect}
                style={{ display: 'none' }}
                id="file-input"
              />
              <label htmlFor="file-input">
                <Button variant="contained" component="span">
                  Select Files
                </Button>
              </label>
              <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                Supported formats: MP3, WAV, FLAC, OGG, M4A
              </Typography>
            </Box>
          </Paper>

          {/* File List */}
          {files.length > 0 && (
            <Card sx={{ mt: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Selected Files ({files.length})
                </Typography>
                <List>
                  {files.map((uploadFile) => (
                    <ListItem key={uploadFile.id} divider>
                      <ListItemIcon>
                        {getStatusIcon(uploadFile.status)}
                      </ListItemIcon>
                      <ListItemText
                        primary={uploadFile.file.name}
                        secondary={
                          <Box>
                            <Typography variant="caption">
                              {formatFileSize(uploadFile.file.size)}
                              {uploadFile.status === 'error' && uploadFile.error && (
                                <> • <span style={{ color: 'red' }}>{uploadFile.error}</span></>
                              )}
                            </Typography>
                            {uploadFile.status === 'uploading' && (
                              <LinearProgress 
                                variant="indeterminate" 
                                sx={{ mt: 1 }} 
                              />
                            )}
                          </Box>
                        }
                      />
                      <IconButton 
                        onClick={() => removeFile(uploadFile.id)}
                        disabled={uploadFile.status === 'uploading'}
                      >
                        <Delete />
                      </IconButton>
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          )}
        </Grid>

        {/* Settings Panel */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Processing Settings
              </Typography>
              
              <FormControl fullWidth sx={{ mb: 3 }}>
                <InputLabel>AI Model</InputLabel>
                <Select
                  value={splitter}
                  label="AI Model"
                  onChange={(e) => setSplitter(e.target.value)}
                >
                  <MenuItem value="DEMUCS">Demucs (High Quality)</MenuItem>
                  <MenuItem value="SPLEETER">Spleeter (Fast)</MenuItem>
                </Select>
              </FormControl>

              <Typography variant="subtitle2" gutterBottom>
                Stems to Keep:
              </Typography>
              <FormGroup sx={{ mb: 3 }}>
                {['vocals', 'drums', 'bass', 'other'].map((stem) => (
                  <FormControlLabel
                    key={stem}
                    control={
                      <Checkbox
                        checked={stemsToKeep.includes(stem)}
                        onChange={() => handleStemToggle(stem)}
                      />
                    }
                    label={stem.charAt(0).toUpperCase() + stem.slice(1)}
                  />
                ))}
              </FormGroup>

              <Button
                variant="contained"
                fullWidth
                size="large"
                onClick={handleUploadAll}
                disabled={files.length === 0 || uploading || files.every(f => f.status !== 'pending')}
                startIcon={<CloudUpload />}
              >
                {uploading ? 'Uploading...' : `Upload ${files.filter(f => f.status === 'pending').length} Files`}
              </Button>

              {files.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="caption" color="text.secondary">
                    Status: {files.filter(f => f.status === 'completed').length} completed, 
                    {files.filter(f => f.status === 'error').length} failed,
                    {files.filter(f => f.status === 'pending').length} pending
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>

          <Alert severity="info" sx={{ mt: 2 }}>
            <Typography variant="body2">
              Files will be processed automatically after upload. 
              Check the Jobs page to monitor progress.
            </Typography>
          </Alert>
        </Grid>
      </Grid>
    </Box>
  );
};

export default UploadPage;
