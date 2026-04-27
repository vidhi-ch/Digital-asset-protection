const express = require("express");
const cors = require("cors");
require("dotenv").config();
const db = require("./firebase/config");

const app = express();

app.use(cors());
app.use(express.json());

// routes
const uploadRoutes = require("./routes/uploadRoutes");
app.use("/api", uploadRoutes);



const PORT = process.env.PORT || 8080;

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
}); 