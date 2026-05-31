import streamlit as st
import requests
from datetime import datetime
import io
import PyPDF2
import hmac
import hashlib
import json

st.set_page_config(page_title="Aura Career AI", page_icon="🎯", layout="wide")

st.markdown("""
<style>
.stApp { background-color: #0b1120; color: white; }
.main-title { text-align: center; font-size: 50px; font-weight: bold; color: #00ffff; }
.subtitle { text-align: center; color: #bbbbbb; margin-bottom: 20px; }
div[data-testid="stSidebar"] { background-color: #0d1b2e; }
.stTextArea textarea { background-color: #1a2a4a !important; color: white !important; border: 1px solid #00ffff33 !important; }
.price-card {
    background: linear-gradient(135deg, #1a2a4a, #0d1b2e);
    border: 1px solid #00ffff44;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    margin: 10px 0;
}
.free-badge { background: #2EC4B6; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; }
.paid-badge { background: #E94E77; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'>🎯 Aura Career AI</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>AI-Powered Career Assistant — Resume, Interview, Cover Letter & More</div>", unsafe_allow_html=True)

# ── PRICING PLANS ──
PLANS = {
    "free": {
        "name": "Free",
        "price": 0,
        "features": ["3 Resume Analyses", "1 Mock Interview", "Basic Cover Letter"],
        "badge": "free-badge"
    },
    "basic": {
        "name": "Basic",
        "price": 49,
        "features": ["10 Resume Analyses", "5 Mock Interviews", "Cover Letters", "JD Analyzer"],
        "badge": "paid-badge"
    },
    "pro": {
        "name": "Pro",
        "price": 199,
        "features": ["Unlimited Everything", "LinkedIn Reviewer", "Priority AI Model", "Download Reports"],
        "badge": "paid-badge"
    }
}

# ── SESSION STATE ──
if "plan" not in st.session_state:
    st.session_state.plan = "free"
if "usage" not in st.session_state:
    st.session_state.usage = {"resume": 0, "interview": 0}
if "paid" not in st.session_state:
    st.session_state.paid = False

# ── SIDEBAR ──
with st.sidebar:
    st.markdown("## ⚙ Settings")
    st.markdown("---")

    feature = st.selectbox("🧩 Choose Feature", [
        "🏠 Home & Pricing",
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
    # Show current plan
    plan_name = st.session_state.plan.upper()
    if st.session_state.plan == "free":
        st.markdown(f"**Plan:** <span class='free-badge'>{plan_name}</span>", unsafe_allow_html=True)
    else:
        st.markdown(f"**Plan:** <span class='paid-badge'>{plan_name}</span>", unsafe_allow_html=True)

    st.caption("Built by Rupal Darode 🚀")


# ── GROQ HELPER ──
def groq_ask(system, user_msg, temperature=0.5, max_tokens=2000):
    try:
        GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    except Exception:
        return "❌ GROQ_API_KEY not found."
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


# ── RAZORPAY PAYMENT LINK CREATOR ──
def create_payment_link(amount, description, plan_name):
    try:
        key_id = st.secrets["RAZORPAY_KEY_ID"]
        key_secret = st.secrets["RAZORPAY_KEY_SECRET"]

        payload = {
            "amount": amount * 100,  # paise mein
            "currency": "INR",
            "accept_partial": False,
            "description": description,
            "notify": {"sms": True, "email": True},
            "reminder_enable": True,
            "notes": {"plan": plan_name},
            "callback_url": "https://aura-career-ai.streamlit.app",
            "callback_method": "get"
        }

        res = requests.post(
            "https://api.razorpay.com/v1/payment_links",
            auth=(key_id, key_secret),
            json=payload,
            timeout=15
        )
        data = res.json()
        if "short_url" in data:
            return data["short_url"]
        else:
            return None
    except Exception as e:
        return None


# ── CHECK USAGE LIMIT ──
def check_limit(feature_key, free_limit):
    if st.session_state.plan != "free":
        return True
    if st.session_state.usage.get(feature_key, 0) >= free_limit:
        return False
    return True


def increment_usage(feature_key):
    if st.session_state.plan == "free":
        st.session_state.usage[feature_key] = st.session_state.usage.get(feature_key, 0) + 1


# ── PAYMENT WALL ──
def show_payment_wall(feature_name):
    st.warning(f"⚠️ Free limit reached for {feature_name}!")
    st.markdown("### 🚀 Upgrade to Continue")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class='price-card'>
            <h3>⚡ Basic</h3>
            <h2 style='color: #00ffff;'>₹49</h2>
            <p style='color: #aaa;'>one-time</p>
            <p>✅ 10 Resume Analyses</p>
            <p>✅ 5 Mock Interviews</p>
            <p>✅ Cover Letters</p>
            <p>✅ JD Analyzer</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("💳 Pay ₹49 — Basic", use_container_width=True):
            with st.spinner("Creating payment link..."):
                link = create_payment_link(49, "Aura Career AI — Basic Plan", "basic")
                if link:
                    st.success("Payment link created!")
                    st.markdown(f"### 👉 [Click here to pay ₹49]({link})")
                    st.info("After payment, enter your payment ID below to activate.")
                else:
                    st.error("Could not create payment link. Please try again.")

    with col2:
        st.markdown("""
        <div class='price-card'>
            <h3>💎 Pro</h3>
            <h2 style='color: #E94E77;'>₹199</h2>
            <p style='color: #aaa;'>one-time</p>
            <p>✅ Unlimited Everything</p>
            <p>✅ LinkedIn Reviewer</p>
            <p>✅ Priority AI Model</p>
            <p>✅ Download All Reports</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("💳 Pay ₹199 — Pro", use_container_width=True):
            with st.spinner("Creating payment link..."):
                link = create_payment_link(199, "Aura Career AI — Pro Plan", "pro")
                if link:
                    st.success("Payment link created!")
                    st.markdown(f"### 👉 [Click here to pay ₹199]({link})")
                    st.info("After payment, enter your payment ID below to activate.")
                else:
                    st.error("Could not create payment link. Please try again.")

    st.markdown("---")
    st.markdown("**Already paid? Enter Payment ID to activate:**")
    payment_id = st.text_input("Payment ID (starts with pay_...)")
    selected_plan = st.selectbox("Select Plan", ["basic", "pro"])
    if st.button("✅ Activate Plan"):
        if payment_id.startswith("pay_"):
            st.session_state.plan = selected_plan
            st.session_state.paid = True
            st.success(f"🎉 {selected_plan.upper()} plan activated! Refresh the page.")
            st.rerun()
        else:
            st.error("Invalid payment ID. Should start with 'pay_'")


# ══════════════════════════════════════════
# HOME & PRICING
# ══════════════════════════════════════════
if "Home" in feature:
    st.markdown("## 🎯 Welcome to Aura Career AI!")
    st.markdown("Your complete AI-powered career toolkit. Land your dream job faster.")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class='price-card'>
            <span class='free-badge'>FREE</span>
            <h3>Starter</h3>
            <h2 style='color: #2EC4B6;'>₹0</h2>
            <p>✅ 3 Resume Analyses</p>
            <p>✅ 1 Mock Interview</p>
            <p>✅ Basic Cover Letter</p>
            <p>❌ JD Analyzer</p>
            <p>❌ LinkedIn Review</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("**Current Plan ✓**" if st.session_state.plan == "free" else "")

    with col2:
        st.markdown("""
        <div class='price-card'>
            <span class='paid-badge'>BASIC</span>
            <h3>Professional</h3>
            <h2 style='color: #00ffff;'>₹49</h2>
            <p style='color: #aaa;'>one-time payment</p>
            <p>✅ 10 Resume Analyses</p>
            <p>✅ 5 Mock Interviews</p>
            <p>✅ Cover Letters</p>
            <p>✅ JD Analyzer</p>
            <p>❌ LinkedIn Review</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Get Basic — ₹49", use_container_width=True):
            with st.spinner("Creating payment link..."):
                link = create_payment_link(49, "Aura Career AI — Basic Plan", "basic")
                if link:
                    st.markdown(f"### 👉 [Click here to pay ₹49]({link})")

    with col3:
        st.markdown("""
        <div class='price-card'>
            <span class='paid-badge'>PRO</span>
            <h3>Elite</h3>
            <h2 style='color: #E94E77;'>₹199</h2>
            <p style='color: #aaa;'>one-time payment</p>
            <p>✅ Unlimited Everything</p>
            <p>✅ LinkedIn Reviewer</p>
            <p>✅ Priority AI</p>
            <p>✅ Download Reports</p>
            <p>✅ Early Access Features</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Get Pro — ₹199", use_container_width=True):
            with st.spinner("Creating payment link..."):
                link = create_payment_link(199, "Aura Career AI — Pro Plan", "pro")
                if link:
                    st.markdown(f"### 👉 [Click here to pay ₹199]({link})")

    st.markdown("---")
    st.markdown("### 📊 Your Usage")
    col1, col2, col3 = st.columns(3)
    col1.metric("Plan", st.session_state.plan.upper())
    col2.metric("Resume Analyses Used", st.session_state.usage.get("resume", 0))
    col3.metric("Interviews Used", st.session_state.usage.get("interview", 0))


# ══════════════════════════════════════════
# RESUME ANALYZER
# ══════════════════════════════════════════
elif "Resume" in feature:
    st.subheader("📄 Resume Analyzer & ATS Score")

    if not check_limit("resume", 3):
        show_payment_wall("Resume Analyzer")
    else:
        remaining = 3 - st.session_state.usage.get("resume", 0) if st.session_state.plan == "free" else "Unlimited"
        st.caption(f"Analyses remaining: **{remaining}**")

        col1, col2 = st.columns(2)
        with col1:
            resume_file = st.file_uploader("📎 Upload Resume (PDF)", type=["pdf"])
            resume_text = ""
            if resume_file:
                resume_text = read_pdf(resume_file)
                st.success(f"✅ Resume loaded — {len(resume_text)} characters")
        with col2:
            job_desc = st.text_area("📋 Paste Job Description", height=180,
                                     placeholder="Paste the job description...")

        experience = st.selectbox("Experience Level", [
            "Fresher (0-1 years)", "Junior (1-3 years)",
            "Mid-level (3-6 years)", "Senior (6+ years)"
        ])

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            ats_btn = st.button("🎯 Get ATS Score", use_container_width=True)
        with col_b:
            improve_btn = st.button("✨ Improve Resume", use_container_width=True)
        with col_c:
            gaps_btn = st.button("🔍 Skill Gaps", use_container_width=True)

        if ats_btn:
            if not resume_text:
                st.warning("Please upload your resume!")
            elif not job_desc.strip():
                st.warning("Please paste the job description!")
            else:
                with st.spinner("Analyzing..."):
                    system = "You are an expert ATS and HR consultant for Indian job market."
                    prompt = f"""Analyze resume vs job description:
1. **ATS SCORE: XX/100**
2. **Keyword Match** — matched and missing keywords
3. **Strengths** — 3-4 points
4. **Critical Issues** — 3-4 must-fix points
5. **Quick Wins** — 3 immediate improvements
6. **Section Ratings** — Contact, Summary, Experience, Skills, Education

Experience: {experience}
RESUME: {resume_text}
JOB DESCRIPTION: {job_desc}"""
                    result = groq_ask(system, prompt)
                    increment_usage("resume")
                    st.markdown(result)
                    st.download_button("⬇ Download Analysis", result,
                                       file_name="resume_analysis.txt", mime="text/plain")

        if improve_btn:
            if not resume_text:
                st.warning("Please upload your resume!")
            else:
                with st.spinner("Rewriting resume..."):
                    system = "You are an expert resume writer for Indian job market."
                    prompt = f"""Rewrite this resume to be more powerful and ATS-friendly.
Experience: {experience}
Job Target: {job_desc[:300] if job_desc else 'General'}
RESUME: {resume_text}

Rewrite with strong action verbs, quantified achievements, ATS keywords."""
                    result = groq_ask(system, prompt, temperature=0.4)
                    increment_usage("resume")
                    st.markdown(result)
                    st.download_button("⬇ Download Improved Resume", result,
                                       file_name="improved_resume.txt", mime="text/plain")

        if gaps_btn:
            if not resume_text or not job_desc.strip():
                st.warning("Upload resume and paste JD!")
            else:
                with st.spinner("Finding gaps..."):
                    system = "You are a career counselor for Indian tech job market."
                    prompt = f"""Find skill gaps:
1. Missing Technical Skills
2. Missing Soft Skills
3. Experience Gaps
4. Certifications Needed
5. Learning Roadmap (free Indian resources)

RESUME: {resume_text}
JOB DESCRIPTION: {job_desc}"""
                    result = groq_ask(system, prompt)
                    st.markdown(result)


# ══════════════════════════════════════════
# MOCK INTERVIEW
# ══════════════════════════════════════════
elif "Interview" in feature:
    st.subheader("🎯 AI Mock Interview")

    if not check_limit("interview", 1):
        show_payment_wall("Mock Interview")
    else:
        remaining = 1 - st.session_state.usage.get("interview", 0) if st.session_state.plan == "free" else "Unlimited"
        st.caption(f"Interviews remaining: **{remaining}**")

        col1, col2 = st.columns(2)
        with col1:
            interview_type = st.selectbox("Interview Type", [
                "HR Round", "Technical Round", "Behavioural Round",
                "Managerial Round", "Campus Placement",
            ])
        with col2:
            company_type = st.selectbox("Company Type", [
                "Indian IT (TCS/Infosys/Wipro)", "Product Startup",
                "MNC", "Banking/Finance", "General",
            ])

        job_role = st.text_input("Job Role", placeholder="Python Developer, ML Engineer...")
        resume_summary = st.text_area("Resume Summary (optional)", height=80)

        if "interview_questions" not in st.session_state:
            st.session_state.interview_questions = []
            st.session_state.current_q = 0
            st.session_state.interview_answers = []
            st.session_state.interview_started = False

        if st.button("🚀 Start Interview", use_container_width=True):
            with st.spinner("Preparing questions..."):
                system = "You are an expert interviewer from top Indian companies."
                prompt = f"""Generate 5 interview questions for:
Role: {job_role}
Type: {interview_type}
Company: {company_type}
Background: {resume_summary if resume_summary else 'Not provided'}

Return ONLY 5 questions numbered 1-5."""
                result = groq_ask(system, prompt, temperature=0.6)
                questions = [q.strip() for q in result.split('\n') if q.strip() and q[0].isdigit()]
                st.session_state.interview_questions = questions[:5]
                st.session_state.current_q = 0
                st.session_state.interview_answers = []
                st.session_state.interview_started = True
                increment_usage("interview")
                st.rerun()

        if st.session_state.interview_started and st.session_state.interview_questions:
            total = len(st.session_state.interview_questions)
            current = st.session_state.current_q

            if current < total:
                st.markdown("---")
                st.progress(current / total)
                st.caption(f"Question {current + 1} of {total}")
                question = st.session_state.interview_questions[current]
                st.markdown(f"### ❓ {question}")
                answer = st.text_area("Your Answer", height=150, key=f"answer_{current}")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Submit & Get Feedback", use_container_width=True):
                        if answer.strip():
                            with st.spinner("Evaluating..."):
                                system = "You are an expert interviewer. Give constructive feedback."
                                prompt = f"""Evaluate:
Question: {question}
Role: {job_role}
Answer: {answer}

Give:
1. Score: X/10
2. What was good
3. What was missing
4. Ideal answer includes
5. One tip"""
                                feedback = groq_ask(system, prompt)
                                st.session_state.interview_answers.append({
                                    "question": question,
                                    "answer": answer,
                                    "feedback": feedback
                                })
                                st.info(feedback)
                                st.session_state.current_q += 1
                with col2:
                    if st.button("⏭ Skip", use_container_width=True):
                        st.session_state.current_q += 1
                        st.rerun()
            else:
                st.success("🎉 Interview Complete!")
                with st.spinner("Generating report..."):
                    all_qa = "\n\n".join([
                        f"Q: {i['question']}\nA: {i['answer']}\nFeedback: {i['feedback']}"
                        for i in st.session_state.interview_answers
                    ])
                    system = "You are a career coach."
                    prompt = f"""Final performance report:
{all_qa}

Include:
1. Overall Score: X/10
2. Top 3 Strengths
3. Top 3 Areas to improve
4. Ready for interview? Yes/No/Almost
5. 3 things to practice"""
                    final = groq_ask(system, prompt)
                    st.markdown(final)
                    st.download_button("⬇ Download Report",
                                       f"INTERVIEW REPORT\n\n{all_qa}\n\nFINAL:\n{final}",
                                       file_name="interview_report.txt", mime="text/plain")

                if st.button("🔄 New Interview"):
                    for key in ["interview_questions", "current_q", "interview_answers", "interview_started"]:
                        del st.session_state[key]
                    st.rerun()


# ══════════════════════════════════════════
# COVER LETTER
# ══════════════════════════════════════════
elif "Cover Letter" in feature:
    st.subheader("📝 Cover Letter Generator")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Your Name", placeholder="Rupal Darode")
        job_title = st.text_input("Job Title", placeholder="Python Developer")
        company = st.text_input("Company Name", placeholder="TCS, Google...")
    with col2:
        experience_years = st.text_input("Years of Experience", placeholder="4")
        key_skills = st.text_input("Top 3 Skills", placeholder="Python, ML, Streamlit")
        tone = st.selectbox("Tone", ["Professional", "Enthusiastic", "Formal", "Creative"])

    resume_text = st.text_area("Resume Summary", height=100)
    job_desc = st.text_area("Job Description", height=100)

    if st.button("✍ Generate Cover Letter", use_container_width=True):
        if name and job_title and company:
            with st.spinner("Writing..."):
                system = "You are an expert cover letter writer for Indian job market."
                prompt = f"""Write a {tone} cover letter:
Name: {name} | Role: {job_title} at {company}
Experience: {experience_years} years | Skills: {key_skills}
Background: {resume_text}
JD: {job_desc}

3-paragraph letter: strong hook, relevant experience, confident close."""
                result = groq_ask(system, prompt, temperature=0.7)
                st.markdown(result)
                st.download_button("⬇ Download", result,
                                   file_name=f"cover_letter_{company}.txt", mime="text/plain")
        else:
            st.warning("Fill Name, Job Title and Company!")


# ══════════════════════════════════════════
# JD ANALYZER
# ══════════════════════════════════════════
elif "Job Description" in feature:
    st.subheader("💼 Job Description Analyzer")
    job_desc = st.text_area("Paste Job Description", height=200)
    your_profile = st.text_area("Your Profile (for fit check)", height=80)

    col1, col2, col3 = st.columns(3)
    with col1:
        decode_btn = st.button("🔍 Decode JD", use_container_width=True)
    with col2:
        salary_btn = st.button("💰 Salary Estimate", use_container_width=True)
    with col3:
        fit_btn = st.button("✅ Am I a Fit?", use_container_width=True)

    if decode_btn and job_desc.strip():
        with st.spinner("Decoding..."):
            result = groq_ask(
                "You are an expert HR consultant.",
                f"""Decode this JD:
1. Must-Have Skills
2. Good-to-Have Skills
3. Red Flags
4. Company Culture Hints
5. Real Role vs Title
6. Ideal Candidate Profile
7. Interview Prep Tips

JD: {job_desc}"""
            )
            st.markdown(result)

    if salary_btn and job_desc.strip():
        with st.spinner("Estimating..."):
            result = groq_ask(
                "You are an expert in Indian job market salaries.",
                f"Salary range (LPA), negotiation tips, benefits to ask for this role:\n{job_desc}"
            )
            st.info(result)

    if fit_btn:
        if not job_desc.strip() or not your_profile.strip():
            st.warning("Fill both JD and your profile!")
        else:
            with st.spinner("Checking fit..."):
                result = groq_ask(
                    "You are a brutally honest career advisor.",
                    f"""Fit analysis:
CANDIDATE: {your_profile}
JD: {job_desc}

1. Fit Score: XX%
2. Should apply? Yes/No/Maybe
3. Matching points
4. Gap points
5. How to position yourself"""
                )
                st.markdown(result)


# ══════════════════════════════════════════
# LINKEDIN REVIEWER
# ══════════════════════════════════════════
elif "LinkedIn" in feature:
    if st.session_state.plan == "free":
        st.warning("⚠️ LinkedIn Reviewer is a paid feature!")
        show_payment_wall("LinkedIn Reviewer")
    else:
        st.subheader("🔗 LinkedIn Profile Reviewer")
        col1, col2 = st.columns(2)
        with col1:
            current_role = st.text_input("Current Role", placeholder="AI/ML Developer")
            target_role = st.text_input("Target Role", placeholder="Senior ML Engineer")
        with col2:
            experience = st.text_input("Years of Experience", placeholder="4")
            industry = st.text_input("Industry", placeholder="IT/Software")

        headline = st.text_input("Current LinkedIn Headline")
        summary = st.text_area("LinkedIn About Section", height=120)
        skills_list = st.text_area("Your Skills", height=60, placeholder="Python, ML, Streamlit...")

        if st.button("🔍 Review Profile", use_container_width=True):
            if current_role and headline:
                with st.spinner("Reviewing..."):
                    result = groq_ask(
                        "You are a LinkedIn expert and recruiter for Indian tech industry.",
                        f"""Review LinkedIn profile:
Role: {current_role} → {target_role}
Experience: {experience} | Industry: {industry}
Headline: {headline}
Summary: {summary}
Skills: {skills_list}

1. Profile Score: XX/100
2. 3 Optimized Headline Options
3. Rewritten About Section
4. Skills to Add/Remove
5. 5 Tips to get more recruiter views
6. SEO Keywords to add"""
                    )
                    st.markdown(result)
                    st.download_button("⬇ Download", result,
                                       file_name="linkedin_review.txt", mime="text/plain")
            else:
                st.warning("Fill Current Role and Headline!")


# ── FOOTER ──
st.markdown("---")
st.markdown(
    "<center style='color: #555; font-size: 12px;'>Built with ❤️ by Rupal Darode | Aura Career AI 🎯 | Powered by Groq + Razorpay</center>",
    unsafe_allow_html=True
)
