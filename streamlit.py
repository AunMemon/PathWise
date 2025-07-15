import streamlit as st
import fitz
from model import JobRecommendationSystem

st.set_page_config(page_title="PathWise - Career Guidance", layout="wide")

recommender = JobRecommendationSystem("JobsFE.csv")

# Session state to persist user profile
if "profile" not in st.session_state:
    st.session_state.profile = {}

st.title("🎓 PathWise – AI-Powered Career Navigation Platform")

menu = st.radio("Navigate", ["🏠 Home", "👤 User Profile", "📄 Resume Upload", 
                              "📊 Job Matches", "📚 Learning Plan", 
                              "💼 Freelance & Startups", "🧭 Future Enhancements"])

# --- Section: Home ---
if menu == "🏠 Home":
    st.markdown("""
    ## Welcome to PathWise
    PathWise helps you discover the right career path using AI-based recommendations tailored to your:
    - Resume content
    - Skills & Interests
    - Career preferences (freelance, startup, full-time)
    """)

# --- Section: User Profile ---
elif menu == "👤 User Profile":
    st.markdown("## 👤 Enter Your Profile Information")

    with st.form("profile_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email (optional)")
        skills = st.text_area("List your technical or soft skills (comma-separated)")
        interests = st.text_area("What are your career interests or passions?")
        preferred_types = st.multiselect("Preferred Job Types", ["Full-time", "Freelance", "Startup"])
        submitted = st.form_submit_button("Save Profile")

    if submitted:
        st.session_state.profile = {
            "name": name,
            "email": email,
            "skills": [s.strip().lower() for s in skills.split(",") if s],
            "interests": interests,
            "preferred_types": preferred_types
        }
        st.success("✅ Profile saved!")

# --- Section: Resume Upload ---
elif menu == "📄 Resume Upload":
    st.markdown("## 📄 Upload Your Resume (PDF)")
    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])
    if uploaded_file:
        with st.spinner("Extracting text..."):
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            resume_text = "\n".join([page.get_text("text") for page in doc]).strip()
            st.session_state.resume_text = resume_text
            st.success("✅ Resume processed successfully!")
            st.text_area("Resume Preview", resume_text, height=250)

# --- Section: Job Matches ---
elif menu == "📊 Job Matches":
    st.markdown("## 📊 AI-Powered Job Recommendations")

    if "resume_text" not in st.session_state or not st.session_state.resume_text:
        st.warning("⚠️ Please upload your resume first.")
    else:
        with st.spinner("Matching you with jobs..."):
            recommendations = recommender.recommend_jobs(st.session_state.resume_text, top_n=20)
            jobs = recommendations["recommended_jobs"]

        for i, job in enumerate(jobs, 1):
            if st.session_state.profile.get("preferred_types"):
                if job["job_type"].capitalize() not in st.session_state.profile["preferred_types"]:
                    continue

            st.markdown(f"### {i}. {job['position']} ({job['job_type'].capitalize()})")
            st.write(f"**Company:** {job['workplace']}")
            st.write(f"**Mode:** {job['working_mode']}")
            st.write(f"**Duties:** {job['job_role_and_duties']}")
            st.write(f"**Required Skills:** {job['requisite_skill']}")

            if job.get("missing_skills"):
                st.warning(f"❌ Missing Skills: {', '.join(job['missing_skills'])}")
            if job.get("learning_links"):
                st.write("📚 *Suggested Courses:*")
                for link in job["learning_links"]:
                    st.markdown(f"- [Course Link]({link})")
            elif not job.get("missing_skills"):
                st.success("✅ You match all required skills!")
            st.write("---")

# --- Section: Learning Plan ---
elif menu == "📚 Learning Plan":
    st.markdown("## 📚 Personalized Learning Plan")
    st.info("This section summarizes the missing skills from your matched jobs and offers suggested courses.")
    # Reuse previous results
    if "resume_text" in st.session_state:
        recs = recommender.recommend_jobs(st.session_state.resume_text, top_n=20)
        all_missing = set()
        for job in recs["recommended_jobs"]:
            all_missing.update(job.get("missing_skills", []))
        if all_missing:
            for skill in sorted(all_missing):
                st.markdown(f"🔹 **{skill.title()}**")
                link = recommender.LEARNING_RESOURCES.get(skill)
                if link:
                    st.markdown(f"↪️ [Suggested Course]({link})")
        else:
            st.success("✅ No skill gaps found across matched jobs!")
    else:
        st.warning("⚠️ Upload your resume first to generate learning suggestions.")

# --- Section: Freelance / Startup ---
elif menu == "💼 Freelance & Startups":
    st.markdown("## 💼 Freelance & Startup Opportunities")
    if "resume_text" in st.session_state:
        results = recommender.recommend_jobs(st.session_state.resume_text, top_n=20)
        for job in results["recommended_jobs"]:
            if job["job_type"].lower() in ["freelance", "startup"]:
                st.markdown(f"### {job['position']} ({job['job_type'].capitalize()})")
                st.write(f"**Company:** {job['workplace']}")
                st.write(f"**Mode:** {job['working_mode']}")
                st.write(f"**Required Skills:** {job['requisite_skill']}")
                st.write(f"**Duties:** {job['job_role_and_duties']}")
                st.write("---")
    else:
        st.warning("⚠️ Please upload your resume to see relevant freelance/startup roles.")

# --- Section: Future Enhancements ---
elif menu == "🧭 Future Enhancements":
    st.markdown("## 🧭 Future Enhancements")
    st.write("Here are the upcoming features aligned with our interim report roadmap:")
    st.markdown("""
    - 🧑‍💻 Conversational AI Bot for live career Q&A
    - 🧠 Advanced Predictive Modeling for long-term career success
    - 🎯 Gamified learning and reward system
    - 🌐 Localization support for international users
    - 🤝 Mentorship session booking from within the app
    """)
