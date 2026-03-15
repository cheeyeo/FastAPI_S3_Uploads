import UploadCard from './UploadCard';

export type Upload = {
  _id: string;
  filename: string;
  progress: number;
};

export type UploadListProps = {
  uploads: Upload[];
};

const UploadList = ({ uploads }: UploadListProps) => {
  return (
    <div className="active-uploads-panel">
      <h2>Active Uploads</h2>
      {uploads.length === 0 ? (
        <p>No active uploads.</p>
      ) : (
        <div>
          {uploads.map((upload) => (
            <UploadCard
              key={'unique'+upload._id}
              uploadId={upload._id}
              filename={upload.filename}
              initialProgress={upload.progress}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default UploadList;
