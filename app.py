import streamlit as st
import requests
from datetime import datetime
import io
import PyPDF2

st.set_page_config(page_title="Aura Career AI", page_icon="🎯", layout="wide")

st.markdown("""
<style>
.stApp { background-color: #0b1120; color: white; }
.main-title { text-align: center; font-size: 50px; font-weight: bold; color: #00ffff; }
.subtitle { text-align: center; color: #bbbbbb; margin-bottom: 20px; }
div[data-testid="stSidebar"] { background-color: #0d1b2e; }
.stTextArea textarea { background-color: #1a2a4a !important; color: white !important; border: 1px solid #00ffff33 !important; }
.metric-card { background: #1a2a4a; border-radius: 10px; padding: 15px; text-align: center; border: 1px solid #00ffff33; }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'>🎯 Aura Career AI</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Resume Analyzer + Mock Interview — Land Your Dream Job!</div>", unsafe_allow_html=True)

# ── SIDEBAR ──
with st.sidebar:
    st.markdown("## ⚙ Settings")
    st.markdown("---")
    feature = st.selectbox("🧩 Choose Feature", [
        "📄 Resume Analyzer",
        "🎯 Mock Interview",
        "📝 Cover Letter Generator",
        "💼 Job Description Analyzer",
        "🔗 LinkedIn Profile Reviewer",
    ])
    st.markdown("**🤖 AI Model:**")
    model = st.selectbox("Model", [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
    ])
    st.markdown("---")
    st.caption("Built by Rupal Darode 🚀")


# ── GROQ HELPER ──
def groq_ask(system, user_msg, temperature=0.5, max_tokens=2000):
    try:
        GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    except Exception:
        return "❌ GROQ_API_KEY not found in Streamlit secrets."
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers, json=payload, timeout=30
        )
        data = res.json()
        if "choices" in data:
            return data["choices"][0]["message"]["content"].strip()
        elif "error" in data:
            return f"❌ {data['error']['message']}"
        return "❌ Unexpected error."
    except Exception as e:
        return f"❌ Error: {str(e)}"


# ── PDF READER ──
def read_pdf(uploaded_file):
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text[:5000]
    except Exception as e:
        return f"Error reading PDF: {e}"


# ══════════════════════════════════════════
# FEATURE 1: RESUME ANALYZER
# ══════════════════════════════════════════
if "Resume Analyzer" in feature:
    st.subheader("📄 Resume Analyzer & ATS Score")
    st.caption("Upload your resume + paste job description → Get ATS score, feedback & improved resume")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**📎 Upload Resume (PDF)**")
        resume_file = st.file_uploader("Upload PDF", type=["pdf"], key="resume")
        resume_text = ""
        if resume_file:
            resume_text = read_pdf(resume_file)
            st.success(f"✅ Resume loaded — {len(resume_text)} characters")

    with col2:
        st.markdown("**📋 Paste Job Description**")
        job_desc = st.text_area("Job Description", height=180,
                                placeholder="Paste the job description you are applying for...")

    experience = st.selectbox("Your Experience Level", [
        "Fresher (0-1 years)",
        "Junior (1-3 years)",
        "Mid-level (3-6 years)",
        "Senior (6+ years)"
    ])

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        ats_btn = st.button("🎯 Get ATS Score", use_container_width=True)
    with col_b:
        improve_btn = st.button("✨ Improve Resume", use_container_width=True)
    with col_c:
        gaps_btn = st.button("🔍 Find Skill Gaps", use_container_width=True)

    if ats_btn:
        if not resume_text:
            st.warning("Please upload your resume!")
        elif not job_desc.strip():
            st.warning("Please paste the job description!")
        else:
            with st.spinner("Analyzing your resume..."):
                system = """You are an expert ATS (Applicant Tracking System) and HR consultant with 10+ years experience.
                Analyze resumes for Indian job market. Be specific and actionable."""

                prompt = f"""Analyze this resume against the job description and provide:

1. **ATS SCORE: XX/100** (be realistic)
2. **Keyword Match** — list matched and missing keywords
3. **Strengths** — what's good (3-4 points)
4. **Critical Issues** — what must be fixed (3-4 points)
5. **Quick Wins** — 3 changes that will immediately improve the score
6. **Section-wise Rating** — rate each section: Contact, Summary, Experience, Skills, Education

Experience Level: {experience}

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_desc}"""

                result = groq_ask(system, prompt)
                st.markdown(result)
                st.download_button("⬇ Download Analysis",
                                   result,
                                   file_name="resume_analysis.txt",
                                   mime="text/plain",
                                   use_container_width=True)

    if improve_btn:
        if not resume_text:
            st.warning("Please upload your resume!")
        else:
            with st.spinner("Rewriting your resume..."):
                system = "You are an expert resume writer for the Indian job market. Write powerful, ATS-optimized resumes."
                prompt = f"""Rewrite and improve this resume to be more powerful and ATS-friendly.

Experience Level: {experience}
Job Target: {job_desc[:500] if job_desc else 'General improvement'}

ORIGINAL RESUME:
{resume_text}

Provide a completely rewritten, improved version with:
- Strong action verbs
- Quantified achievements
- ATS-friendly keywords
- Clean formatting
- Powerful summary"""

                result = groq_ask(system, prompt, temperature=0.4)
                st.markdown(result)
                st.download_button("⬇ Download Improved Resume",
                                   result,
                                   file_name="improved_resume.txt",
                                   mime="text/plain",
                                   use_container_width=True)

    if gaps_btn:
        if not resume_text or not job_desc.strip():
            st.warning("Please upload resume and paste job description!")
        else:
            with st.spinner("Finding skill gaps..."):
                system = "You are a career counselor specializing in the Indian tech job market."
                prompt = f"""Compare this resume with the job description and identify:

1. **Missing Technical Skills** — skills in JD not in resume
2. **Missing Soft Skills** — soft skills mentioned in JD
3. **Experience Gaps** — experience requirements not met
4. **Certifications Needed** — certifications that would help
5. **Learning Roadmap** — specific courses/resources to fill each gap (mention free Indian resources like NPTEL, Coursera free tier)

RESUME: {resume_text}
JOB DESCRIPTION: {job_desc}"""

                result = groq_ask(system, prompt)
                st.markdown(result)


# ══════════════════════════════════════════
# FEATURE 2: MOCK INTERVIEW
# ══════════════════════════════════════════
elif "Mock Interview" in feature:
    st.subheader("🎯 AI Mock Interview")
    st.caption("Practice interview with AI — get instant feedback on every answer")

    col1, col2 = st.columns(2)
    with col1:
        interview_type = st.selectbox("Interview Type", [
            "HR Round",
            "Technical Round",
            "Behavioural Round",
            "Managerial Round",
            "Campus Placement",
        ])
    with col2:
        company_type = st.selectbox("Company Type", [
            "Indian IT (TCS/Infosys/Wipro)",
            "Product Startup",
            "MNC",
            "Banking/Finance",
            "General",
        ])

    job_role = st.text_input("Job Role", placeholder="e.g. Python Developer, Data Scientist, ML Engineer")
    resume_summary = st.text_area("Paste your Resume Summary (optional)",
                                   height=100,
                                   placeholder="Paste a brief summary of your experience...")

    if "interview_questions" not in st.session_state:
        st.session_state.interview_questions = []
        st.session_state.current_q = 0
        st.session_state.interview_answers = []
        st.session_state.interview_started = False

    if st.button("🚀 Start Interview", use_container_width=True):
        with st.spinner("Preparing your interview..."):
            system = "You are an expert interviewer from top Indian companies. Generate realistic interview questions."
            prompt = f"""Generate 5 interview questions for:
Role: {job_role}
Type: {interview_type}
Company: {company_type}
Candidate background: {resume_summary if resume_summary else 'Not provided'}

Return ONLY the 5 questions, numbered 1-5. No explanations."""

            result = groq_ask(system, prompt, temperature=0.6)
            questions = [q.strip() for q in result.split('\n') if q.strip() and q[0].isdigit()]
            st.session_state.interview_questions = questions[:5]
            st.session_state.current_q = 0
            st.session_state.interview_answers = []
            st.session_state.interview_started = True
            st.rerun()

    if st.session_state.interview_started and st.session_state.interview_questions:
        total = len(st.session_state.interview_questions)
        current = st.session_state.current_q

        if current < total:
            st.markdown("---")
            st.progress((current) / total)
            st.caption(f"Question {current + 1} of {total}")

            question = st.session_state.interview_questions[current]
            st.markdown(f"### ❓ {question}")

            answer = st.text_area("Your Answer", height=150,
                                   key=f"answer_{current}",
                                   placeholder="Type your answer here...")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Submit Answer & Get Feedback", use_container_width=True):
                    if answer.strip():
                        with st.spinner("Evaluating your answer..."):
                            system = "You are an expert interviewer. Give constructive, specific feedback."
                            prompt = f"""Evaluate this interview answer:

Question: {question}
Role: {job_role}
Interview Type: {interview_type}
Answer: {answer}

Give feedback on:
1. **Score: X/10**
2. **What was good**
3. **What was missing**
4. **Ideal answer would include**
5. **One tip to improve**

Be encouraging but honest."""

                            feedback = groq_ask(system, prompt)
                            st.session_state.interview_answers.append({
                                "question": question,
                                "answer": answer,
                                "feedback": feedback
                            })
                            st.markdown("#### 💬 Feedback:")
                            st.info(feedback)
                            st.session_state.current_q += 1

            with col2:
                if st.button("⏭ Skip Question", use_container_width=True):
                    st.session_state.current_q += 1
                    st.rerun()

        else:
            # Interview complete
            st.success("🎉 Interview Complete!")
            st.markdown("### 📊 Your Performance Summary")

            with st.spinner("Generating final report..."):
                all_qa = "\n\n".join([
                    f"Q: {item['question']}\nA: {item['answer']}\nFeedback: {item['feedback']}"
                    for item in st.session_state.interview_answers
                ])

                system = "You are a career coach. Give an overall interview performance report."
                prompt = f"""Based on these interview answers, give a final performance report:

{all_qa}

Include:
1. **Overall Score: X/10**
2. **Top 3 Strengths shown**
3. **Top 3 Areas to improve**
4. **Ready for interview? Yes/No/Almost**
5. **3 specific things to practice before actual interview**"""

                final = groq_ask(system, prompt)
                st.markdown(final)

                full_report = f"INTERVIEW REPORT\n{'='*50}\n\n{all_qa}\n\n{'='*50}\nFINAL ASSESSMENT\n{final}"
                st.download_button("⬇ Download Full Report",
                                   full_report,
                                   file_name="interview_report.txt",
                                   mime="text/plain",
                                   use_container_width=True)

            if st.button("🔄 Start New Interview", use_container_width=True):
                for key in ["interview_questions", "current_q", "interview_answers", "interview_started"]:
                    del st.session_state[key]
                st.rerun()


# ══════════════════════════════════════════
# FEATURE 3: COVER LETTER GENERATOR
# ══════════════════════════════════════════
elif "Cover Letter" in feature:
    st.subheader("📝 Cover Letter Generator")
    st.caption("Generate a personalized cover letter in seconds")

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Your Name", placeholder="Rupal Darode")
        job_title = st.text_input("Job Title Applying For", placeholder="Python Developer")
        company = st.text_input("Company Name", placeholder="TCS, Google, Startup...")
    with col2:
        experience_years = st.text_input("Years of Experience", placeholder="4")
        key_skills = st.text_input("Your Top 3 Skills", placeholder="Python, ML, Streamlit")
        tone = st.selectbox("Tone", ["Professional", "Enthusiastic", "Formal", "Creative"])

    resume_text = st.text_area("Paste Resume Summary", height=120,
                                placeholder="Brief summary of your background...")
    job_desc = st.text_area("Paste Job Description", height=120,
                             placeholder="Paste the job description...")

    if st.button("✍ Generate Cover Letter", use_container_width=True):
        if name and job_title and company:
            with st.spinner("Writing your cover letter..."):
                system = "You are an expert cover letter writer for the Indian job market."
                prompt = f"""Write a compelling {tone} cover letter for:

Name: {name}
Applying for: {job_title} at {company}
Experience: {experience_years} years
Skills: {key_skills}
Background: {resume_text}
Job Description: {job_desc}

Write a 3-paragraph cover letter that:
- Opens with a strong hook
- Highlights relevant experience and skills
- Closes with confidence and call to action
- Is tailored specifically to {company}
- Sounds human, not generic"""

                result = groq_ask(system, prompt, temperature=0.7)
                st.markdown(result)
                st.download_button("⬇ Download Cover Letter",
                                   result,
                                   file_name=f"cover_letter_{company}.txt",
                                   mime="text/plain",
                                   use_container_width=True)
        else:
            st.warning("Please fill Name, Job Title and Company!")


# ══════════════════════════════════════════
# FEATURE 4: JOB DESCRIPTION ANALYZER
# ══════════════════════════════════════════
elif "Job Description" in feature:
    st.subheader("💼 Job Description Analyzer")
    st.caption("Understand exactly what a company wants before you apply")

    job_desc = st.text_area("Paste Job Description", height=250,
                             placeholder="Paste the complete job description here...")

    col1, col2, col3 = st.columns(3)
    with col1:
        decode_btn = st.button("🔍 Decode JD", use_container_width=True)
    with col2:
        salary_btn = st.button("💰 Salary Estimate", use_container_width=True)
    with col3:
        fit_btn = st.button("✅ Am I a Good Fit?", use_container_width=True)

    your_profile = st.text_area("Your Profile (for fit analysis)", height=100,
                                 placeholder="Brief summary of your skills and experience...")

    if decode_btn and job_desc.strip():
        with st.spinner("Decoding JD..."):
            system = "You are an expert HR consultant and career advisor."
            prompt = f"""Decode this job description and extract:

1. **Must-Have Skills** — non-negotiable requirements
2. **Good-to-Have Skills** — preferred but not required
3. **Red Flags** — anything suspicious or concerning
4. **Company Culture Hints** — what the work environment might be like
5. **Real Role vs Title** — what you'll actually be doing
6. **Ideal Candidate Profile** — who they're really looking for
7. **Interview Prep Tips** — what topics to prepare based on this JD

JOB DESCRIPTION:
{job_desc}"""

            result = groq_ask(system, prompt)
            st.markdown(result)

    if salary_btn and job_desc.strip():
        with st.spinner("Estimating salary..."):
            system = "You are an expert in Indian job market salaries."
            prompt = f"""Based on this job description, estimate:

1. **Salary Range** for Indian market (in LPA)
2. **Factors affecting salary** in this role
3. **Negotiation Tips** specific to this role
4. **Benefits to ask for** beyond salary

JOB DESCRIPTION:
{job_desc}"""

            result = groq_ask(system, prompt)
            st.info(result)

    if fit_btn:
        if not job_desc.strip() or not your_profile.strip():
            st.warning("Please paste JD and your profile!")
        else:
            with st.spinner("Checking your fit..."):
                system = "You are a brutally honest career advisor."
                prompt = f"""Analyze if this candidate is a good fit for this job:

CANDIDATE PROFILE:
{your_profile}

JOB DESCRIPTION:
{job_desc}

Give:
1. **Fit Score: XX%**
2. **Should you apply? Yes/No/Maybe**
3. **Matching points** — where you fit well
4. **Gap points** — where you fall short
5. **How to position yourself** — how to present your profile for best chances"""

                result = groq_ask(system, prompt)
                st.markdown(result)


# ══════════════════════════════════════════
# FEATURE 5: LINKEDIN PROFILE REVIEWER
# ══════════════════════════════════════════
elif "LinkedIn" in feature:
    st.subheader("🔗 LinkedIn Profile Reviewer")
    st.caption("Optimize your LinkedIn to attract recruiters")

    col1, col2 = st.columns(2)
    with col1:
        current_role = st.text_input("Current Role/Title", placeholder="AI/ML Developer")
        target_role = st.text_input("Target Role", placeholder="Senior ML Engineer")
    with col2:
        experience = st.text_input("Years of Experience", placeholder="4")
        industry = st.text_input("Industry", placeholder="IT/Software")

    headline = st.text_input("Current LinkedIn Headline", placeholder="Your current headline...")
    summary = st.text_area("Current LinkedIn Summary/About", height=150,
                            placeholder="Paste your current LinkedIn About section...")
    skills_list = st.text_area("Your Skills (comma separated)", height=80,
                                placeholder="Python, Machine Learning, Streamlit, LLM...")

    if st.button("🔍 Review My LinkedIn Profile", use_container_width=True):
        if current_role and headline:
            with st.spinner("Reviewing your profile..."):
                system = "You are a LinkedIn optimization expert and recruiter with 10+ years experience in Indian tech industry."
                prompt = f"""Review and optimize this LinkedIn profile:

Current Role: {current_role}
Target Role: {target_role}
Experience: {experience} years
Industry: {industry}
Current Headline: {headline}
Current Summary: {summary}
Skills: {skills_list}

Provide:
1. **Profile Strength Score: XX/100**
2. **Optimized Headline** — write 3 better headline options
3. **Improved Summary** — rewrite their About section
4. **Skills to Add** — missing skills recruiters search for
5. **Skills to Remove/Reorder** — less relevant ones
6. **Profile Tips** — 5 specific actions to get more recruiter views
7. **Keywords to Add** — SEO keywords for their target role"""

                result = groq_ask(system, prompt, temperature=0.5)
                st.markdown(result)
                st.download_button("⬇ Download Recommendations",
                                   result,
                                   file_name="linkedin_review.txt",
                                   mime="text/plain",
                                   use_container_width=True)
        else:
            st.warning("Please fill Current Role and Headline!")


# ── FOOTER ──
st.markdown("---")
st.markdown(
    "<center style='color: #555; font-size: 12px;'>Built with ❤️ by Rupal Darode | Aura Career AI 🎯 | Powered by Groq AI</center>",
    unsafe_allow_html=True
)
