import { useRef, useState } from "react";
import { formatBytes } from "../../utils/format";

const ACCEPTED = [".csv", ".tsv", ".txt"];
const MAX_BYTES = 100 * 1024 * 1024;

/** Client-side check, so an obviously wrong file never costs a round trip. */
function validate(file) {
  if (!file) return "No file selected.";

  const name = file.name.toLowerCase();
  if (!ACCEPTED.some((extension) => name.endsWith(extension))) {
    return "This file format isn't supported. Please upload a CSV file.";
  }
  if (file.size === 0) {
    return "That file is empty. Please upload a dataset containing data.";
  }
  if (file.size > MAX_BYTES) {
    return `That file is ${formatBytes(file.size)} — the limit is 100 MB.`;
  }
  return null;
}

function UploadBox({ onUpload, busy = false, progress = 0, serverError = null }) {
  const [file, setFile] = useState(null);
  const [localError, setLocalError] = useState(null);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);

  const error = localError || serverError;

  const choose = (candidate) => {
    const problem = validate(candidate);
    setLocalError(problem);
    setFile(problem ? null : candidate);
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setDragging(false);
    if (busy) return;
    choose(event.dataTransfer.files?.[0]);
  };

  const openPicker = () => {
    if (!busy) inputRef.current?.click();
  };

  return (
    <div>
      <div
        className={`dp-dropzone${dragging ? " is-dragging" : ""}${error ? " has-error" : ""}`}
        onDragOver={(event) => {
          event.preventDefault();
          if (!busy) setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={openPicker}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            openPicker();
          }
        }}
        role="button"
        tabIndex={0}
        aria-label="Upload a CSV file"
      >
        <div className="dp-dropzone-icon" aria-hidden="true">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
        </div>

        <div className="dp-dropzone-title">
          {dragging ? "Drop to upload" : "Drop your CSV here"}
        </div>
        <div className="dp-dropzone-hint">
          or <span style={{ color: "var(--accent-bright)" }}>browse files</span> · CSV, TSV up to 100 MB
        </div>

        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED.join(",")}
          hidden
          onChange={(event) => choose(event.target.files?.[0])}
        />
      </div>

      {file && !error && (
        <div className="dp-file-chip">
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="dp-file-chip-name">{file.name}</div>
            <div className="dp-file-chip-size">{formatBytes(file.size)}</div>
          </div>
          {!busy && (
            <button
              type="button"
              className="dp-btn dp-btn-ghost"
              onClick={() => setFile(null)}
            >
              Remove
            </button>
          )}
        </div>
      )}

      {error && (
        <p style={{ marginTop: 14, color: "var(--danger)", fontSize: 14 }} role="alert">
          {error}
        </p>
      )}

      {busy && progress > 0 && progress < 100 && (
        <div className="dp-meter" style={{ marginTop: 16 }}>
          <div className="dp-meter-head">
            <span className="dp-meter-name">Uploading</span>
            <span className="dp-meter-value">{progress}%</span>
          </div>
          <div className="dp-meter-track">
            <div className="dp-meter-fill tone-accent" style={{ width: `${progress}%` }} />
          </div>
        </div>
      )}

      <button
        type="button"
        className="dp-btn dp-btn-primary dp-btn-lg"
        style={{ width: "100%", marginTop: 18 }}
        disabled={!file || busy}
        onClick={() => file && onUpload(file)}
      >
        {busy ? "Analysing…" : "Analyse dataset"}
      </button>
    </div>
  );
}

export default UploadBox;
