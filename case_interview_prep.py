import os
import streamlit as st
import google.generativeai as genai
import json

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Case Interview Coach",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@700&display=swap');

  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

  .hero-title {
      font-family: 'Playfair Display', serif;
      font-size: 2.6rem;
      font-weight: 700;
      color: #1a1a2e;
      line-height: 1.2;
      margin-bottom: 0.25rem;
  }
  .hero-sub {
      font-size: 1.05rem;
      color: #5a6072;
      margin-bottom: 2rem;
  }

  /* Step pill */
  .step-pill {
      display: inline-block;
      background: #1a1a2e;
      color: #ffffff;
      font-size: 0.72rem;
      font-weight: 600;
      letter-spacing: 0.06em;
      padding: 3px 10px;
      border-radius: 20px;
      margin-bottom: 8px;
  }
  .step-title {
      font-size: 1.25rem;
      font-weight: 700;
      color: #1a1a2e;
      margin-bottom: 0.35rem;
  }
  .step-desc {
      font-size: 0.93rem;
      color: #4a5568;
      line-height: 1.6;
  }
  .hint-box {
      background: #f0f4ff;
      border-left: 4px solid #4361ee;
      border-radius: 6px;
      padding: 12px 16px;
      font-size: 0.88rem;
      color: #1a1a2e !important;
      margin-top: 10px;
  }
  .case-card {
      background: #f8f9fc;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 20px 24px;
      margin-bottom: 16px;
  }
  .case-tag {
      background: #e8edff;
      color: #3b52cc;
      font-size: 0.75rem;
      font-weight: 600;
      padding: 3px 9px;
      border-radius: 20px;
      margin-right: 6px;
  }
  .feedback-good {
      background: #f0fff4;
      border-left: 4px solid #38a169;
      border-radius: 6px;
      padding: 14px 18px;
      margin-top: 12px;
      color: #1a1a2e !important;
  }
  .feedback-improve {
      background: #fff8f0;
      border-left: 4px solid #ed8936;
      border-radius: 6px;
      padding: 14px 18px;
      margin-top: 12px;
      color: #1a1a2e !important;
  }
  .feedback-wrong {
      background: #fff5f5;
      border-left: 4px solid #e53e3e;
      border-radius: 6px;
      padding: 14px 18px;
      margin-top: 12px;
      color: #1a1a2e !important;
  }
  
  /* Forzar color oscuro en los textos y listas dentro de los recuadros de feedback */
  .feedback-good *, .feedback-improve *, .feedback-wrong *, .hint-box * {
      color: #1a1a2e !important;
  }

  .score-badge {
      font-size: 2rem;
      font-weight: 700;
      color: #1a1a2e;
  }
  .progress-bar-bg {
      background: #e2e8f0;
      border-radius: 99px;
      height: 8px;
      margin-top: 8px;
  }
  .stButton > button {
      border-radius: 8px;
      font-weight: 600;
  }
  [data-testid="stSidebar"] { background: #1a1a2e !important; }
  [data-testid="stSidebar"] * { color: #e2e8f0 !important; }
  [data-testid="stSidebar"] .stSelectbox label,
  [data-testid="stSidebar"] .stMarkdown { color: #a0aec0 !important; }
</style>
""", unsafe_allow_html=True)

# ── Business case library ─────────────────────────────────────────────────────
CASES = {
    "📦 Profitability Drop – RetailCo": {
        "industry": "Retail",
        "difficulty": "Medium",
        "context": """
**Company:** RetailCo, a mid-size brick-and-mortar chain with 300 stores across Mexico.
**Situation:** Over the past 18 months, net profit margin has fallen from 12% to 6%.
Revenue is flat. Leadership suspects rising costs, but has not identified the root cause.
Your role is to diagnose the problem and recommend a clear action plan.
        """,
        "steps": [
            {
                "title": "Clarify & structure the problem",
                "prompt": "Before diving in, what clarifying questions would you ask the client? Then outline your overall framework for diagnosing a profitability problem.",
                "hint": "Think about Revenue vs. Cost breakdown. Ask about time period, geography, product mix, and any recent changes. A good structure could be: Revenue → Volume & Price, Cost → Fixed & Variable.",
                "ideal_topics": ["revenue vs cost split", "framework", "clarifying questions", "time period", "geography"],
            },
            {
                "title": "Revenue analysis",
                "prompt": "Assume revenue is flat — no growth, no decline. Walk me through how you would analyze whether the revenue side is contributing to the margin compression.",
                "hint": "Even flat revenue can hide issues: mix shift toward lower-margin products, price erosion, or channel changes. Explore: price × volume per segment.",
                "ideal_topics": ["product mix", "price", "volume", "channel", "segment"],
            },
            {
                "title": "Cost deep-dive",
                "prompt": "The data shows COGS increased by 3 pp and SG&A by another 3 pp over 18 months. How would you break this down and identify the culprit(s)?",
                "hint": "Split COGS: raw materials, labor, logistics. Split SG&A: store rent, headcount, marketing. Ask whether costs are fixed vs variable and if they scale with revenue.",
                "ideal_topics": ["COGS", "SG&A", "fixed vs variable", "labor", "rent", "logistics"],
            },
            {
                "title": "Root cause & hypothesis",
                "prompt": "You discover: store count grew 15% but same-store sales were flat, and new stores are underperforming. State your root-cause hypothesis clearly.",
                "hint": "The classic 'over-expansion' trap: fixed costs (rent, staff) rose faster than revenue contribution from new stores. State this as a clear, data-backed hypothesis.",
                "ideal_topics": ["over-expansion", "fixed costs", "new store performance", "hypothesis", "data-backed"],
            },
            {
                "title": "Recommendations",
                "prompt": "Based on your hypothesis, give 2–3 concrete, prioritized recommendations. Be specific about what to do, expected impact, and risks.",
                "hint": "Think: halt new openings / close underperforming stores, optimize the store footprint model before expanding, and improve new-store ramp-up playbook.",
                "ideal_topics": ["prioritized", "specific actions", "expected impact", "risks", "quick wins vs long-term"],
            },
        ],
    },

    "🚀 Market Entry – EdTech Startup": {
        "industry": "EdTech",
        "difficulty": "Hard",
        "context": """
**Company:** LearnSpark, a well-funded EdTech startup that offers AI-powered tutoring in the US.
**Situation:** They want to enter the Mexican market within 12 months.
The CEO asks: *Should we enter Mexico, and if so, how?*
        """,
        "steps": [
            {
                "title": "Structure the market entry question",
                "prompt": "What is your overall framework for deciding whether to enter a new market? List the key dimensions you'd analyze.",
                "hint": "Classic market entry: Market attractiveness (size, growth, competition) + Company fit (capabilities, cost, risk) + Entry strategy (how: organic, JV, acquisition).",
                "ideal_topics": ["market size", "competition", "company fit", "entry mode", "framework"],
            },
            {
                "title": "Market sizing",
                "prompt": "Estimate the addressable market for AI tutoring in Mexico. Walk me through your math step by step.",
                "hint": "Use a top-down or bottom-up approach. E.g., Mexico population → school-age children → those with internet access → willingness to pay → price per seat → TAM.",
                "ideal_topics": ["population", "school-age", "internet penetration", "willingness to pay", "TAM", "assumption transparency"],
            },
            {
                "title": "Competitive landscape",
                "prompt": "Who are the likely competitors in Mexico and how would you assess competitive intensity?",
                "hint": "Local players (Kumon, local tutoring), regional (Duolingo in language), global EdTech. Use Porter's 5 forces or a simpler: Existing players + threat of substitutes + buyer power.",
                "ideal_topics": ["local competitors", "global players", "differentiation", "barriers", "substitutes"],
            },
            {
                "title": "Entry strategy recommendation",
                "prompt": "Should LearnSpark enter Mexico? If yes, how — organic build, partnership, or acquisition? Defend your recommendation.",
                "hint": "Given the 12-month window, a partnership with a local player (school district, publisher, telco) is typically faster and lower-risk than organic. State your reasoning clearly.",
                "ideal_topics": ["yes/no recommendation", "partnership", "timeline", "risk", "rationale"],
            },
            {
                "title": "Risks & next steps",
                "prompt": "What are the top 3 risks and what immediate next steps would you propose?",
                "hint": "Risks: regulatory, localization/language, competition from incumbents, unit economics. Next steps: pilot in one city, sign a distribution partner, hire local GM.",
                "ideal_topics": ["risks", "mitigation", "pilot", "immediate actions", "KPIs"],
            },
        ],
    },

    "🏭 Operations – ManufactureCo Efficiency": {
        "industry": "Manufacturing",
        "difficulty": "Easy",
        "context": """
**Company:** ManufactureCo, an automotive parts supplier in Guadalajara.
**Situation:** On-time delivery rate fell from 95% to 78% in Q2.
Customers are threatening to switch suppliers. Diagnose and fix.
        """,
        "steps": [
            {
                "title": "Frame the operations problem",
                "prompt": "How do you structure an operations diagnostic? What are the first questions you'd ask?",
                "hint": "Think along the supply chain: Inputs → Process → Output → Delivery. Clarify: Is this a demand spike or supply failure? Internal or external bottleneck?",
                "ideal_topics": ["supply chain", "framework", "internal vs external", "clarifying questions"],
            },
            {
                "title": "Root cause analysis",
                "prompt": "Data shows: machine downtime up 20%, supplier delays on 2 key components. How do you prioritize and go deeper?",
                "hint": "Use the 80/20 rule. Which downtime issues cause the most delays? Which components have the longest impact? Build an issue tree.",
                "ideal_topics": ["80/20", "prioritization", "machine downtime", "supplier delays", "issue tree"],
            },
            {
                "title": "Short-term fix",
                "prompt": "The client needs improvement within 30 days. What would you recommend?",
                "hint": "Quick wins: emergency supplier diversification, predictive maintenance schedule, buffer inventory for critical parts. Don't over-engineer.",
                "ideal_topics": ["quick wins", "30 days", "supplier", "inventory buffer", "maintenance"],
            },
            {
                "title": "Long-term solution",
                "prompt": "What structural changes would you recommend to prevent recurrence?",
                "hint": "Systemic fixes: supplier SLAs with penalties, IoT-based predictive maintenance, demand forecasting improvements, safety stock policy.",
                "ideal_topics": ["systemic", "SLAs", "predictive maintenance", "forecasting", "structural"],
            },
            {
                "title": "Measuring success",
                "prompt": "How would you measure whether your recommendations are working? Define 3 KPIs.",
                "hint": "Good KPIs are leading AND lagging. E.g., machine uptime % (leading), on-time delivery % (lagging), supplier lead-time variance (leading).",
                "ideal_topics": ["KPIs", "leading indicators", "lagging indicators", "on-time delivery", "measurement"],
            },
        ],
    },
}

# ── Gemini client ─────────────────────────────────────────────────────────────
@st.cache_resource
def configure_gemini():
    api_key = (
        os.environ.get("GEMINI_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or (st.secrets.get("GEMINI_API_KEY") if hasattr(st, "secrets") else None)
        or (st.secrets.get("OPENAI_API_KEY") if hasattr(st, "secrets") else None)
    )
    if api_key:
        genai.configure(api_key=api_key)

@st.cache_data
def get_gemini_models():
    """Busca dinámicamente las diferentes modalidades/modelos disponibles de Gemini"""
    configure_gemini()
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        return models if models else ["models/gemini-1.5-flash", "models/gemini-1.5-pro"]
    except Exception:
        # Fallback en caso de que aún no se haya ingresado la API Key o haya un error
        return ["models/gemini-1.5-flash", "models/gemini-1.5-pro"]

def get_client(model_name="models/gemini-1.5-flash"):
    configure_gemini()
    return genai.GenerativeModel(model_name)

def analyze_answer(case_name, step, user_answer, case_context, model_name):
    """Call Gemini to evaluate the user's answer and give structured feedback."""
    model = get_client(model_name)

    prompt = f"""You are an expert management consulting interview coach with 15 years of experience at McKinsey, BCG, and Bain.
You evaluate candidates' answers to case interview questions and give precise, actionable feedback.
Always respond ONLY in JSON with this exact structure, no extra text, no markdown fences:
{{
  "score": <integer 1-10>,
  "verdict": "<Excellent|Good|Needs Work|Incomplete>",
  "strengths": ["<strength 1>", "<strength 2>"],
  "gaps": ["<gap 1>", "<gap 2>"],
  "model_answer_summary": "<2-3 sentence ideal answer>",
  "coaching_tip": "<one specific, actionable tip for improvement>"
}}
Be specific, honest, and constructive. Score 8+ only for genuinely strong answers.

CASE: {case_name}
CASE CONTEXT: {case_context}

STEP: {step['title']}
QUESTION: {step['prompt']}

CANDIDATE'S ANSWER:
{user_answer}

Evaluate this answer. Be rigorous but fair. Respond ONLY with the JSON object.
"""

    response = model.generate_content(prompt)
    raw = response.text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
    return json.loads(raw)


# ── Session state init ────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "selected_case": None,
        "current_step": 0,
        "answers": {},
        "feedbacks": {},
        "show_hint": {},
        "session_complete": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 Case Interview Coach")
    
    st.markdown("---")
    st.markdown("**Configuración de IA:**")
    available_models = get_gemini_models()
    # Intenta seleccionar el modelo 'flash' por defecto para mayor rapidez si está disponible
    default_idx = 0
    for i, m in enumerate(available_models):
        if "flash" in m.lower():
            default_idx = i
            break
    selected_model = st.selectbox("Modalidad de Gemini:", available_models, index=default_idx)

    st.markdown("---")
    st.markdown("**Select a business case:**")

    for case_name, case_data in CASES.items():
        diff_color = {"Easy": "🟢", "Medium": "🟡", "Hard": "🔴"}.get(case_data["difficulty"], "⚪")
        label = f"{case_name} {diff_color}"
        if st.button(label, key=f"btn_{case_name}", use_container_width=True):
            st.session_state.selected_case = case_name
            st.session_state.current_step = 0
            st.session_state.answers = {}
            st.session_state.feedbacks = {}
            st.session_state.show_hint = {}
            st.session_state.session_complete = False

    st.markdown("---")
    if st.session_state.selected_case:
        case = CASES[st.session_state.selected_case]
        n_steps = len(case["steps"])
        answered = len(st.session_state.feedbacks)
        st.markdown(f"**Progress:** {answered}/{n_steps} steps")
        pct = int((answered / n_steps) * 100)
        st.progress(pct / 100)

        if st.session_state.feedbacks:
            scores = [f["score"] for f in st.session_state.feedbacks.values()]
            avg = sum(scores) / len(scores)
            st.markdown(f"**Avg score:** {avg:.1f} / 10")

    st.markdown("---")
    st.markdown("**Tips for case interviews:**")
    st.markdown("""
- 🗣️ Think out loud — always
- 🔢 Structure before diving in
- 📐 Use frameworks, then adapt
- ❓ Ask clarifying questions
- 🎯 Lead with the answer (Pyramid Principle)
    """)


# ── Main area ─────────────────────────────────────────────────────────────────
if not st.session_state.selected_case:
    # Landing screen
    st.markdown('<p class="hero-title">Case Interview Coach</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-sub">AI-powered practice with real-time feedback. Pick a case from the sidebar to begin.</p>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    for col, (name, data) in zip([col1, col2, col3], CASES.items()):
        with col:
            diff_color = {"Easy": "#38a169", "Medium": "#d69e2e", "Hard": "#e53e3e"}.get(data["difficulty"])
            st.markdown(f"""
<div class="case-card">
  <div>
    <span class="case-tag">{data['industry']}</span>
    <span style="font-size:0.75rem;font-weight:600;color:{diff_color};">{data['difficulty']}</span>
  </div>
  <p style="font-size:1.05rem;font-weight:700;color:#1a1a2e;margin:10px 0 6px;">{name}</p>
  <p style="font-size:0.85rem;color:#5a6072;">{len(data['steps'])} steps · AI-graded answers</p>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### How it works")
    col_a, col_b, col_c, col_d = st.columns(4)
    for col, emoji, title, desc in [
        (col_a, "1️⃣", "Pick a case", "Choose from 3 real-world business scenarios."),
        (col_b, "2️⃣", "Read the brief", "Understand the situation like a real consultant."),
        (col_c, "3️⃣", "Answer each step", "Work through the case step by step."),
        (col_d, "4️⃣", "Get AI feedback", "Gemini grades your answer and gives coaching."),
    ]:
        with col:
            st.markdown(f"**{emoji} {title}**")
            st.caption(desc)

else:
    # Case session
    case_name = st.session_state.selected_case
    case = CASES[case_name]
    steps = case["steps"]
    n_steps = len(steps)
    current = st.session_state.current_step

    # Header
    st.markdown(f'<p class="hero-title">{case_name}</p>', unsafe_allow_html=True)
    diff = case["difficulty"]
    diff_color = {"Easy": "#38a169", "Medium": "#d69e2e", "Hard": "#e53e3e"}.get(diff, "#718096")
    st.markdown(
        f'<span class="case-tag">{case["industry"]}</span>'
        f'<span style="font-size:0.8rem;font-weight:600;color:{diff_color};margin-left:4px;">{diff}</span>',
        unsafe_allow_html=True,
    )

    # Context box
    with st.expander("📋 Case brief (click to expand / collapse)", expanded=(current == 0)):
        st.markdown(case["context"])

    st.markdown("---")

    # Step tabs
    tab_labels = [f"Step {i+1}" for i in range(n_steps)]
    tabs = st.tabs(tab_labels)

    for i, (tab, step) in enumerate(zip(tabs, steps)):
        with tab:
            # Status indicator
            if i in st.session_state.feedbacks:
                score = st.session_state.feedbacks[i]["score"]
                color = "#38a169" if score >= 7 else ("#d69e2e" if score >= 5 else "#e53e3e")
                status = f"✅ Scored: **{score}/10**"
            elif i == current:
                color = "#4361ee"
                status = "▶ Current step"
            else:
                color = "#a0aec0"
                status = "🔒 Complete previous steps first"

            st.markdown(f'<div class="step-pill">STEP {i+1} OF {n_steps}</div>', unsafe_allow_html=True)
            st.markdown(f'<p class="step-title">{step["title"]}</p>', unsafe_allow_html=True)
            st.markdown(f"<span style='color:{color};font-size:0.85rem;'>{status}</span>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

            # Question
            st.markdown(f'<p class="step-desc">📝 <strong>Question:</strong> {step["prompt"]}</p>', unsafe_allow_html=True)

            # Hint toggle
            hint_key = f"hint_{i}"
            if st.button("💡 Show hint", key=hint_key):
                st.session_state.show_hint[i] = not st.session_state.show_hint.get(i, False)

            if st.session_state.show_hint.get(i, False):
                st.markdown(f'<div class="hint-box">💡 <strong>Hint:</strong> {step["hint"]}</div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Answer area — only active for current step
            if i <= current:
                answer_key = f"answer_{i}"
                existing_answer = st.session_state.answers.get(i, "")

                if i not in st.session_state.feedbacks:
                    user_answer = st.text_area(
                        "Your answer:",
                        value=existing_answer,
                        height=160,
                        key=answer_key,
                        placeholder="Structure your answer clearly. Think out loud. Use frameworks.",
                    )
                    st.session_state.answers[i] = user_answer

                    col_submit, col_clear = st.columns([2, 1])
                    with col_submit:
                        if st.button("🧠 Analyze my answer", key=f"submit_{i}", type="primary"):
                            if len(user_answer.strip()) < 30:
                                st.warning("Please write a more complete answer before submitting (at least a sentence or two).")
                            else:
                                with st.spinner("Coach is reviewing your answer..."):
                                    try:
                                        feedback = analyze_answer(case_name, step, user_answer, case["context"], selected_model)
                                        st.session_state.feedbacks[i] = feedback
                                        # Advance to next step
                                        if i == current and current < n_steps - 1:
                                            st.session_state.current_step = current + 1
                                        elif i == current and current == n_steps - 1:
                                            st.session_state.session_complete = True
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error analyzing answer: {e}")
                else:
                    # Already answered — show answer as read-only
                    st.markdown(f"**Your answer:**")
                    st.info(st.session_state.answers.get(i, ""))

                # Show feedback if available
                if i in st.session_state.feedbacks:
                    fb = st.session_state.feedbacks[i]
                    score = fb["score"]
                    verdict = fb["verdict"]

                    css_class = "feedback-good" if score >= 7 else ("feedback-improve" if score >= 5 else "feedback-wrong")
                    score_emoji = "🌟" if score >= 8 else ("✅" if score >= 7 else ("⚠️" if score >= 5 else "❌"))

                    st.markdown("---")
                    st.markdown("### 🎓 Coach Feedback")

                    col_score, col_verdict = st.columns([1, 3])
                    with col_score:
                        st.markdown(f'<p class="score-badge">{score_emoji} {score}/10</p>', unsafe_allow_html=True)
                    with col_verdict:
                        st.markdown(f"**Verdict:** {verdict}")
                        bar_color = "#38a169" if score >= 7 else ("#d69e2e" if score >= 5 else "#e53e3e")
                        st.markdown(
                            f'<div class="progress-bar-bg"><div style="width:{score*10}%;background:{bar_color};height:8px;border-radius:99px;"></div></div>',
                            unsafe_allow_html=True,
                        )

                    col_s, col_g = st.columns(2)
                    with col_s:
                        st.markdown(f'<div class="{css_class}"><strong>✅ Strengths</strong><ul>' +
                                    "".join(f"<li>{s}</li>" for s in fb["strengths"]) +
                                    "</ul></div>", unsafe_allow_html=True)
                    with col_g:
                        st.markdown(f'<div class="{css_class.replace("good", "improve")}"><strong>⚠️ Gaps / To improve</strong><ul>' +
                                    "".join(f"<li>{g}</li>" for g in fb["gaps"]) +
                                    "</ul></div>", unsafe_allow_html=True)

                    # Se agregó color explícito #1a1a2e aquí también para prevenir invisibilidad en modo oscuro
                    st.markdown(f"""
<div style="background:#f0f4ff;border-left:4px solid #4361ee;border-radius:6px;padding:12px 16px;font-size:0.88rem;margin-top:14px;color:#1a1a2e !important;">
  <strong>📌 Model answer:</strong> {fb['model_answer_summary']}
</div>
<div style="background:#f7f3ff;border-left:4px solid #805ad5;border-radius:6px;padding:12px 16px;margin-top:10px;font-size:0.88rem;color:#1a1a2e !important;">
  <strong>🎯 Coaching tip:</strong> {fb['coaching_tip']}
</div>
""", unsafe_allow_html=True)

            else:
                st.markdown('<p style="color:#a0aec0;font-style:italic;">Complete previous steps to unlock this one.</p>', unsafe_allow_html=True)

    # Session complete summary
    if st.session_state.session_complete and len(st.session_state.feedbacks) == n_steps:
        st.markdown("---")
        st.markdown("## 🏁 Case Complete!")

        scores = [st.session_state.feedbacks[i]["score"] for i in range(n_steps)]
        avg = sum(scores) / len(scores)
        overall = "Outstanding" if avg >= 8 else ("Strong" if avg >= 6.5 else ("Developing" if avg >= 5 else "Needs Practice"))

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Average Score", f"{avg:.1f}/10")
        with col2:
            st.metric("Steps Completed", f"{n_steps}/{n_steps}")
        with col3:
            st.metric("Overall Rating", overall)

        st.markdown("### Score breakdown")
        step_names = [s["title"] for s in steps]
        chart_data = {"Step": step_names, "Score": scores}
        import pandas as pd
        df = pd.DataFrame(chart_data)
        st.bar_chart(df.set_index("Step"))

        if st.button("🔄 Restart this case", type="primary"):
            st.session_state.current_step = 0
            st.session_state.answers = {}
            st.session_state.feedbacks = {}
            st.session_state.show_hint = {}
            st.session_state.session_complete = False
            st.rerun()
