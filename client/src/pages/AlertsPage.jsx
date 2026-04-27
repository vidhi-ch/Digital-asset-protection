import { useEffect, useState } from "react";
import { db } from "../firebase/config";
import {
collection,
getDocs,
updateDoc,
doc,
query,
orderBy,
} from "firebase/firestore";
import "./AlertPage.css";
import { auth } from "../firebase/config";

function AlertPage() {
const [alerts, setAlerts] = useState([]);
const [loading, setLoading] = useState(true);

const [showPopup, setShowPopup] = useState(false);
useEffect(() => {
fetchAlerts();
localStorage.setItem("hasNewAlerts", "false");
}, []);

const fetchAlerts = async () => {
  try {
    const user = auth.currentUser;
if (!user) return;

// 1️⃣ get user's media
const mediaSnap = await getDocs(collection(db, "registered_media"));

const userMediaIds = mediaSnap.docs
  .filter((doc) => doc.data().metadata?.user_id === user.uid)
  .map((doc) => doc.id);

// 2️⃣ get detections
const snapshot = await getDocs(collection(db, "detections"));

const data = snapshot.docs
  .map((doc) => ({
    id: doc.id,
    ...doc.data(),
  }))
  // 🔥 filter only YOUR detections
  .filter((item) =>
    userMediaIds.includes(item.original_media_id)
  )
  // 🔥 then pending
  .filter((item) => item.status === "pending")
  .sort((a, b) => {
    return new Date(b.createdAt || 0) - new Date(a.createdAt || 0);
  });

    setAlerts(data);
    setLoading(false);

    // 🔥 UPDATED LOGIC (popup + red dot)
    const prevCount = parseInt(localStorage.getItem("alertCount") || 0);

    if (data.length > prevCount) {
      setShowPopup(true);

      // 🔴 show red dot in navbar
      localStorage.setItem("hasNewAlerts", "true");
    }

    // always update latest count
    localStorage.setItem("alertCount", data.length);

  } catch (error) {
    console.error("Error fetching alerts:", error);
  }
};

const handleAction = async (id, status) => {
try {
const ref = doc(db, "detections", id);
await updateDoc(ref, { status });


  // Update UI instantly
  setAlerts((prev) =>
  prev.filter((item) => item.id !== id)
);
} catch (error) {
  console.error("Error updating status:", error);
}


};

if (loading) {
return <p className="alert-page">Loading alerts...</p>;
}

return ( <div className="alert-page">
  {showPopup && (
  <div className="alert-popup">
    🚨 {alerts.length} new detections found!
    <button onClick={() => setShowPopup(false)}>X</button>
  </div>
)}
 <div className="alert-header">
  <h1>Alerts</h1>
  <div className="alert-count-badge">
    {alerts.length} Pending
  </div>
</div>

<div className="alert-summary">
  {alerts.length} detections require review
</div>
  {alerts.length === 0 ? (
    <p>No pending alerts 🎉</p>
  ) : (
    alerts.map((alert) => (
      <div
        key={alert.id}
        className={`alert-card ${
          alert.similarity_score > 0.7 ? "high-risk" : ""
        }`}
      >
        {/* Image */}
        <img
          src={alert.image_url}
          alt="preview"
          className="alert-image"
        />

        {/* Info */}
        <div className="alert-info">
          <p className="alert-match">{alert.match_name}</p>
          

          <p className="alert-text">
            Similarity: {alert.similarity_percentage}
          </p>

          <p className="alert-label">{alert.label}</p>

          <p className="alert-platform">
            Platform: {alert.platform}
          </p>

          <p className="alert-status">
            Status:
            <span
              className={
                alert.status === "authorized"
                  ? "status-authorized"
                  : alert.status === "unauthorized"
                  ? "status-unauthorized"
                  : "status-pending"
              }
            >
              {" "}
              {alert.status}
            </span>
          </p>
        </div>

        {/* Buttons */}
        <div className="alert-actions">
          <button
            onClick={() =>
              handleAction(alert.id, "authorized")
            }
            className="btn btn-approve"
          >
            Authorize
          </button>

          <button
            onClick={() =>
              handleAction(alert.id, "unauthorized")
            }
            className="btn btn-reject"
          >
            Unauthorize
          </button>
        </div>
      </div>
    ))
  )}
</div>

);
}

export default AlertPage;
