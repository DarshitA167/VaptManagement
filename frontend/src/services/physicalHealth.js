import axios from "axios";

export const diagnoseDisease = async (symptoms) => {
  try {
    // 🧼 Clean & normalize symptoms
    const formattedSymptoms = Array.isArray(symptoms)
      ? symptoms.map((s) => s.trim().toLowerCase())
      : symptoms.split(",").map((s) => s.trim().toLowerCase());

    // 🌐 API call to Django backend
    const response = await axios.post(
      "http://127.0.0.1:8000/api/security/diagnose/",
      {
        symptoms: formattedSymptoms,
      },
      {
        headers: { "Content-Type": "application/json" },
      }
    );

    const { result, advice } = response.data;

    // 🧠 Join disease names with commas
    const diseases = Array.isArray(result)
      ? result.map((item) => item.disease).join(", ")
      : "Unknown";

    return {
      disease: diseases,
      advice: advice || "No advice provided.",
    };
  } catch (error) {
    console.error(
      "Error diagnosing disease:",
      error.response?.data || error.message
    );
    return {
      disease: "Error",
      advice: "Unable to fetch diagnosis",
    };
  }
};
