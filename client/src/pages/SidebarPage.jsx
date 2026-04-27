import "./SidebarPage.css";

function SidebarPage({ isOpen, setIsOpen }) {
    if (!isOpen) return null;  
  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div className="overlay" onClick={() => setIsOpen(false)}></div>
      )}

      {/* Sidebar */}
      <div className={`sidebar ${isOpen ? "open" : ""}`}>
        <button className="close-btn" onClick={() => setIsOpen(false)}>
          ✖
        </button>

        <h2>Your Media</h2>

        {/* You’ll connect real data later */}
        <ul>
          <li>image1.jpg</li>
          <li>video1.mp4</li>
        </ul>
      </div>
    </>
  );
}

export default SidebarPage;