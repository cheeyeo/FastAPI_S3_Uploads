import { useState } from 'react';
import './App.css';

const API_BASE_URL = 'http://127.0.0.1:8000'; // Make sure this matches your FastAPI server address

function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [message, setMessage] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      setSelectedFile(event.target.files[0]);
      setMessage('');
    } else {
      setSelectedFile(null);
    }
  };

  const uploadFile = async (endpoint: string) => {
    if (!selectedFile) {
      setMessage('Please select a file first.');
      return;
    }

    setLoading(true);
    setMessage('Uploading...');

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
      setMessage(`Upload successful! ${JSON.stringify(data, null, 2)}`);
    } catch (error: any) {
      setMessage(`Error: ${error.message}`);
    } finally {
      setLoading(false);
      setSelectedFile(null);
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
            {loading && message.includes('Uploading') ? 'Uploading to Local...' : 'Upload to Local'}
          </button>
          <button onClick={() => uploadFile('/upload/s3')} disabled={loading || !selectedFile}>
            {loading && message.includes('Uploading') ? 'Uploading to S3...' : 'Upload to S3'}
          </button>
        </div>
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
