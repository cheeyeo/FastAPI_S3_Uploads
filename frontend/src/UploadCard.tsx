import { useState, useEffect, useRef } from 'react';
import ProgressBar from "./ProgressBar";

const WS_URL = 'ws://localhost:8000/ws';

export type UploadCardProps = {
  uploadId: string;
  filename: string;
  initialProgress: number;
};

const UploadCard = ({ uploadId, filename, initialProgress }: UploadCardProps) => {
  const [progress, setProgress] = useState<number>(initialProgress);
  const ws = useRef<WebSocket | null>(null);
  const [message, setMessage] = useState<string>('');

  useEffect(() => {
    ws.current = new WebSocket(WS_URL);

    if (!ws.current || ws.current.readyState === WebSocket.CLOSED) {
      const ws2 = new WebSocket('ws://localhost:8001')
      ws.current = ws2
    }

    ws.current.onopen = () => {
      console.log(`WebSocket for ${filename} connected`);
      // Optionally send a message to subscribe to updates for this uploadId
      // ws.current?.send(JSON.stringify({ subscribe_to_upload: uploadId }));
    };

    ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        // if error exists close WS and show error
        if (data.event === 'update' && data.document_id === uploadId && data.after.status === 'error') {
          console.log(data.after.exception);
          setMessage(data.after.exception);
          ws.current?.close()
        }

        if (data.event === 'update' && data.document_id === uploadId && typeof data.after.percentage === 'number') {
          setProgress(data.after.percentage);
        }

        if (data.after.percentage === 100) {
          // close websocket after completion
          setMessage(data.after.s3_key + '\n' + data.after.s3_url)
          ws.current?.close()
        }

      } catch (err) {
        console.error("Error parsing websocket message for uploadId", uploadId, err);
      }

    };

    ws.current.onerror = (error) => {
      console.error(`WebSocket error for ${filename}:`, error);
    };

    ws.current.onclose = () => {
      console.log(`WebSocket for ${filename} closed`);
    };

    return () => {
      if (ws.current && ws.current.readyState === WebSocket.OPEN) {
        ws.current.close()
      }
    };
  }, [uploadId, filename]);

  return (
    <div className="upload-card">
      <div className="upload-card-filename">{filename}</div>
      <ProgressBar 
        progress={progress} 
        progressText={progress > 0 ? `${Math.round(progress)}%` : 'Initializing...'} 
      />
      <div>
        <pre>
          {message}
        </pre>
      </div>
    </div>
  );
};

export default UploadCard;
