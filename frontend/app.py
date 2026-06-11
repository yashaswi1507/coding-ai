import streamlit as st
import requests
import time
import os 

BASE = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")
USER_ID = "guest"

st.set_page_config(page_title="ThinkCode AI", layout="wide", page_icon="🧠")

def api(endpoint, method="GET", data=None):
    try:
        if method == "POST":
            return requests.post(f"{BASE}{endpoint}", json=data, timeout=10).json()
        return requests.get(f"{BASE}{endpoint}", timeout=5).json()
    except:
        return None

# ── Session State ─────────────────────────────────────────────────────────────
for key, val in {
    "result": None, "hint_level": 0, "timer_running": False,
    "timer_start": None, "timer_seconds": 0, "timer_done": False,
    "active_tab": "Solve"
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🧠 ThinkCode AI")
    st.caption("Train Your Thinking, Not Just Your Coding")
    st.divider()

    # Mentor Message
    mentor = api(f"/mentor/?user_id={USER_ID}")
    if mentor and mentor.get("message"):
        st.info(f"💬 {mentor['message']}")
        for tip in mentor.get("tips", [])[:2]:
            st.caption(f"→ {tip}")
        st.divider()

    # Streak
    streak = api(f"/streak/?user_id={USER_ID}")
    if streak:
        col1, col2 = st.columns(2)
        col1.metric("🔥 Streak", f"{streak['current_streak']} days")
        col2.metric("🏆 Best", f"{streak['longest_streak']} days")

        # Heatmap (last 14 days)
        heatmap = streak.get("heatmap", [])[-14:]
        if heatmap:
            st.caption("Last 14 days:")
            cols = st.columns(14)
            for i, day in enumerate(heatmap):
                emoji = "🟩" if day["active"] else "⬜"
                cols[i].markdown(f"<div style='text-align:center;font-size:12px'>{emoji}</div>", unsafe_allow_html=True)
        st.divider()

    # Weakness report
    weak = api(f"/weakness/?user_id={USER_ID}")
    if weak and weak.get("weak_topics"):
        st.markdown("**⚠️ Weak Areas:**")
        for t in weak["weak_topics"][:3]:
            st.markdown(f"- {t}")
        st.divider()

    # Navigation
    st.session_state.active_tab = st.radio(
        "Navigate",
        ["Solve", "My History", "Leaderboard", "Recommended", "Admin"],
        label_visibility="collapsed"
    )

# ── Main Content ──────────────────────────────────────────────────────────────
tab = st.session_state.active_tab

# ═══════════════════════════════════════════════════════
# TAB: SOLVE
# ═══════════════════════════════════════════════════════
if tab == "Solve":

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        companies = api("/companies/") or []
        company_filter = st.selectbox("🏢 Company", ["All"] + companies)
    with col2:
        topics_list = ["All","arrays","strings","dynamic-programming","graphs","trees","stack","binary-search","linked-lists"]
        topic_filter = st.selectbox("📂 Topic", topics_list)
    with col3:
        diff_filter = st.selectbox("⚡ Difficulty", ["All","easy","medium","hard"])

    # Fetch problems with filters
    params = "?"
    if company_filter != "All": params += f"company={company_filter}&"
    if topic_filter != "All":   params += f"topic={topic_filter}&"
    if diff_filter != "All":    params += f"difficulty={diff_filter}&"

    problems = api(f"/problems/{params}") or []
    if not problems:
        st.warning("No problems for this filter.")
        st.stop()

    problem_map = {f"[{p['difficulty'].upper()}] {p['title']}": p["id"] for p in problems}
    selected_label = st.selectbox("🧩 Select Problem", list(problem_map.keys()))
    selected_id    = problem_map[selected_label]
    problem        = api(f"/problem/{selected_id}")
    if not problem: st.stop()

    # Company tags
    if problem.get("companies"):
        tags = " ".join([f"`{c}`" for c in problem["companies"][:5]])
        st.caption(f"🏢 Asked at: {tags}")

    st.subheader(problem["title"])
    diff = problem["difficulty"]
    icon = "🟢" if diff=="easy" else "🟡" if diff=="medium" else "🔴"
    st.caption(f"{icon} {diff.title()} · 📂 {problem['topic']}")
    st.info(problem["question"])

    # ── Interview Timer ───────────────────────────────────────────────────────
    with st.expander("⏱️ Interview Timer (optional)", expanded=False):
        timer_mins = st.slider("Set timer (minutes)", 10, 60, 20, step=5)
        col_t1, col_t2, col_t3 = st.columns(3)

        if col_t1.button("▶ Start Timer"):
            st.session_state.timer_running = True
            st.session_state.timer_start   = time.time()
            st.session_state.timer_seconds = timer_mins * 60
            st.session_state.timer_done    = False

        if col_t2.button("⏹ Stop Timer"):
            st.session_state.timer_running = False

        if st.session_state.timer_running:
            elapsed  = time.time() - (st.session_state.timer_start or time.time())
            remaining = max(0, st.session_state.timer_seconds - int(elapsed))
            mins, secs = divmod(remaining, 60)
            progress = 1 - (remaining / st.session_state.timer_seconds)

            if remaining == 0:
                st.error("⏰ Time's up! Submit your solution now!")
                st.session_state.timer_running = False
            else:
                color = "normal" if progress < 0.7 else "inverse"
                st.progress(progress)
                st.metric("Time Remaining", f"{mins:02d}:{secs:02d}")
                time.sleep(1)
                st.rerun()

    # ── Visible Test Cases ────────────────────────────────────────────────────
    st.subheader("🧪 Examples")
    visible_cases = problem.get("visible_test_cases", problem.get("test_cases", []))
    hidden_count  = len(problem.get("hidden_test_cases", []))
    for i, tc in enumerate(visible_cases):
        with st.expander(f"Example {i+1}", expanded=(i==0)):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Input:**")
                for k, v in tc["input"].items():
                    st.code(f"{k} = {v}", language="python")
            with c2:
                st.markdown("**Expected Output:**")
                st.code(str(tc["output"]), language="python")
    st.caption(f"🔒 +{hidden_count} hidden test cases will also run")

    # ── Hints ─────────────────────────────────────────────────────────────────
    with st.expander("💡 Hints (click to reveal)", expanded=False):
        for i, hint in enumerate(problem.get("hints", [])):
            if st.button(f"Reveal Hint {i+1}", key=f"hint_{selected_id}_{i}"):
                st.session_state.hint_level = i + 1
            if st.session_state.hint_level > i:
                st.warning(f"💡 {hint}")

    # ── Thinking ──────────────────────────────────────────────────────────────
    st.subheader("🧠 Your Thinking")
    st.caption("⭐ This is what ThinkCode AI evaluates — explain BEFORE you code!")
    thinking = st.text_area(
        "Explain your approach:",
        placeholder="• Why did you choose this approach?\n• What is the time complexity?\n• How are you handling edge cases?\n• Can it be optimized?",
        height=120, key=f"think_{selected_id}"
    )
    wc = len(thinking.split()) if thinking.strip() else 0
    if wc > 0:
        q = "🏆 Excellent!" if wc>=60 else "✅ Good!" if wc>=25 else "⚠️ Thoda aur likho..."
        st.caption(f"{wc} words — {q}")

    # ── Code Editor ───────────────────────────────────────────────────────────
    st.subheader("💻 Your Code")
    default_code = problem.get("starter_code", "def solve():\n    pass")
    code = st.text_area("Write inside solve():", height=320,
                        value=default_code, key=f"code_{selected_id}")

    # ── Submit ────────────────────────────────────────────────────────────────
    if st.button("🚀 Submit & Get AI Feedback", type="primary", use_container_width=True):
        with st.spinner("🧠 Analyzing your thinking..."):
            result = api("/submit/", "POST", {
                "problem_id": selected_id,
                "user_code": code,
                "thinking_text": thinking,
                "user_id": USER_ID
            })
            st.session_state.result = result

    # ── Results ───────────────────────────────────────────────────────────────
    if st.session_state.result:
        r = st.session_state.result
        st.divider()
        st.subheader("📊 Results")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Passed",   f"{r.get('passed',0)} / {r.get('total',0)}")
        c2.metric("Visible",        f"{r.get('visible_passed',0)} / {r.get('visible_total',0)}")
        c3.metric("Hidden 🔒",      f"{r.get('hidden_passed',0)} / {r.get('hidden_total',0)}")
        c4.metric("Thinking Score", f"{r.get('thinking_score',0)} / 100")

        for i, res in enumerate(r.get("results", [])):
            if res["passed"]:
                st.success(f"✅ Example {i+1}: Passed")
            else:
                st.error(f"❌ Example {i+1}: Wrong Answer")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Expected:**")
                    st.code(str(res.get('expected')), language="python")
                with col2:
                    st.markdown("**Your Output:**")
                    st.code(str(res.get('got')), language="python")
                
                # Hint kya galat hua
                exp = res.get('expected')
                got = res.get('got')
                if got is None:
                    st.warning("⚠️ Your function returned nothing — make sure solve() returns a value!")
                elif type(exp) != type(got):
                    st.warning(f"⚠️ Wrong data type — expected `{type(exp).__name__}` but got `{type(got).__name__}`")
                elif isinstance(exp, list) and sorted(exp) == sorted(got):
                    st.info("💡 Values sahi hain but order galat hai — check karo!")
                else:
                    st.warning("⚠️ Output galat hai — apna logic check karo")
                
                if res.get('message') and res.get('message') != 'Wrong Answer':
                    st.caption(f"🔍 {res.get('message')}")
        ht = r.get("hidden_total", 0)
        if ht > 0:
            hp = r.get("hidden_passed", 0)
            if hp == ht: st.success(f"✅ All {ht} hidden test cases passed!")
            else: st.warning(f"⚠️ {ht-hp} hidden test case(s) failed — check edge cases")

        # Complexity
        cx = r.get("complexity_analysis", {})
        if cx:
            c1, c2 = st.columns(2)
            c1.metric("⏱ Time Complexity",  cx.get("time","?"))
            c2.metric("💾 Space Complexity", cx.get("space","?"))
            st.caption(cx.get("explanation",""))

        # Thinking feedback
        st.subheader("🧠 AI Thinking Analysis")
        src = r.get("model_source","rule_based")
        st.caption(f"Evaluated by: {'🤖 Neural Network' if src=='neural_network' else '📏 Rule-Based Engine'} · Approach: **{r.get('code_approach','?').replace('_',' ').title()}**")
        for fb in r.get("feedback",[]): st.info(fb)

        col1, col2 = st.columns(2)
        with col1:
            if r.get("strengths"):
                st.subheader("💪 Strengths")
                for s in r["strengths"]: st.success(s)
        with col2:
            if r.get("areas_to_improve"):
                st.subheader("📈 Improve")
                for a in r["areas_to_improve"]: st.warning(a)

        if r.get("suggestions"):
            st.subheader("🚀 Suggestions")
            for s in r["suggestions"]: st.info(s)

        # Code vs Optimal
        optimal = problem.get("optimal_solution")
        if optimal:
            st.subheader("🔍 Your Code vs Optimal Solution")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Your Code**")
                st.code(code, language="python")
            with col2:
                st.markdown("**Optimal Solution**")
                st.code(optimal, language="python")
                if problem.get("optimal_explanation"):
                    st.info(f"💡 {problem['optimal_explanation']}")

        # Reflection
        st.subheader("🪞 Reflection Questions")
        for q in r.get("reflection_questions",[]): st.warning(q)

        # Interviewer
        st.subheader("🎤 AI Interviewer")
        for q in r.get("followup_questions",[]): st.error(f"❓ {q}")

# ═══════════════════════════════════════════════════════
# TAB: MY HISTORY
# ═══════════════════════════════════════════════════════
elif tab == "My History":
    st.subheader("📜 My Submission History")

    history = api(f"/history/?user_id={USER_ID}&limit=30") or []
    dashboard = api(f"/dashboard/?user_id={USER_ID}") or {}

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Submissions",    dashboard.get("total_submissions", 0))
    c2.metric("Avg Thinking Score",   f"{dashboard.get('average_thinking_score',0)}/100")
    c3.metric("Avg Code Score",       f"{dashboard.get('average_code_score',0)}/100")

    # Topic performance bars
    st.subheader("📊 Performance by Topic")
    for t in dashboard.get("topics", []):
        score = round(t.get("avg_score") or 0, 1)
        col1, col2 = st.columns([3, 1])
        col1.progress(score/100, text=f"{t['topic']} ({t['count']} attempts)")
        col2.markdown(f"**{score}/100**")

    # History table
    st.subheader("Recent Submissions")
    if history:
        for h in history:
            passed_icon = "✅" if h["passed"] == h["total"] and h["total"] > 0 else "⚠️"
            diff_icon = "🟢" if h["difficulty"]=="easy" else "🟡" if h["difficulty"]=="medium" else "🔴"
            with st.expander(f"{passed_icon} {diff_icon} {h['problem_id'].replace('_',' ').title()} — Thinking: {h['thinking_score']}/100 · {h['submitted_at'][:10]}"):
                c1, c2, c3 = st.columns(3)
                c1.metric("Tests", f"{h['passed']}/{h['total']}")
                c2.metric("Thinking", f"{h['thinking_score']}/100")
                c3.metric("Code", f"{h['code_score']}/100")
    else:
        st.info("No submissions yet. Start solving problems!")

# ═══════════════════════════════════════════════════════
# TAB: LEADERBOARD
# ═══════════════════════════════════════════════════════
elif tab == "Leaderboard":
    st.subheader("🏆 Thinking Leaderboard")
    st.caption("Ranked by average thinking score — not just code correctness!")

    leaders = api("/leaderboard/?limit=10") or []
    if leaders:
        medals = ["🥇","🥈","🥉"] + ["🔸"]*7
        for i, l in enumerate(leaders):
            with st.container():
                c1, c2, c3, c4 = st.columns([1,3,2,2])
                c1.markdown(f"### {medals[i]}")
                c2.markdown(f"**{l['display_name']}**")
                c3.metric("Avg Thinking", f"{round(l['avg_thinking_score'],1)}/100")
                c4.metric("🔥 Streak", f"{l['current_streak']} days")
    else:
        st.info("Leaderboard is empty. Be the first to submit!")

# ═══════════════════════════════════════════════════════
# TAB: RECOMMENDED
# ═══════════════════════════════════════════════════════
elif tab == "Recommended":
    st.subheader("🎯 Recommended For You")
    st.caption("Based on your performance, weak areas, and progression")

    weak = api(f"/weakness/?user_id={USER_ID}") or {}
    recommended = api(f"/recommended/?user_id={USER_ID}") or []

    if weak.get("weak_topics"):
        st.warning(f"⚠️ Focus areas: **{', '.join(weak['weak_topics'][:3])}**")
    if weak.get("strong_topics"):
        st.success(f"💪 You're great at: **{', '.join(weak['strong_topics'][:3])}**")

    if recommended:
        st.subheader("Next Problems to Solve:")
        for p in recommended:
            diff_icon = "🟢" if p["difficulty"]=="easy" else "🟡" if p["difficulty"]=="medium" else "🔴"
            companies = ", ".join(p.get("companies", [])[:3])
            with st.expander(f"{diff_icon} {p['title']} · {p['topic']}"):
                st.write(p["question"])
                if companies: st.caption(f"🏢 {companies}")
                if st.button("Solve This", key=f"rec_{p['id']}"):
                    st.session_state.active_tab = "Solve"
                    st.rerun()
    else:
        st.info("Solve some problems first to get personalized recommendations!")

# ═══════════════════════════════════════════════════════
# TAB: ADMIN
# ═══════════════════════════════════════════════════════
elif tab == "Admin":
    st.subheader("🛠 Admin Panel")
    st.caption("Label training data and retrain the thinking model")

    admin_stats = api("/admin/stats/") or {}
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Submissions", admin_stats.get("total_submissions", 0))
    c2.metric("Labeled",           admin_stats.get("labeled", 0))
    c3.metric("Unlabeled",         admin_stats.get("unlabeled", 0))
    engine = "🤖 Neural Net" if admin_stats.get("model_available") else "📏 Rule-Based"
    c4.metric("Engine", engine)

    st.subheader("🧠 Train Model")
    col1, col2 = st.columns(2)
    epochs    = col1.number_input("Epochs", 10, 1000, 150, step=10)
    seed_only = col2.checkbox("Labeled data only")
    if st.button("🚀 Train Now", type="primary"):
        res = api("/admin/train/", "POST", {"epochs": int(epochs), "seed_only": seed_only})
        if res: st.success(f"✅ {res.get('message', 'Training started!')}")

    st.subheader("📋 Label Submissions")
    samples = api(f"/admin/unlabeled/?limit=10") or []
    if not samples:
        st.success("🎉 All caught up — no unlabeled submissions!")
    for s in samples:
        with st.expander(f"#{s['id'][:8]} — {s['problem_id']} · {s.get('topic','')}"):
            if s.get("thinking_text"):
                st.markdown("**🧠 Thinking:**")
                st.text(s["thinking_text"])
            st.markdown("**💻 Code:**")
            st.code(s.get("code",""), language="python")

            c1, c2 = st.columns(2)
            score    = c1.number_input("Score (0-100)", 0, 100, int(s.get("thinking_score",50)), key=f"sc_{s['id']}")
            approach = c2.selectbox("Approach", ["brute_force","basic","optimized","optimal"], key=f"ap_{s['id']}")
            if st.button("✅ Save Label", key=f"save_{s['id']}"):
                res = api("/admin/label/", "POST", {
                    "sample_id": s["id"], "thinking_score": int(score),
                    "approach": approach, "notes": ""
                })
                if res: st.success("Saved!")
                st.rerun()