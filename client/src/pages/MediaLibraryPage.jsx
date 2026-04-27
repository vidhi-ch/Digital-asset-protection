import { useEffect, useState } from "react";
import { db } from "../firebase/config";
import { auth } from "../firebase/config";
import { collection, getDocs } from "firebase/firestore";
import { useNavigate } from "react-router-dom";
import "./MediaLibraryPage.css";

function MediaLibraryPage() {
  const [mediaList, setMediaList] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchMedia = async () => {
      try {
        const snap = await getDocs(collection(db, "registered_media"));

        const user = auth.currentUser;
if (!user) return;

const data = snap.docs
  .map((doc) => ({
    id: doc.id,
    ...doc.data(),
  }))
  .filter((media) => media.metadata?.user_id === user.uid);

        setMediaList(data);
      } catch (err) {
        console.error("Error fetching media:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchMedia();
  }, []);

  const getImageUrl = (media) => {
    const gcs = media?.metadata?.gcs_uri;
    if (!gcs) return null;

    return gcs
      .replace("gs://", "https://storage.googleapis.com/")
      .replace(/ /g, "%20");
  };

  if (loading) return <p className="loading">Loading media...</p>;

  return (
    <div className="media-library">
      <h1 className="library-title">Media Library</h1>

      {mediaList.length === 0 ? (
        <p className="empty">No media uploaded yet</p>
      ) : (
        <div className="media-grid">
          {mediaList.map((media) => {
            const imageUrl = getImageUrl(media);

            return (
              <div
                key={media.id}
                className="media-card"
                onClick={() => navigate(`/app/media/${media.id}`)}
              >
                {imageUrl ? (
                  <img src={imageUrl} alt="media" />
                ) : (
                  <div className="media-placeholder">No Preview</div>
                )}

                <div className="media-overlay">
                  <p>{media.metadata?.match_name || "Untitled"}</p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default MediaLibraryPage;