import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { auth } from "./firebase/config";
import { onAuthStateChanged } from "firebase/auth";

import LoginPage from "./pages/LoginPage";
import SignupPage from "./pages/SignupPage";
import LayoutPage from "./pages/LayoutPage";
import DashboardPage from "./pages/DashboardPage";
import UploadPage from "./pages/UploadPage";
import AlertsPage from "./pages/AlertsPage";
import MediaPage from "./pages/MediaPage";
import DetectionsPage from "./pages/DetectionsPage";
import MediaLibraryPage from "./pages/MediaLibraryPage";
function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true); // 🔥 add this

  useEffect(() => {
    const unsub = onAuthStateChanged(auth, (u) => {
      setUser(u);
      setLoading(false); // 🔥 done checking
    });
    return () => unsub();
  }, []);

  if (loading) return <div>Loading...</div>; // 🔥 wait before redirecting

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />

        <Route
          path="/app" 
          element={user ? <LayoutPage /> : <Navigate to="/" />}
        >
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="upload" element={<UploadPage />} />
          <Route path="alerts" element={<AlertsPage />} />
          <Route path="media/:media_id" element={<MediaPage />} />
          <Route path="detections/:status" element={<DetectionsPage />} />
          <Route path="media-library" element={<MediaLibraryPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
