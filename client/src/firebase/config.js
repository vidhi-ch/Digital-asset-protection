import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

const firebaseConfig = {
  apiKey: "AIzaSyCql6_8l61qFGqNnFmB2XLdYwtLNna_o2U",
  authDomain: "mediashield-ai.firebaseapp.com",
  projectId: "mediashield-ai",
  storageBucket: "mediashield-ai.firebasestorage.app",
  messagingSenderId: "678299066750",
  appId: "1:678299066750:web:a597296ac23a50a6f0d32f",
  measurementId: "G-7F88MD6FEW"
};

const app = initializeApp(firebaseConfig);

export const db = getFirestore(app);
export const auth = getAuth(app);