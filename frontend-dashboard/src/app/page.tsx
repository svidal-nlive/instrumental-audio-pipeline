"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { api } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  const [jobs, setJobs] = useState<string[]>([]);
  const [musicFiles, setMusicFiles] = useState<string[]>([]);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);

  // Fetch jobs from API
  const fetchJobs = async () => {
    try {
      const response = await fetch(`${API_BASE}/jobs/`);
      const data = await response.json();
      setJobs(data.jobs || []);
    } catch (error) {
      console.error("Failed to fetch jobs:", error);
    }
  };

  // Fetch music library
  const fetchMusicLibrary = async () => {
    try {
      const response = await fetch(`${API_BASE}/music-library/`);
      const data = await response.json();
      setMusicFiles(data.files || []);
    } catch (error) {
      console.error("Failed to fetch music library:", error);
    }
  };

  // Upload files
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    setIsUploading(true);
    setUploadProgress(0);

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append("files", files[i]);
    }

    try {
      const response = await fetch(`${API_BASE}/upload/`, {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        console.log("Upload successful:", result);
        setUploadProgress(100);
        // Refresh jobs after upload
        setTimeout(() => {
          fetchJobs();
          setIsUploading(false);
          setUploadProgress(0);
        }, 1000);
      } else {
        console.error("Upload failed");
        setIsUploading(false);
      }
    } catch (error) {
      console.error("Upload error:", error);
      setIsUploading(false);
    }
  };

  // Update settings
  const updateSettings = async (setting: string, value: string) => {
    try {
      const formData = new FormData();
      formData.append("setting", setting);
      formData.append("value", value);

      const response = await fetch(`${API_BASE}/settings/`, {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        console.log("Settings updated:", result);
      }
    } catch (error) {
      console.error("Failed to update settings:", error);
    }
  };

  // Play audio file
  const playAudio = (filePath: string) => {
    const audio = new Audio(`${API_BASE}/music-library/play/${encodeURIComponent(filePath)}`);
    audio.play().catch(error => console.error("Audio playback failed:", error));
  };

  useEffect(() => {
    fetchJobs();
    fetchMusicLibrary();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-900 mb-8">Instrumental Maker Dashboard</h1>
        
        <Tabs defaultValue="upload" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="upload">Upload</TabsTrigger>
            <TabsTrigger value="jobs">Jobs</TabsTrigger>
            <TabsTrigger value="library">Music Library</TabsTrigger>
            <TabsTrigger value="settings">Settings</TabsTrigger>
          </TabsList>

          {/* Upload Tab */}
          <TabsContent value="upload">
            <Card>
              <CardHeader>
                <CardTitle>Upload Audio Files</CardTitle>
                <CardDescription>Upload single or multiple audio files for processing</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="file-upload">Select Audio Files</Label>
                  <Input
                    id="file-upload"
                    type="file"
                    multiple
                    accept=".mp3,.wav,.flac"
                    onChange={handleFileUpload}
                    disabled={isUploading}
                  />
                </div>
                {isUploading && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm text-gray-600">
                      <span>Uploading...</span>
                      <span>{uploadProgress}%</span>
                    </div>
                    <Progress value={uploadProgress} className="w-full" />
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Jobs Tab */}
          <TabsContent value="jobs">
            <Card>
              <CardHeader>
                <CardTitle>Processing Jobs</CardTitle>
                <CardDescription>View currently running and completed jobs</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {jobs.length === 0 ? (
                    <p className="text-gray-500">No jobs currently running</p>
                  ) : (
                    jobs.map((job, index) => (
                      <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                        <span>{job}</span>
                        <Badge variant="outline">Running</Badge>
                      </div>
                    ))
                  )}
                </div>
                <Button onClick={fetchJobs} className="mt-4">
                  Refresh Jobs
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Music Library Tab */}
          <TabsContent value="library">
            <Card>
              <CardHeader>
                <CardTitle>Music Library</CardTitle>
                <CardDescription>Browse and play your processed audio files</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {musicFiles.length === 0 ? (
                    <p className="text-gray-500">No music files found</p>
                  ) : (
                    musicFiles.map((file, index) => (
                      <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                        <div className="flex-1">
                          <p className="font-medium">{file.split("/").pop()}</p>
                          <p className="text-sm text-gray-500">{file}</p>
                        </div>
                        <Button
                          onClick={() => playAudio(file)}
                          variant="outline"
                          size="sm"
                        >
                          Play
                        </Button>
                      </div>
                    ))
                  )}
                </div>
                <Button onClick={fetchMusicLibrary} className="mt-4">
                  Refresh Library
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings">
            <Card>
              <CardHeader>
                <CardTitle>Pipeline Settings</CardTitle>
                <CardDescription>Configure audio processing settings</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="splitter">Splitter Engine</Label>
                  <select
                    id="splitter"
                    className="w-full p-2 border rounded-md"
                    onChange={(e) => updateSettings("splitter", e.target.value)}
                  >
                    <option value="spleeter">Spleeter</option>
                    <option value="demucs">Demucs</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="model">Model</Label>
                  <select
                    id="model"
                    className="w-full p-2 border rounded-md"
                    onChange={(e) => updateSettings("model", e.target.value)}
                  >
                    <option value="4stems">4stems</option>
                    <option value="5stems">5stems</option>
                    <option value="htdemucs">htdemucs</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="stems">Stems to Keep</Label>
                  <Input
                    id="stems"
                    placeholder="drums,bass,other"
                    onChange={(e) => updateSettings("stems_to_keep", e.target.value)}
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
