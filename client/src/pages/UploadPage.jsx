

import { useState, useRef } from "react";
import { auth } from "../firebase/config";
import { useNavigate } from "react-router-dom";
import "./UploadPage.css";

function UploadPage() {
  
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [urlInput, setUrlInput] = useState("");
  const [title, setTitle] = useState("");
  const [tags, setTags] = useState("");
  const [eventDate, setEventDate] = useState("");
  const [organization, setOrganization] = useState("");

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [mode, setMode] = useState("file");

  const fileInputRef = useRef();

  const handleDrop = (e) => {
    e.preventDefault();
    const dropped = e.dataTransfer.files[0];
    if (dropped) setFile(dropped);
  };

  const handleDragOver = (e) => e.preventDefault();

  const handleFileSelect = (e) => {
    setFile(e.target.files[0]);
  };

  // 🔥 FILE UPLOAD
  const handleUploadFile = async () => {
    if (!auth.currentUser) return alert("User not logged in");
    if (!file) return alert("Please select a file");

    setLoading(true);
    setResult(null);
    setError(null);

    try {
      const formData = new FormData();

      formData.append("file", file);
      formData.append("match_name", title);
      formData.append("user_id", auth.currentUser.uid);
      formData.append("teams", tags);
      formData.append("event_date", eventDate);
      formData.append("organization", organization);

      const token = await auth.currentUser?.getIdToken();
      const API = process.env.REACT_APP_API_URL;
      const res = await fetch(`${process.env.REACT_APP_API_URL}/api/upload`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      const data = await res.json();
      console.log("RESPONSE:", data);
   navigate(`/app/media/${data.media_id}`);
    } catch (err) {
      setError("Upload failed. Make sure the server is running.");
    } finally {
      setLoading(false);
    }
  };

  // 🔥 URL UPLOAD
  const handleUploadUrl = async () => {
    if (!auth.currentUser) return alert("User not logged in");
    if (!urlInput) return alert("Please enter a URL");

    setLoading(true);
    setResult(null);
    setError(null);

    try {
      const formData = new FormData();

      formData.append("url", urlInput);
      formData.append("match_name", title);
      formData.append("user_id", auth.currentUser.uid);
      formData.append("teams", tags);
      formData.append("event_date", eventDate);
      formData.append("organization", organization);

      const token = await auth.currentUser?.getIdToken();
      const API = process.env.REACT_APP_API_URL;
      const res = await fetch(`${process.env.REACT_APP_API_URL}/api/upload-url`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      const data = await res.json();
     navigate(`/app/media/${data.media_id}`);
    } catch (err) {
      setError("URL upload failed.");
    } finally {
      setLoading(false);
    }
  };

  const resetAll = () => {
    setFile(null);
    setUrlInput("");
    setTitle("");
    setTags("");
    setEventDate("");
    setOrganization("");
    setResult(null);
    setError(null);
  };

  return (
    <div className="upload-container">
      <h2>Upload Media</h2>
      <p className="subtitle">
        Upload your digital content to protect and monitor
      </p>

      {/* Mode Toggle */}
      <div className="mode-toggle">
        <button
          className={mode === "file" ? "active" : ""}
          onClick={() => {
            setMode("file");
            resetAll();
          }}
        >
          Upload File
        </button>
        <button
          className={mode === "url" ? "active" : ""}
          onClick={() => {
            setMode("url");
            resetAll();
          }}
        >
          Upload via URL
        </button>
      </div>

      {/* FILE MODE */}
      {mode === "file" && (
        <>
          <div
            className={`upload-box ${file ? "has-file" : ""}`}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onClick={() => fileInputRef.current.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*,video/*"
              style={{ display: "none" }}
              onChange={handleFileSelect}
            />
            {file ? (
              <>
                <p>✅</p>
                <h4>{file.name}</h4>
                <span>{(file.size / 1024 / 1024).toFixed(2)} MB</span>
              </>
            ) : (
              <>
                <p>⬆️</p>
                <h4>Drag & drop your files here</h4>
                <span>or click to browse</span>
              </>
            )}
          </div>

          <div className="media-form">
            <h3>Media Details</h3>

            <input
              type="text"
              placeholder="Match Name"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />

            <input
              type="text"
              placeholder="Teams (India,Pakistan)"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
            />

            <input
              type="date"
              value={eventDate}
              onChange={(e) => setEventDate(e.target.value)}
            />

            <input
              type="text"
              placeholder="Organization"
              value={organization}
              onChange={(e) => setOrganization(e.target.value)}
            />

            <button onClick={handleUploadFile} disabled={loading}>
              {loading ? "Analyzing..." : "Upload Media"}
            </button>
          </div>
        </>
      )}

      {/* URL MODE */}
      {mode === "url" && (
        <div className="media-form">
          <h3>Media URL</h3>

          <input
            type="text"
            placeholder="https://example.com/file.jpg"
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
          />

          <input
            type="text"
            placeholder="Match Name"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />

          <input
            type="text"
            placeholder="Teams (India,Pakistan)"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
          />

          <input
            type="date"
            value={eventDate}
            onChange={(e) => setEventDate(e.target.value)}
          />

          <input
            type="text"
            placeholder="Organization"
            value={organization}
            onChange={(e) => setOrganization(e.target.value)}
          />

          <button onClick={handleUploadUrl} disabled={loading}>
            {loading ? "Analyzing..." : "Analyze URL"}
          </button>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="result-box loading">
          <p>🔍 Analyzing media...</p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="result-box error">
          <p>❌ {error}</p>
        </div>
      )}

      {/* Result */}
      {result && (
        <div className={`result-box ${result.duplicate ? "duplicate" : "safe"}`}>
          {/* {result.duplicate ? (
            <>
              <h4>⚠️ Duplicate Detected</h4>
              <p>{result.message}</p>
            </>
          ) : (
            <>
              <h4>✅ Media Verified</h4>
              <p>{result.message}</p>
            </>
          )} */}
          {result.success ? (
  <>
    <h4>✅ Media Processed</h4>
    <p>Media ID: {result.media_id}</p>

    {result.vision_analysis && (
      <div>
        <p><strong>Labels:</strong> {result.vision_analysis.labels.join(", ")}</p>
      </div>
    )}
  </>
) : (
  <>
    <h4>❌ Upload Failed</h4>
  </>
)}
          <button onClick={resetAll}>Upload Another</button>
        </div>
      )}
    </div>
  );
}

export default UploadPage;