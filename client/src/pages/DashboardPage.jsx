import { useEffect, useState } from "react";
import { auth } from "../firebase/config";
import { db } from "../firebase/config";
import { collection, getDocs } from "firebase/firestore";
import "./DashboardPage.css";
import { useNavigate } from "react-router-dom";

function DashboardPage() {
  
  const navigate = useNavigate();
  const user = auth.currentUser;

  const [stats, setStats] = useState({
    total: 0,
    authorized: 0,
    unauthorized: 0,
    pending: 0,
  });

  const [recent, setRecent] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
  try {
    // 🔹 1. Total uploads (keep as is)
    const user = auth.currentUser;
if (!user) return;

const mediaSnap = await getDocs(collection(db, "registered_media"));

const userMedia = mediaSnap.docs.filter(
  (doc) => doc.data().metadata?.user_id === user.uid
);

const total = userMedia.length;

    // 🔹 2. Get detections
    const detSnap = await getDocs(collection(db, "detections"));

    let authorized = 0;
    let unauthorized = 0;
    let pending = 0;

    // get user's media IDs
const userMediaIds = userMedia.map((doc) => doc.id);

detSnap.forEach((doc) => {
  const d = doc.data();

  // 🔥 filter only your media detections
  if (!userMediaIds.includes(d.original_media_id)) return;

  if (d.status === "authorized") authorized++;
  else if (d.status === "unauthorized") unauthorized++;
  else pending++;
});

    setStats({
      total,
      authorized,
      unauthorized,
      pending,
    });

    // 🔹 3. Recent uploads (same as before)
    const docs = mediaSnap.docs
  .map((d) => ({
    id: d.id,
    ...d.data(),
  }))
  .filter((d) => d.metadata?.user_id === user.uid);
    const sorted = [...docs].sort((a, b) => {
      const aTime = a.registered_at?.seconds || 0;
      const bTime = b.registered_at?.seconds || 0;
      return bTime - aTime;
    });

    setRecent(sorted.slice(0, 5));

  } catch (err) {
    console.error("Failed to fetch stats:", err);
  } finally {
    setLoading(false);
  }
};

    fetchStats();
  }, []);

  const formatDate = (ts) => {
    if (!ts) return "—";
    const date = new Date(ts.seconds * 1000);
    return date.toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  };

  return (
    <>
    <div className="dashboard-container">
      {/* Header */}
      <div className="dash-header">
  <div className="dash-left">
    <h1>Dashboard</h1>
    <p className="dash-subtitle">Welcome back, {user?.email}</p>
  </div>


</div>

      {/* Stats */}
      {loading ? (
        <p className="loading-text">Loading stats...</p>
      ) : (
        <div className="stats-grid">
          <div className="stat-card total">
            <p>Total Uploads</p>
            <h2>{stats.total}</h2>
          </div>

          <div
  className="stat-card authorized"
  onClick={() => navigate("/app/detections/authorized")}
>
            <p>Authorized</p>
            <h2>{stats.authorized}</h2>
          </div>

          <div className="stat-card unauthorized" onClick={() => navigate("/app/detections/unauthorized")}>
            <p>Unauthorized</p>
            <h2>{stats.unauthorized}</h2>
          </div>

          <div className="stat-card pending" onClick={() => navigate("/app/detections/pending")}>
            <p>Pending</p>
            <h2>{stats.pending}</h2>
          </div>
   
        </div>
      )}

      {/* Recent Uploads */}
      <div className="recent-section">
        <div className="recent-header">
  <h3>Recent Uploads</h3>

  <button
    className="view-all-btn"
    onClick={() => navigate("/app/media-library")}
  >
    View All →
  </button>
</div>

        {recent.length === 0 ? (
          <p className="empty-text">
            No uploads yet. Go to Upload page to get started!
          </p>
        ) : (
          <div className="recent-list">
            {recent.map((item) => {
              console.log(item);
              const status =
                item.status ||
                (item.duplicate ? "unauthorized" : "authorized");

              return (
                <div className="recent-item" key={item.id} onClick={()=>navigate(`/app/media/${item.id}`)}>
                  <div className="recent-icon">
  {item.thumbnail ? (
    <img src={item.thumbnail} alt="" />
  ) : (
    "🖼️"
  )}
</div>

                  <div className="recent-info">
                    <p className="recent-name">
                      {item.metadata?.match_name||item.filename || item.url || "Unknown"}
                    </p>
                    <p className="recent-date">
                      {formatDate(item.createdAt)}
                    </p>
                  </div>

                  <div className={`recent-badge badge-${status}`}>
                    {status === "authorized" && "Authorized"}
                    {status === "unauthorized" && "Unauthorized"}
                    {status === "pending" && "Pending"}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
    </>
  );
}

export default DashboardPage;