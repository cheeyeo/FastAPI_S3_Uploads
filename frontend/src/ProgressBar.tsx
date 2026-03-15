import "./ProgressBar.css";

export type ProgressBarProps = {
  progress: number;
  progressText?: string;
};

const ProgressBar = ({ progress, progressText = "" }: ProgressBarProps) => {
  // Make sure our value stays between 0 and 100.
  const _progress = Math.min(Math.max(0, progress), 100);
  return (
    <div className="progress-container">
      <div className="progress-bar-background">
        <div
          className="progress-bar-fill"
          style={{ width: `${_progress}%` }}
        ></div>
      </div>
      {progressText && <span className="progress-text">{progressText}</span>}
    </div>
  );
};

export default ProgressBar;
