import { useState } from 'react';
import './App.css';
import UploadList, { type Upload } from './UploadList';
import './UploadsLayout.css';

const API_BASE_URL = 'http://localhost:8000';


function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [message, setMessage] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [uploads, setUploads] = useState<Upload[]>([]);



  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      const file = event.target.files[0];
      setSelectedFile(file);
      setMessage('');
    } else {
      setSelectedFile(null);
    }
  };

  const uploadFile = async (fileToUpload: File, endpoint: string) => {
    setLoading(true);
    setMessage('Initiating upload...');

    const formData = new FormData();
    formData.append('file', fileToUpload);

    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload initiation failed');
      }

      const data = await response.json();
      console.log(data)

      // Add the new upload to the list
      setUploads((prevUploads) => [
        ...prevUploads,
        {_id: data._id, filename: fileToUpload.name, progress: 0 },
      ]);

      setMessage(`Upload started for ${fileToUpload.name}`);
    } catch (error: any) {
      setMessage(`Error: ${error.message}`);
    } finally {
      setLoading(false);
      setSelectedFile(null); // Clear selected file after initiation
      setSelectedFile(null);
    }
  };

  const handleUploadClick = () => {
    if (selectedFile) {
      uploadFile(selectedFile, '/upload/background');
    }
  };

  return (
    <div className="App">
      <h1>FastAPI File Upload</h1>
      <div className="uploads-container">
        <div className="upload-panel">
          <h2>Upload New File</h2>
          <input type="file" onChange={handleFileChange} disabled={loading} />
          {selectedFile && <p>Selected file: {selectedFile.name}</p>}
          <button onClick={handleUploadClick} disabled={loading || !selectedFile}>
            {loading ? 'Initiating Upload...' : 'Start Background Upload'}
          </button>
          {message && (
            <pre className={`message ${message.startsWith('Error') ? 'error' : 'success'}`}>
              {message}
            </pre>
          )}
        </div>
        <UploadList uploads={uploads} />
      </div>
      <p className="read-the-docs">
        Ensure your FastAPI backend is running on {API_BASE_URL}
      </p>
    </div>
  );
}

export default App;
