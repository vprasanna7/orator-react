import React, { useState } from 'react';
import { Button, Container, Typography, Box, Input } from '@mui/material';
import Transcript from './Transcript';

const Home = () => {
  const [file, setFile] = useState(null);
  const [transcriptId, setTranscriptId] = useState(null);
  const [transcript, setTranscript] = useState('');

  const startTranscription = async () => {
    console.log('Starting transcription');
    try {
      const response = await fetch('http://localhost:5000/start', { 
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to start transcription');
      }
      console.log('Transcription started');
    } catch (error) {
      console.error('Failed to start transcription', error);
    }
  };

  const stopTranscription = async () => {
    console.log('Stopping transcription');
    try {
      const response = await fetch('http://localhost:5000/stop', { method: 'POST' });
      if (!response.ok) {
        throw new Error('Failed to stop transcription');
      }
      console.log('Transcription stopped');
    } catch (error) {
      console.error('Failed to stop transcription', error);
    }
  };

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  const uploadFile = async () => {
    if (!file) {
      console.error('No file selected');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:5000/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('File upload failed');
      }

      const data = await response.json();
      setTranscriptId(data.transcript_id);
      console.log('File uploaded, transcript ID:', data.transcript_id);
    } catch (error) {
      console.error('Error uploading file:', error);
    }
  };

  const getTranscript = async () => {
    if (!transcriptId) {
      console.error('No transcript ID');
      return;
    }

    try {
      const response = await fetch(`http://localhost:5000/transcript/${transcriptId}`);
      const data = await response.json();

      if (response.status === 200) {
        setTranscript(data.transcript);
      } else if (response.status === 202) {
        console.log('Transcription in progress:', data.status);
      } else {
        throw new Error('Failed to get transcript');
      }
    } catch (error) {
      console.error('Error getting transcript:', error);
    }
  };

  return (
    <Container>
      <Typography variant="h4">Live Transcription</Typography>
      <Button variant="contained" color="primary" onClick={startTranscription}>Start Live</Button>
      <Button variant="contained" color="secondary" onClick={stopTranscription}>Stop Live</Button>
      
      <Box mt={2}>
        <Input type="file" onChange={handleFileChange} />
        <Button variant="contained" color="primary" onClick={uploadFile}>Upload File</Button>
      </Box>
      
      {transcriptId && (
        <Box mt={2}>
          <Button variant="contained" color="primary" onClick={getTranscript}>Get Transcript</Button>
        </Box>
      )}
      
      {transcript && (
        <Box mt={2}>
          <Typography variant="h6">File Transcript:</Typography>
          <pre>{transcript}</pre>
        </Box>
      )}
      
      <Box mt={2}>
        <Transcript />
      </Box>
    </Container>
  );
};

export default Home;
