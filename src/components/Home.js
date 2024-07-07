import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';
import { Container, Typography, Button, Box } from '@mui/material';
import Transcript from './Transcript';

const Home = () => {
  const [socket, setSocket] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('Disconnected');

  useEffect(() => {
    const newSocket = io('http://localhost:5000', {
      transports: ['websocket'],
    });

    newSocket.on('connect', () => {
      console.log('Connected to server');
      setConnectionStatus('Connected');
    });

    newSocket.on('disconnect', () => {
      console.log('Disconnected from server');
      setConnectionStatus('Disconnected');
    });

    newSocket.on('live_transcription', (data) => {
      console.log('Received live transcription in Home:', data);
    });

    // Add this line to log all events
    newSocket.onAny((event, ...args) => {
      console.log(`Received event "${event}" in Home:`, args);
    });

    setSocket(newSocket);
    console.log('Socket object created:', newSocket);

    return () => newSocket.close();
  }, []);

  const startTranscription = () => {
    if (socket) {
      console.log('Starting transcription');
      socket.emit('start_transcription', (response) => {
        console.log('Start transcription response:', response);
      });
    }
  };

  const stopTranscription = () => {
    if (socket) {
      console.log('Stopping transcription');
      socket.emit('stop_transcription', (response) => {
        console.log('Stop transcription response:', response);
      });
    }
  };

  const testSocket = () => {
    if (socket) {
      console.log('Testing socket');
      socket.emit('test_socket', (response) => {
        console.log('Test socket response:', response);
      });
    }
  };

  const testEmit = () => {
    console.log('Testing event emission');
    fetch('http://localhost:5000/test_emit', {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then(response => response.json())
      .then(data => console.log('Test emit response:', data))
      .catch(error => console.error('Error:', error));
  };

  return (
    <Container>
      <Typography variant="h4">Live Transcription</Typography>
      <Typography>Connection Status: {connectionStatus}</Typography>
      <Button variant="contained" color="primary" onClick={startTranscription}>Start Live</Button>
      <Button variant="contained" color="secondary" onClick={stopTranscription}>Stop Live</Button>
      <Button variant="contained" color="info" onClick={testSocket}>Test Socket</Button>
      <Button variant="contained" color="warning" onClick={testEmit}>Test Emit</Button>
      <Box mt={2}>
        {socket ? <Transcript socket={socket} /> : <Typography>Connecting...</Typography>}
      </Box>
    </Container>
  );
};

export default Home;