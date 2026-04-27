// const admin = require("firebase-admin");

// const verifyUser = async (req, res, next) => {
//   try {
//     const token = req.headers.authorization?.split(" ")[1];

//     if (!token) {
//       return res.status(401).json({ message: "No token provided" });
//     }

//     const decoded = await admin.auth().verifyIdToken(token);

//     req.user = decoded; // 🔥 contains UID

//     next();
//   } catch (err) {
//     return res.status(401).json({ message: "Unauthorized" });
//   }
// };

// module.exports = verifyUser;