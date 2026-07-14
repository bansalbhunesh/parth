"use client";

import { useCallback, useRef, useState } from "react";

interface DropZoneProps {
  label: string;
  file: File | null;
  onFile: (file: File) => void;
  accept: string;
  hint?: string;
  disabled: boolean;
}

export default function DropZone({ label, file, onFile, accept, hint, disabled }: DropZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  const handleDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      setDragOver(false);
      const droppedFile = event.dataTransfer.files[0];
      if (droppedFile) onFile(droppedFile);
    },
    [onFile],
  );

  return (
    <div
      className={`analyze-dropzone ${dragOver ? "drag-over" : ""} ${file ? "has-file" : ""}`}
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-label={`${label}: drop a PDF, MD or TXT file here, or activate to browse`}
      aria-disabled={disabled}
      onDragOver={(event) => { event.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
      onClick={() => !disabled && inputRef.current?.click()}
      onKeyDown={(event) => {
        if (!disabled && (event.key === "Enter" || event.key === " ")) {
          event.preventDefault();
          inputRef.current?.click();
        }
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="dropzone-input"
        aria-label={`Choose ${label.toLowerCase()}`}
        onChange={(event) => {
          const selectedFile = event.target.files?.[0];
          if (selectedFile) onFile(selectedFile);
        }}
        disabled={disabled}
      />
      {file ? (
        <div className="dropzone-file">
          <div className="dropzone-file-icon" aria-hidden="true">DOC</div>
          <div className="dropzone-file-info">
            <div className="dropzone-file-name">{file.name}</div>
            <div className="dropzone-file-size">{(file.size / 1024).toFixed(1)} KB</div>
          </div>
        </div>
      ) : (
        <div className="dropzone-empty">
          <div className="dropzone-icon" aria-hidden="true">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
          </div>
          <div className="dropzone-label">{label}</div>
          <div className="dropzone-hint">{hint ?? "Drop PDF/MD/TXT here or click to browse"}</div>
        </div>
      )}
    </div>
  );
}
