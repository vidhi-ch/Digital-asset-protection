const FormData = require("form-data");
const axios = require("axios");
const db = require("../firebase/config");

const ML_API = "https://mediashield-ml-678299066750.us-central1.run.app";

exports.uploadFile = async (req, res) => {
  try {
     console.log("🔥 API HIT /upload");

    console.log("BODY:", req.body);
    console.log("FILE:", req.file);
    const file = req.file;
    const { match_name, teams, event_date, organization,user_id  } = req.body;

    if (!file) {
      return res.status(400).json({ message: "No file uploaded" });
    }

    // ⚠️ validate required fields
    if (!match_name || !teams || !event_date || !organization || !user_id) {
      return res.status(400).json({ message: "Missing required fields" });
    }

    const formData = new FormData();

    // file
    formData.append("file", file.buffer, {
      filename: file.originalname,
      contentType: file.mimetype,
    });

    // required fields (VERY IMPORTANT)
    formData.append("match_name", match_name);
    formData.append("teams", teams);
    formData.append("event_date", event_date);
    formData.append("organization", organization);
    formData.append("user_id", user_id);

    const response = await axios.post(
      `${ML_API}/register`,
      formData,
      {
        headers: {
          ...formData.getHeaders(),
        },
      }
    );
    console.log("✅ AI RESPONSE:", response.data);

    const media_id = response.data.media_id;
const detections = response.data.detections || [];

// await db.collection("registered_media").doc(media_id).set({
//   media_id,
//   metadata: {
//     match_name,
//     teams,
//     event_date,
//     organization,
//   },
//   createdAt: new Date(),
// });

for (const det of detections) {
  await db.collection("detections").add({
    similarity_score: det.similarity_score || null,
    similarity_percentage: det.similarity_percentage || null,
    image_url: det.source_url || det.image_url || "", // ⚠️ important mapping
    status: "pending",
    original_media_id: media_id,
    createdAt: new Date(),
  });
}

    res.status(200).json(response.data);

} catch (err) {
  console.error("❌ ERROR:", err.response?.data || err.message);

  res.status(500).json({
    error: err.response?.data || err.message,
  });
}
};

exports.uploadFromUrl = async (req, res) => {
  try {
    const { url, match_name, teams, event_date, organization , user_id} = req.body;

    if (!url) {
      return res.status(400).json({ message: "No URL provided" });
    }
    if (!match_name || !teams || !event_date || !organization) {
  return res.status(400).json({ message: "Missing required fields" });
}
    const formData = new FormData();

    formData.append("media_url", url);
formData.append("match_name", match_name);
formData.append("teams", teams);
formData.append("event_date", event_date);
formData.append("organization", organization);
formData.append("user_id", user_id);
    const response = await axios.post(
      `${ML_API}/register-url`,
      formData,
      {
        headers: formData.getHeaders(),
      }
    );

    res.json(response.data);

  } catch (err) {
    console.error("UPLOAD ERROR:", err);
    res.status(500).json({ error: err.message });
  }
};