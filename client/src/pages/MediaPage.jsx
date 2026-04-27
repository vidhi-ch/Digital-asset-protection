import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { db } from "../firebase/config";
import {
doc,
getDoc,
collection,
getDocs,
updateDoc,
} from "firebase/firestore";
import "./MediaPage.css";
import { auth } from "../firebase/config";

function MediaPage() {
const { media_id } = useParams();

const [media, setMedia] = useState(null);
const [detections, setDetections] = useState([]);
const [loading, setLoading] = useState(true);

useEffect(() => {
const fetchData = async () => {
try {
// 🔹 Fetch media

const mediaSnap = await getDoc(doc(db, "registered_media", media_id));

const mediaData = mediaSnap.data();


// check if media exists
if (!mediaData) {
  console.error("No media found");
  return;
}

// optional user check (safe version)
const user = auth.currentUser;
if (user && mediaData.metadata?.user_id !== user.uid){
  console.error("Unauthorized access");
  return;
}

setMedia(mediaData);


    // 🔹 Fetch detections
    const detSnap = await getDocs(collection(db, "detections"));

    const allDetections = detSnap.docs.map((d) => ({
      id: d.id,
      ...d.data(),
    }));

    // 🔹 Filter detections (FIXED)
    const filtered = allDetections.filter(
      (d) => d.original_media_id === media_id
    );

    // 🔥 Sort by highest similarity
    filtered.sort((a, b) => b.similarity_score - a.similarity_score);

    setDetections(filtered);

  } catch (err) {
    console.error("Error fetching data:", err);
  } finally {
    setLoading(false);
  }
};

fetchData();


}, [media_id]);

// 🔹 Convert GCS → public URL
const rawUrl = media?.metadata?.gcs_uri?.replace(
  "gs://",
  "https://storage.googleapis.com/"
);

const imageUrl = rawUrl ? encodeURI(rawUrl) : null;

// 🔹 Update detection status
const updateStatus = async (id, status) => {
try {
await updateDoc(doc(db, "detections", id), { status });


  setDetections((prev) =>
    prev.map((d) =>
      d.id === id ? { ...d, status } : d
    )
  );
} catch (err) {
  console.error("Update failed:", err);
}


};

if (loading) return <p className="loading">Loading...</p>;
if (!media) return <p className="empty">Media not found</p>;
console.log("MEDIA:", media);
console.log("GCS URI:", media?.metadata?.gcs_uri);
console.log("FINAL URL:", imageUrl);
return ( <div className="media-page">


  {/* 🖼️ TOP SECTION */}
  <div className="media-header">

    {imageUrl && (
      <img
        src={imageUrl}
        alt="media"
        className="media-preview"
      />
    )}

    <div className="media-details">
      <h2 className="media-title">
        {media.metadata?.match_name || "Untitled Media"}
      </h2>

      <p className="media-meta">
        Organization: {media.metadata?.organization || "—"}
      </p>

      <p className="media-meta">
        Platform: {media.metadata?.platform || "—"}
      </p>

      {media.metadata?.source_url && (
        <a
          href={media.metadata.source_url}
          target="_blank"
          rel="noreferrer"
          className="media-link"
        >
          🔗 View Original Source
        </a>
      )}
    </div>
  </div>

  {/* 🔍 DETECTIONS */}
  <div className="detections-section">
    <h3 className="detections-title">
      Detections ({detections.length})
    </h3>

    {detections.length === 0 ? (
      <p className="empty">No detections found</p>
    ) : (
      <div className="detection-list">
        {detections.map((d) => (
          <div
            key={d.id}
            className={`detection-card ${
              d.similarity_score > 0.7 ? "high-risk" : ""
            }`}
          >

            <div className="detection-info">
              <p>
                Similarity:{" "}
                {d.similarity_score
                  ? (d.similarity_score * 100).toFixed(1) + "%"
                  : d.similarity_percentage}
              </p>

              <p className="detection-label">
                {d.label}
              </p>

              <p>
                Status:
                <span className={`status-${d.status}`}>
                  {" "}{d.status || "pending"}
                </span>
              </p>

              {d.source_url && (
                <a
                  href={d.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="detection-link"
                >
                  View Source
                </a>
              )}
            </div>

            {/* 🎯 ACTIONS */}
            <div className="media-actions">
              <button
                onClick={() =>
                  updateStatus(d.id, "authorized")
                }
                className="btn btn-approve"
              >
                Authorize
              </button>

              <button
                onClick={() =>
                  updateStatus(d.id, "unauthorized")
                }
                className="btn btn-reject"
              >
                Unauthorize
              </button>
            </div>

          </div>
        ))}
      </div>
    )}
  </div>
</div>


);
}

export default MediaPage;
