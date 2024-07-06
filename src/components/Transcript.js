import React, { useEffect, useState } from 'react';
import io from 'socket.io-client';

function Transcript() {
  const [transcript, setTranscript] = useState('');
  const [partialTranscript, setPartialTranscript] = useState('');

  useEffect(() => {
    const socket = io('http://localhost:5000');

    socket.on('connect', () => {
      console.log('Connected to server');
    });

    socket.on('disconnect', () => {
      console.log('Disconnected from server');
    });

    socket.on('transcription', (data) => {
      console.log('Received transcript data:', data);
      if (data.type === 'FinalTranscript') {
        setTranscript(prev => prev + data.text + '\n');
        setPartialTranscript('');
      } else if (data.type === 'PartialTranscript') {
        setPartialTranscript(data.text);
      }
    });

    socket.on('error', (error) => {
      console.error('Socket error:', error);
    });

    socket.on('connection_closed', (data) => {
      console.log('Connection closed:', data);
    });

    socket.on('session_terminated', () => {
      console.log('Session terminated');
      setPartialTranscript('');
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  return (
    <div>
      <h1>Transcript</h1>
      <pre>{transcript}</pre>
      <h2>Partial Transcript</h2>
      <pre>{partialTranscript}</pre>
    </div>
  );
}

export default Transcript;
