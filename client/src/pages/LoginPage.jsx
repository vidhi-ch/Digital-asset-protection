import { useState } from "react";
import { auth } from "../firebase/config";
import { signInWithEmailAndPassword } from "firebase/auth";
import { GoogleAuthProvider, signInWithPopup } from "firebase/auth";
import "./LoginPage.css";
import { useNavigate } from "react-router-dom";


function LoginPage() {
  const navigate = useNavigate(); 
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = async (e) => {
    e.preventDefault();

    if (!email || !password) {
      alert("Please fill all fields");
      return;
    }

    try {
      const userCredential = await signInWithEmailAndPassword(
  auth,
  email,
  password
);

const user = userCredential.user;

// 🔥 reload to get latest verification status
await user.reload();

if (!user.emailVerified) {
  alert("Please verify your email before logging in");
  return;
}

navigate("/dashboard");
      console.log(user.user);
      navigate("/app/dashboard");
    } catch (err) {
      if (err.code === "auth/user-not-found") {
        alert("User not found");
      } else if (err.code === "auth/wrong-password") {
        alert("Incorrect password");
      } else {
        alert("Login failed");
      }
    }
  };
  const handleGoogleLogin = async () => {
  try {
    const provider = new GoogleAuthProvider();
    const result = await signInWithPopup(auth, provider);

    console.log(result.user);
    navigate("/app/dashboard");
  } catch (err) {
    alert(err.message);
  }
};

  return (
  <div className="login-container">
    {/* 🔥 BRAND HEADER */}
  <div className="brand">
  <div className="brand-row">
    <img src="/logo.png" alt="logo" />
    <h1>MediaShield</h1>
  </div>
  <p>Digital Media Protection Platform</p>
</div>
  <div className="login-card">
    <h2>Welcome Back</h2>
    <p className="subtitle">Sign in to protect your digital content</p>

    <form onSubmit={handleLogin}>
      <label>Email</label>
      <input
        type="email"
        placeholder="you@example.com"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />

      <label>Password</label>
      <input
        type="password"
        placeholder="Enter your password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />

      <button type="submit" className="primary-btn">Sign In</button>
    </form>

    <div className="divider">or</div>

    <button onClick={handleGoogleLogin} className="google-btn">
      <img
     src="https://img.icons8.com/color/16/google-logo.png"
     className="google-icon"
   />
      Continue with Google
    </button>

    <p className="signup-text">
      Don't have an account? <span onClick={() => navigate("/signup")}>Sign up</span>
    </p>
  </div>
</div>
);
}

export default LoginPage;