import string
import numpy as np
import faiss
import pandas as pd
import torch
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer

# Define skills and resources
COMMON_SKILLS = [
    "python", "java", "sql", "excel", "communication", "project management",
    "data analysis", "machine learning", "leadership", "react", "cloud", "html",
    "css", "javascript", "public speaking", "finance", "teamwork", "problem solving"
]

LEARNING_RESOURCES = {
    "python": "https://www.coursera.org/specializations/python",
    "sql": "https://www.udemy.com/course/sql-mysql-for-data-analytics/",
    "excel": "https://www.udemy.com/course/microsoft-excel-all-in-one-package/",
    "data analysis": "https://www.edx.org/learn/data-analysis",
    "machine learning": "https://www.coursera.org/learn/machine-learning",
    "public speaking": "https://www.coursera.org/learn/public-speaking"
}

def extract_skills(text):
    text = text.lower()
    found_skills = [skill for skill in COMMON_SKILLS if skill in text]
    return found_skills

MODEL = SentenceTransformer("paraphrase-MiniLM-L6-v2", device="cpu")
MODEL = torch.quantization.quantize_dynamic(MODEL, {torch.nn.Linear}, dtype=torch.qint8)

class JobRecommendationSystem:
    def __init__(self, jobs_csv):
        self.jobs_df = pd.read_csv(jobs_csv)
        self.jobs_df["job_text"] = (
            self.jobs_df["workplace"].astype(str) + " " +
            self.jobs_df["working_mode"].astype(str) + " " +
            self.jobs_df["position"].astype(str) + " " +
            self.jobs_df["job_role_and_duties"].astype(str) + " " +
            self.jobs_df["requisite_skill"].astype(str)
        )
        self.jobs_texts = self.jobs_df["job_text"].tolist()
        self.job_info = self.jobs_df.copy()
        self.job_embeddings = MODEL.encode(self.jobs_texts, convert_to_numpy=True).astype(np.float16)
        self.dim = self.job_embeddings.shape[1]
        self.index = faiss.IndexFlatIP(self.dim)
        self.index.add(self.job_embeddings.astype(np.float16))

    def clean_text(self, text):
        return text.lower().translate(str.maketrans("", "", string.punctuation)).strip()

    def filter_top_jobs(self, resume_text, top_n=100):
        vectorizer = TfidfVectorizer()
        job_vectors = vectorizer.fit_transform(self.jobs_texts)
        resume_vector = vectorizer.transform([resume_text])
        similarity_scores = (job_vectors @ resume_vector.T).toarray().flatten()
        top_indices = np.argsort(similarity_scores)[-top_n:]
        return (
            [self.jobs_texts[i] for i in top_indices],
            self.job_info.iloc[top_indices].reset_index(drop=True),
            self.job_embeddings[top_indices],
        )

    def recommend_jobs(self, resume_text, top_n=20):
        resume_text_clean = self.clean_text(resume_text)
        resume_skills = extract_skills(resume_text_clean)

        filtered_jobs_texts, filtered_jobs_df, filtered_embeddings = self.filter_top_jobs(resume_text_clean)
        resume_embedding = MODEL.encode([resume_text_clean], convert_to_numpy=True).astype(np.float16)

        index = faiss.IndexFlatIP(self.dim)
        index.add(filtered_embeddings.astype(np.float16))
        distances, indices = index.search(resume_embedding.astype(np.float16), top_n)
        recommended_jobs = []

        for idx in indices[0]:
            job = filtered_jobs_df.iloc[idx].to_dict()
            job_skills = [skill.strip().lower() for skill in str(job["requisite_skill"]).split(",") if skill]
            missing_skills = list(set(job_skills) - set(resume_skills))
            suggestions = [LEARNING_RESOURCES[skill] for skill in missing_skills if skill in LEARNING_RESOURCES]

            job["matched_skills"] = list(set(job_skills) & set(resume_skills))
            job["missing_skills"] = missing_skills
            job["learning_links"] = suggestions
            recommended_jobs.append(job)

        return {"recommended_jobs": recommended_jobs}
