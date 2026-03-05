import { useState, useEffect, useRef } from 'react';
import './App.css';
import ProgressBar from "./ProgressBar";

const API_BASE_URL = 'http://localhost:8000';
const WS_URL = 'ws://localhost:8000/ws';

function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [message, setMessage] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [progress, setProgress] = useState<number>(0);
  
  // Refs to allow websocket listener to access current values without re-running useEffect
  const currentUploadId = useRef<string | null>(null);
  const selectedFileRef = useRef<File | null>(null);

  useEffect(() => {
    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      console.log("CONNECTED TO WEBSOCKET");
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        // console.log(data);
        
        // 1. If we haven't identified our upload_id yet, look for the 'insert' event
        // matching the filename and size of the file we just started uploading.
        if (
          !currentUploadId.current && 
          data.event === 'insert' && 
          data.after && 
          selectedFileRef.current
        ) {
          if (
            data.after.filename === selectedFileRef.current.name && 
            data.after.size === selectedFileRef.current.size
          ) {
            currentUploadId.current = data.document_id;
            console.log("Identified upload_id from websocket:", data.document_id);
          }
        }

        // 2. Update progress if the event is an 'update' for our current upload.
        if (
          data.event === 'update' && 
          data.document_id === currentUploadId.current &&
          data.after && 
          typeof data.after.percentage === 'number'
        ) {
          setProgress(data.after.percentage);
        }
      } catch (err) {
        console.error("Error parsing websocket message:", err);
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    ws.onclose = () => {
      console.log("WEBSOCKET CLOSED");
    };

    return () => {
      ws.close();
    };
  }, []);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      const file = event.target.files[0];
      setSelectedFile(file);
      selectedFileRef.current = file;
      setMessage('');
      setProgress(0);
      currentUploadId.current = null;
    } else {
      setSelectedFile(null);
      selectedFileRef.current = null;
    }
  };

  const uploadFile = async (endpoint: string) => {
    if (!selectedFile) {
      setMessage('Please select a file first.');
      return;
    }

    setLoading(true);
    setMessage('Uploading...');
    setProgress(0);
    currentUploadId.current = null;
    // selectedFileRef.current is already set by handleFileChange

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }

      const data = await response.json();
      
      // If we got the upload_id here and didn't catch it via WS yet, set it now
      if (data.upload_id && !currentUploadId.current) {
        currentUploadId.current = data.upload_id;
      }

      // setMessage(`Upload successful!`);
      setMessage(`Upload successful! ${JSON.stringify(data, null, 2)}`);
      setProgress(100);
    } catch (error: any) {
      setMessage(`Error: ${error.message}`);
      setProgress(0);
    } finally {
      setLoading(false);
      // Don't null out selectedFile immediately if we want to show it, 
      // but the original code did it. I'll keep it for consistency or slightly change it.
      setSelectedFile(null);
      selectedFileRef.current = null;
    }
  };

  return (
    <div className="App">
      <h1>FastAPI File Upload</h1>
      <div className="card">
        <input type="file" onChange={handleFileChange} disabled={loading} />
        {selectedFile && <p>Selected file: {selectedFile.name}</p>}
        
        <div className="buttons">
          <button onClick={() => uploadFile('/upload/local')} disabled={loading || !selectedFile}>
            {loading && !currentUploadId.current ? 'Uploading to Local...' : 'Upload to Local'}
          </button>
          <button onClick={() => uploadFile('/upload/s3')} disabled={loading || !selectedFile}>
            {loading && (currentUploadId.current || progress > 0) ? 'Uploading to S3...' : 'Upload to S3'}
          </button>
        </div>

        {(loading || (progress > 0 && progress < 100)) && (
          <ProgressBar 
            progress={progress} 
            progressText={progress > 0 ? `${Math.round(progress)}%` : 'Initializing...'} 
          />
        )}

        {message && (
          <pre className={`message ${message.startsWith('Error') ? 'error' : 'success'}`}>
            {message}
          </pre>
        )}
      </div>
      <p className="read-the-docs">
        Ensure your FastAPI backend is running on {API_BASE_URL}
      </p>
    </div>
  );
}

export default App;
