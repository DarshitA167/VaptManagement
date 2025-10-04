# import pandas as pd
# import os
# from difflib import get_close_matches

# # Load CSV and normalize column names only once (lazy caching)
# DATASET_PATH = os.path.join("datasets", "Symtomps_Disease_dataset.csv")
# df = pd.read_csv(DATASET_PATH, encoding='latin1')
# df.columns = [col.lower().replace(" ", "_") for col in df.columns]

# SYMPTOM_COLS = df.columns[:-1]  # All except last column
# DISEASE_COL = df.columns[-1]

# # ✅ Helper: Auto-correct using Levenshtein similarity
# def correct_symptom(symptom, valid_symptoms=SYMPTOM_COLS):
#     matches = get_close_matches(symptom, valid_symptoms, n=1, cutoff=0.6)
#     return matches[0] if matches else symptom

# def correct_symptoms(user_symptoms):
#     return [correct_symptom(s.lower().replace(" ", "_")) for s in user_symptoms]

# # 🔮 Main function
# def predict_disease(user_symptoms):
#     if not isinstance(user_symptoms, list):
#         return {"result": [], "advice": "Invalid input format."}

#     # Step 1: Normalize and autocorrect symptoms
#     cleaned_symptoms = correct_symptoms(user_symptoms)

#     # Step 2: Filter only valid symptoms
#     valid_symptoms = [s for s in cleaned_symptoms if s in SYMPTOM_COLS]
#     if not valid_symptoms:
#         return {"disease": "Unknown", "advice": "No matching symptoms found."}

#     # Step 3: Score each disease based on symptom match
#     df["score"] = df[valid_symptoms].sum(axis=1)

#     # Step 4: Group by disease and get top 3
#     top_diseases = df.groupby(DISEASE_COL)["score"].sum().sort_values(ascending=False).head(3)

#     # Step 5: Build response
#     result = [{"disease": disease.title(), "score": int(score)} for disease, score in top_diseases.items()]
    
#     return {
#         "result": result,
#         "advice": "Please consult a doctor for precise treatment."
#     }
