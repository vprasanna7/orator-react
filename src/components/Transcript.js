import React, { useEffect, useState } from 'react';

function Transcript({ socket }) {
  const [transcript, setTranscript] = useState('');
  const [partialTranscript, setPartialTranscript] = useState('');

  useEffect(() => {
    console.log('Transcript component mounted');
    console.log('Socket prop:', socket);

    if (!socket) return;

    const handleTranscription = (data) => {
      console.log('Received live transcript data in Transcript component:', data);
      if (data.type === 'FinalTranscript') {
        setTranscript(prev => {
          const newTranscript = prev + data.text + '\n';
          console.log('Updated final transcript:', newTranscript);
          return newTranscript;
        });
        setPartialTranscript('');
      } else if (data.type === 'PartialTranscript' || data.type === 'TestTranscript') {
        console.log('Updating partial transcript:', data.text);
        setPartialTranscript(data.text);
      }
    };

    socket.on('live_transcription', handleTranscription);
    console.log('Subscribed to live_transcription events');

    // Add this line to log all events
    socket.onAny((event, ...args) => {
      console.log(`Received event "${event}" in Transcript:`, args);
    });

    return () => {
      socket.off('live_transcription', handleTranscription);
      console.log('Unsubscribed from live_transcription events');
    };
  }, [socket]);

  return (
    <div>
      <h2>Transcript</h2>
      <pre style={{whiteSpace: 'pre-wrap', wordWrap: 'break-word'}}>{transcript || "No transcript yet."}</pre>
      <h3>Partial Transcript</h3>
      <pre style={{whiteSpace: 'pre-wrap', wordWrap: 'break-word'}}>{partialTranscript || "No partial transcript yet."}</pre>
    </div>
  );
}

export default Transcript;