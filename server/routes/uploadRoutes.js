const express = require("express");
const router = express.Router();
const multer = require("multer");

const verifyUser = require("../middleware/verifyUser"); // 🔥 ADD THIS
const { uploadFile, uploadFromUrl } = require("../controllers/uploadController");

// memory storage
const upload = multer({ storage: multer.memoryStorage() });

// ✅ CORRECT ORDER: verify → multer → controller
router.post("/upload", upload.single("file"), uploadFile);

// for URL (no multer needed, but still verify user)
router.post("/upload-url", uploadFromUrl);

module.exports = router;