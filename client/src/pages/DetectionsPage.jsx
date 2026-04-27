import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { db } from "../firebase/config";
import { collection, getDocs } from "firebase/firestore";
import "./DetectionsPage.css"
import { auth } from "../firebase/config";

import { doc, updateDoc, deleteDoc } from "firebase/firestore";
function DetectionsPage() {
const { status } = useParams();
const [data, setData] = useState([]);

useEffect(() => {
  const fetchData = async () => {
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

      const all = snapshot.docs.map((d) => ({
        id: d.id,
        ...d.data(),
      }));

      // 3️⃣ filter detections for your media
      const userDetections = all.filter((d) =>
        userMediaIds.includes(d.original_media_id)
      );

      // 4️⃣ filter by status
      const filtered = userDetections.filter(
        (d) => (d.status || "pending") === status
      );

      setData(filtered);

    } catch (err) {
      console.error("Error fetching detections:", err);
    }
  };

  fetchData();
}, [status]);
const updateStatus = async (id, status) => {
  try {
    await updateDoc(doc(db, "detections", id), { status });

    // update UI instantly
   setData((prev) =>
  prev.filter((d) => d.id !== id)
);
  } catch (err) {
    console.error("Update failed:", err);
  }
};

const handleDelete = async (id) => {
  try {
    if (!window.confirm("Are you sure you want to delete this detection?")) return;

    await deleteDoc(doc(db, "detections", id));

    // remove from UI instantly
    setData((prev) => prev.filter((d) => d.id !== id));

  } catch (err) {
    console.error("Delete failed:", err);
  }
};

return (
<div className="detections-page">
  <h1 className="detections-title">
    {status.toUpperCase()} Detections
  </h1>

  {data.length === 0 ? (
    <p className="empty">No detections found</p>
  ) : (
    <table className="detections-table">
      <thead>
        <tr>
          <th>Match</th>
          <th>Similarity</th>
          <th>Label</th>
          <th>Status</th>
          <th>Actions</th>
        </tr>
      </thead>

      <tbody>
        {data.map((d) => (
          <tr
            key={d.id}
            className={d.similarity_score > 0.7 ? "high-risk-row" : ""}
          >
            <td>{d.match_name}</td>

            <td>
              {d.similarity_score
                ? (d.similarity_score * 100).toFixed(1) + "%"
                : d.similarity_percentage}
            </td>

            <td className="label">{d.label}</td>

            <td>
              <span className={`status-${d.status}`}>
                {d.status}
              </span>
            </td>
            <td>
  {status === "pending" && (
    <>
      <button
        onClick={(e) => {
          e.stopPropagation();
          updateStatus(d.id, "authorized");
        }}
        className="btn btn-approve"
      >
        Authorize
      </button>

      <button
        onClick={(e) => {
          e.stopPropagation();
          updateStatus(d.id, "unauthorized");
        }}
        className="btn btn-reject"
      >
        Unauthorize
      </button>
    </>
  )}

  {status === "authorized" && (
    <button
      onClick={(e) => {
        e.stopPropagation();
        updateStatus(d.id, "unauthorized");
      }}
      className="btn btn-reject"
    >
      Unauthorize
    </button>
  )}

  {status === "unauthorized" && (
    <button
      onClick={(e) => {
        e.stopPropagation();
        updateStatus(d.id, "authorized");
      }}
      className="btn btn-approve"
    >
      Authorize
    </button>
  )}

  {/* 🔴 DELETE BUTTON (for ALL) */}
  <button
    onClick={(e) => {
      e.stopPropagation();
      handleDelete(d.id);
    }}
    className="btn btn-delete"
  >
    Delete
  </button>
</td>
            
          </tr>
        ))}
      </tbody>
    </table>
  )}
</div>
);
}

export default DetectionsPage;
