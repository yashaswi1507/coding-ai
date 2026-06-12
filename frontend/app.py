import os
import streamlit as st
import requests
import time

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

for key, val in {
    "result": None, "hint_level": 0,
    "timer_running": False, "timer_start": None,
    "timer_seconds": 1200, "active_tab": "🧩 Solve"
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🧠 ThinkCode AI")
    st.caption("Train Your Thinking, Not Just Your Coding")
    st.divider()

    mentor = api(f"/mentor/?user_id={USER_ID}")
    if mentor:
        level = mentor.get("level", {})
        if level:
            st.markdown(f"### {level.get('icon','')} {level.get('level','')}")
            st.caption(level.get("desc",""))
        if mentor.get("message"):
            st.info(mentor["message"])
        for tip in mentor.get("tips", [])[:2]:
            st.caption(f"→ {tip}")
        st.divider()

    streak = api(f"/streak/?user_id={USER_ID}")
    if streak:
        c1, c2 = st.columns(2)
        c1.metric("🔥 Streak", f"{streak['current_streak']} days")
        c2.metric("🏆 Best",   f"{streak['longest_streak']} days")
        heatmap = streak.get("heatmap", [])[-14:]
        if heatmap:
            cols = st.columns(14)
            for i, day in enumerate(heatmap):
                cols[i].markdown(f"<div style='text-align:center'>{'🟩' if day['active'] else '⬜'}</div>", unsafe_allow_html=True)
        st.divider()

    weak = api(f"/weakness/?user_id={USER_ID}")
    if weak and weak.get("weak_topics"):
        st.markdown("**⚠️ Weak Areas:**")
        for t in weak["weak_topics"][:3]:
            st.markdown(f"- {t}")
        st.divider()

    st.session_state.active_tab = st.radio("", [
        "🧩 Solve", "🌟 Daily Challenge", "🗺️ Learning Path",
        "📜 History", "🏆 Leaderboard", "🎖️ Achievements", "🛠 Admin"
    ], label_visibility="collapsed")

tab = st.session_state.active_tab

# ═══════════════════════════════════════════════════════
# TAB: SOLVE
# ═══════════════════════════════════════════════════════
if tab == "🧩 Solve":
    col1, col2, col3 = st.columns(3)
    with col1:
        companies = api("/companies/") or []
        company_filter = st.selectbox("🏢 Company", ["All"] + companies)
    with col2:
        topics_list = ["All","arrays","strings","dynamic-programming","graphs","trees","stack","binary-search","linked-lists"]
        topic_filter = st.selectbox("📂 Topic", topics_list)
    with col3:
        diff_filter = st.selectbox("⚡ Difficulty", ["All","easy","medium","hard"])

    params = "?"
    if company_filter != "All": params += f"company={company_filter}&"
    if topic_filter != "All":   params += f"topic={topic_filter}&"
    if diff_filter != "All":    params += f"difficulty={diff_filter}&"

    problems = api(f"/problems/{params}") or []
    if not problems: st.warning("No problems for this filter."); st.stop()

    problem_map = {f"[{p['difficulty'].upper()}] {p['title']}": p["id"] for p in problems}
    selected_label = st.selectbox("🧩 Select Problem", list(problem_map.keys()))
    selected_id = problem_map[selected_label]
    problem = api(f"/problem/{selected_id}")
    if not problem: st.stop()

    # Header
    st.subheader(problem["title"])
    diff = problem["difficulty"]
    icon = "🟢" if diff=="easy" else "🟡" if diff=="medium" else "🔴"
    if problem.get("companies"):
        tags = " ".join([f"`{c}`" for c in problem["companies"][:5]])
        st.caption(f"{icon} {diff.title()} · 📂 {problem['topic']} · 🏢 {tags}")
    st.info(problem["question"])

    # Alternative approaches
    if problem.get("approaches"):
        with st.expander("🔄 Different Approaches", expanded=False):
            for approach in problem["approaches"]:
                st.markdown(f"**{approach['name']}** — `{approach['complexity']}`")
                st.caption(approach["desc"])

    # Timer
    with st.expander("⏱️ Interview Timer", expanded=False):
        timer_mins = st.slider("Minutes", 10, 60, 20, step=5)
        c1, c2 = st.columns(2)
        if c1.button("▶ Start"):
            st.session_state.timer_running = True
            st.session_state.timer_start   = time.time()
            st.session_state.timer_seconds = timer_mins * 60
        if c2.button("⏹ Stop"):
            st.session_state.timer_running = False

        if st.session_state.timer_running:
            elapsed   = time.time() - (st.session_state.timer_start or time.time())
            remaining = max(0, st.session_state.timer_seconds - int(elapsed))
            mins, secs = divmod(remaining, 60)
            progress = 1 - (remaining / st.session_state.timer_seconds)
            if remaining == 0:
                st.error("⏰ Time's up!")
                st.session_state.timer_running = False
            else:
                st.progress(progress)
                st.metric("Remaining", f"{mins:02d}:{secs:02d}")
                time.sleep(1); st.rerun()

    # Visible test cases
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
                st.markdown("**Output:**")
                st.code(str(tc["output"]), language="python")
    st.caption(f"🔒 +{hidden_count} hidden test cases will also run")

    # Hints
    with st.expander("💡 Hints", expanded=False):
        for i, hint in enumerate(problem.get("hints", [])):
            if st.button(f"Reveal Hint {i+1}", key=f"h_{selected_id}_{i}"):
                st.session_state.hint_level = i + 1
            if st.session_state.hint_level > i:
                st.warning(f"💡 {hint}")

    # Thinking
    st.subheader("🧠 Think Before You Code")
    st.caption("Explain your plan BEFORE writing code — this is what separates great engineers from average ones!")

    col_t1, col_t2, col_t3 = st.columns(3)
    col_t1.markdown("**Plan your approach**")
    col_t2.markdown("**State complexity**")
    col_t3.markdown("**Spot edge cases**")

    thinking = st.text_area(
        "Your thinking:",
        placeholder="Example: I'll use a hashmap to store each number's index as I traverse. This gives O(n) time since lookup is O(1). Edge cases: empty array returns []. Space is O(n) for the hashmap.",
        height=110, key=f"think_{selected_id}"
    )
    wc = len(thinking.split()) if thinking.strip() else 0
    if wc == 0:
        st.caption("⚠️ No explanation = lower thinking score — interviewers always want to hear your reasoning!")
    elif wc < 15:
        st.caption(f"⚠️ {wc} words — too brief, elaborate more")
    elif wc < 40:
        st.caption(f"🔵 {wc} words — good start, mention complexity too!")
    else:
        st.caption(f"✅ {wc} words — great explanation!")

    # Code
    st.subheader("💻 Your Code")
    default_code = problem.get("starter_code", "def solve():\n    pass")
    code = st.text_area("Write inside solve():", height=320,
                        value=default_code, key=f"code_{selected_id}")

    if st.button("🚀 Submit & Get AI Feedback", type="primary", use_container_width=True):
        # Reset interview state for new submission
        st.session_state.interview_q_idx = 0
        st.session_state.interview_answers = []
        st.session_state.interview_done = False
        with st.spinner("🧠 Analyzing thinking..."):
            result = api("/submit/", "POST", {
                "problem_id": selected_id, "user_code": code,
                "thinking_text": thinking, "user_id": USER_ID
            })
            st.session_state.result = result

    # ── Results ───────────────────────────────────────────────────────────────
    if st.session_state.result:
        r = st.session_state.result
        st.divider()

        # New Achievements popup
        if r.get("new_achievements"):
            for badge in r["new_achievements"]:
                st.success(f"🎖️ New Achievement: {badge['icon']} **{badge['title']}** — {badge['desc']}")

        # XP Gained
        xp = r.get("xp", {})
        if xp.get("xp_gained"):
            xp_info = xp.get("level", {})
            st.info(f"⚡ **+{xp['xp_gained']} XP** gained! · Total: {xp.get('total_xp', 0)} XP · {xp_info.get('icon','')} {xp_info.get('title','')}")

        # Scores
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Tests Passed", f"{r.get('passed',0)}/{r.get('total',0)}")
        c2.metric("Visible",      f"{r.get('visible_passed',0)}/{r.get('visible_total',0)}")
        c3.metric("Hidden 🔒",    f"{r.get('hidden_passed',0)}/{r.get('hidden_total',0)}")
        code_pct = int((r.get('passed',0) / r.get('total',1)) * 100)
        c4.metric("💻 Code Score", f"{code_pct}%")

        # ── FEATURE 1: Score Breakdown ──────────────────────────────────────
        breakdown = r.get("score_breakdown", {}).get("breakdown", {})
        if breakdown:
            st.subheader("📊 Thinking Score Breakdown")
            for key, val in breakdown.items():
                score, max_score = val["score"], val["max"]
                pct = score / max_score if max_score else 0
                c1, c2 = st.columns([3,1])
                c1.progress(pct, text=f"{val['label']} — {val['detail']}")
                c2.markdown(f"**{score}/{max_score}**")

        for i, res in enumerate(r.get("results", [])):
            if res["passed"]: st.success(f"✅ Example {i+1}: Passed")
            else: st.error(f"❌ Example {i+1}: Expected `{res.get('expected')}` → Got `{res.get('got')}`")

        ht = r.get("hidden_total",0)
        if ht > 0:
            hp = r.get("hidden_passed",0)
            if hp==ht: st.success(f"✅ All {ht} hidden test cases passed!")
            else: st.warning(f"⚠️ {ht-hp} hidden test case(s) failed")

        # ── FEATURE 6: Edge Case Detector ──────────────────────────────────
        missing = r.get("missing_edge_cases", [])
        if missing:
            st.subheader("🛡️ Missing Edge Cases")
            for ec in missing:
                st.warning(f"⚠️ **{ec['case']}** — {ec['question']}")

        # Complexity
        cx = r.get("complexity_analysis", {})
        if cx:
            c1, c2 = st.columns(2)
            c1.metric("⏱ Time",  cx.get("time","?"))
            c2.metric("💾 Space", cx.get("space","?"))
            st.caption(cx.get("explanation",""))

        # ── FEATURE 2: Thinking Pattern from feedback ───────────────────────
        st.subheader("🧠 AI Thinking Analysis")
        src = r.get("model_source","rule_based")
        approach = r.get("code_approach","?")
        st.caption(f"{'🤖 Neural Network' if src=='neural_network' else '📏 Rule-Based'} · Approach: **{approach.replace('_',' ').title()}**")
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
            st.subheader("🔍 Your Code vs Optimal")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Your Code**")
                st.code(code, language="python")
            with c2:
                st.markdown("**Optimal Solution**")
                st.code(optimal, language="python")
                if problem.get("optimal_explanation"):
                    st.info(f"💡 {problem['optimal_explanation']}")

        # ── FEATURE 5: Reflection Scoring ──────────────────────────────────
        st.subheader("🪞 Post-Solve Reflection")
        st.caption("Now that you have solved it — reflect and deepen your understanding!")
        with st.form(key=f"ref_{selected_id}"):
            reflection_answers = []
            for idx, q in enumerate(r.get("reflection_questions",[])):
                ans = st.text_area(q, key=f"ans_{selected_id}_{idx}", height=80)
                reflection_answers.append((q, ans))
            submitted = st.form_submit_button("✅ Score My Reflections")

        if submitted:
            st.subheader("📊 Reflection Scores")
            total_ref_score = 0
            for q, ans in reflection_answers:
                if ans.strip():
                    result_ref = api("/score-reflection/", "POST", {"question": q, "answer": ans})
                    if result_ref:
                        score = result_ref.get("score", 0)
                        level = result_ref.get("level","")
                        total_ref_score += score
                        icon = "🏆" if score>=80 else "✅" if score>=55 else "⚠️"
                        st.write(f"{icon} **{level}** ({score}/100) — {result_ref.get('feedback','')}")

            if reflection_answers:
                avg_ref = total_ref_score // len(reflection_answers)
                st.metric("Overall Reflection Score", f"{avg_ref}/100")
                # Save reflection score for trend tracking
                api("/save-score/", "POST", {
                    "user_id": USER_ID,
                    "problem_id": selected_id,
                    "avg_score": avg_ref,
                    "score_type": "reflection"
                })

        # ── AI Interviewer — Step by Step ──────────────────────────────
        st.divider()
        st.subheader("🎤 AI Mock Interview")
        st.caption("Answer each question one by one — just like a real interview!")

        questions = r.get("followup_questions", [])

        if questions:
            # Track current question index
            if "interview_q_idx" not in st.session_state:
                st.session_state.interview_q_idx = 0
            if "interview_answers" not in st.session_state:
                st.session_state.interview_answers = []
            if "interview_done" not in st.session_state:
                st.session_state.interview_done = False

            idx = st.session_state.interview_q_idx
            total_qs = len(questions)

            # Progress bar
            st.progress(idx / total_qs, text=f"Question {min(idx+1, total_qs)} of {total_qs}")

            # Interview not done yet
            if not st.session_state.interview_done:
                if idx < total_qs:
                    # Current question
                    st.markdown(f"### ❓ {questions[idx]}")
                    answer = st.text_area(
                        "Your Answer:",
                        height=100,
                        placeholder="Explain clearly — just like you would in a real interview...",
                        key=f"interview_ans_{idx}"
                    )

                    if st.button("Next →" if idx < total_qs - 1 else "Submit Interview ✅",
                                 type="primary", key=f"interview_btn_{idx}"):
                        if answer.strip():
                            st.session_state.interview_answers.append({
                                "question": questions[idx],
                                "answer": answer
                            })
                            if idx < total_qs - 1:
                                st.session_state.interview_q_idx += 1
                            else:
                                st.session_state.interview_done = True
                            st.rerun()
                        else:
                            st.warning("⚠️ Answer likho pehle!")

            # Interview complete — show analysis
            else:
                st.success("✅ Interview complete! Yeh rahi teri performance:")
                st.divider()

                total_score = 0
                for i, qa in enumerate(st.session_state.interview_answers):
                    result_ref = api("/score-reflection/", "POST", {
                        "question": qa["question"],
                        "answer": qa["answer"]
                    })

                    score = result_ref.get("score", 0) if result_ref else 0
                    level = result_ref.get("level", "") if result_ref else ""
                    feedback = result_ref.get("feedback", "") if result_ref else ""
                    total_score += score

                    icon = "🏆" if score >= 80 else "✅" if score >= 55 else "⚠️"
                    with st.expander(f"{icon} Q{i+1}: {qa['question'][:60]}...", expanded=True):
                        st.markdown(f"**Your Answer:** {qa['answer']}")
                        st.markdown(f"**Score:** {score}/100 — {level}")
                        st.caption(feedback)

                # Overall interview score
                avg = total_score // len(st.session_state.interview_answers)
                st.divider()
                col1, col2 = st.columns(2)
                col1.metric("🎤 Interview Score", f"{avg}/100")
                col2.metric("🧠 Thinking Score", f"{r.get('thinking_score', 0)}/100")

                grade = "Excellent! 🏆" if avg >= 80 else "Good! ✅" if avg >= 55 else "Needs Practice ⚠️"
                st.info(f"**Overall: {grade}** — Keep practicing to ace real interviews!")

                # Restart interview button
                if st.button("🔄 Retry Interview"):
                    st.session_state.interview_q_idx = 0
                    st.session_state.interview_answers = []
                    st.session_state.interview_done = False
                    st.rerun()

# ═══════════════════════════════════════════════════════
# TAB: DAILY CHALLENGE
# ═══════════════════════════════════════════════════════
elif tab == "🌟 Daily Challenge":
    st.subheader("🌟 Today's Thinking Challenge")
    daily = api(f"/daily-challenge/?user_id={USER_ID}")

    if daily:
        if daily.get("completed"):
            st.success("✅ You already completed today's challenge! Come back tomorrow.")
        else:
            st.info(f"🎯 {daily.get('bonus_note','')}")

        diff = daily.get("difficulty","easy")
        icon = "🟢" if diff=="easy" else "🟡" if diff=="medium" else "🔴"
        st.subheader(f"{icon} {daily.get('title','')}")
        st.caption(f"Topic: {daily.get('topic','')} · Difficulty: {diff}")
        st.write(daily.get("question",""))

        if daily.get("companies"):
            st.caption(f"🏢 Asked at: {', '.join(daily['companies'][:3])}")

        st.divider()
        thinking = st.text_area("🧠 Your Thinking:", height=120, key="daily_think")
        code = st.text_area("💻 Your Code:", height=280,
                            value=daily.get("starter_code","def solve():\n    pass"), key="daily_code")

        if st.button("🚀 Submit Daily Challenge", type="primary", use_container_width=True):
            with st.spinner("Analyzing..."):
                result = api("/submit/", "POST", {
                    "problem_id": daily["id"], "user_code": code,
                    "thinking_text": thinking, "user_id": USER_ID
                })
                if result:
                    score = result.get("thinking_score", 0)
                    passed = result.get("passed", 0)
                    total  = result.get("total", 0)
                    st.balloons()
                    st.success(f"🌟 Daily Challenge Complete! Thinking Score: {score}/100 · Tests: {passed}/{total}")
                    if result.get("new_achievements"):
                        for b in result["new_achievements"]:
                            st.success(f"🎖️ {b['icon']} {b['title']} unlocked!")

# ═══════════════════════════════════════════════════════
# TAB: LEARNING PATH
# ═══════════════════════════════════════════════════════
elif tab == "🗺️ Learning Path":
    st.subheader("🗺️ Your Learning Path")
    paths = api("/learning-paths/") or []

    path_options = {p["title"]: p["id"] for p in paths}
    selected_path = st.selectbox("Choose Your Path", list(path_options.keys()))
    path_id = path_options[selected_path]

    path_data = api(f"/learning-path/{path_id}?user_id={USER_ID}")

    if path_data:
        st.caption(path_data.get("desc",""))
        progress = path_data.get("progress", 0)
        solved   = path_data.get("solved_count", 0)
        total    = path_data.get("total", 0)

        st.progress(progress/100, text=f"Progress: {solved}/{total} problems ({progress}%)")
        st.divider()

        for step in path_data.get("steps", []):
            diff_icon = "🟢" if step["difficulty"]=="easy" else "🟡" if step["difficulty"]=="medium" else "🔴"
            if step["solved"]:
                st.success(f"✅ {step['order']}. {step['title']} {diff_icon}")
            elif step["current"]:
                st.warning(f"👉 {step['order']}. **{step['title']}** {diff_icon} ← Next!")
            else:
                st.write(f"🔒 {step['order']}. {step['title']} {diff_icon}")

# ═══════════════════════════════════════════════════════
# TAB: HISTORY
# ═══════════════════════════════════════════════════════
elif tab == "📜 History":
    import pandas as pd

    st.subheader("📜 My Progress")

    dashboard = api(f"/dashboard/?user_id={USER_ID}") or {}
    level = dashboard.get("thinker_level", {})
    history = api(f"/history/?user_id={USER_ID}&limit=50") or []

    if level:
        st.markdown(f"### {level.get('icon','')} {level.get('level','')}")
        st.caption(level.get("desc",""))

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Submissions",  dashboard.get("total_submissions",0))
    c2.metric("Avg Thinking Score", f"{dashboard.get('average_thinking_score',0)}/100")
    c3.metric("Avg Code Score",     f"{dashboard.get('average_code_score',0)}/100")

    # ── 1. XP Progress Dashboard ─────────────────────────────────────────────
    xp_data = api(f"/xp/?user_id={USER_ID}")
    if xp_data:
        st.divider()
        st.subheader("⚡ XP Progress Dashboard")
        col1, col2, col3 = st.columns(3)
        col1.metric(f"{xp_data.get('icon','')} Level",
                    f"{xp_data.get('level',1)} — {xp_data.get('title','')}")
        col2.metric("Total XP", xp_data.get("total_xp", 0))
        col3.metric("Next Level", f"{xp_data.get('xp_to_next',0)} XP needed")
        st.progress(xp_data.get("progress_to_next", 0) / 100,
                    text=f"Progress to next level: {xp_data.get('progress_to_next',0)}%")

        # XP History Bar Chart
        if xp_data.get("history") and len(xp_data["history"]) >= 2:
            xp_hist = xp_data["history"][:10][::-1]
            xp_df = pd.DataFrame({
                "Submission": [f"#{i+1}" for i in range(len(xp_hist))],
                "XP Gained":  [h["xp_gained"] for h in xp_hist]
            })
            st.bar_chart(xp_df.set_index("Submission"))

    # ── 2. Thinking Score Trend Graph ────────────────────────────────────────
    if history and len(history) >= 2:
        st.divider()
        st.subheader("📈 Thinking Score Trend")
        trend_df = pd.DataFrame({
            "Submission": [f"#{i+1}" for i in range(len(history[:20][::-1]))],
            "Thinking Score": [h["thinking_score"] for h in history[:20][::-1]]
        })
        st.line_chart(trend_df.set_index("Submission"))

    # ── 3. Topic-wise Analytics Chart ────────────────────────────────────────
    topics = dashboard.get("topics", [])
    if topics:
        st.divider()
        st.subheader("📊 Topic-wise Analytics")
        topic_df = pd.DataFrame({
            "Topic":          [t["topic"] for t in topics],
            "Thinking Score": [round(t.get("avg_score") or 0, 1) for t in topics],
            "Attempts":       [t["count"] for t in topics]
        })
        st.bar_chart(topic_df.set_index("Topic")["Thinking Score"])
        # Detailed table
        for t in topics:
            score = round(t.get("avg_score") or 0, 1)
            color = "🟢" if score >= 70 else "🟡" if score >= 40 else "🔴"
            col1, col2 = st.columns([4, 1])
            col1.progress(score/100,
                          text=f"{color} {t['topic']} ({t['count']} attempts)")
            col2.markdown(f"**{score}/100**")

    # ── 4. Weakness Evolution Visualization ──────────────────────────────────
    st.divider()
    st.subheader("📉 Weakness Evolution")
    evolution = api(f"/weakness-evolution/?user_id={USER_ID}")
    if evolution and evolution.get("evolution"):
        if evolution.get("most_improved"):
            st.success(f"📈 Most improved: **{evolution['most_improved']}**")
        if evolution.get("needs_attention"):
            st.warning(f"⚠️ Needs attention: **{evolution['needs_attention']}**")
        evo_list = evolution["evolution"]
        if len(evo_list) >= 2:
            evo_df = pd.DataFrame({
                "Topic":      [e["topic"] for e in evo_list],
                "This Week":  [e["recent"] for e in evo_list],
                "Last Week":  [e["prev"] for e in evo_list],
            })
            st.bar_chart(evo_df.set_index("Topic"))
        for e in evo_list:
            col1, col2, col3 = st.columns([3, 1, 1])
            col1.markdown(f"**{e['topic']}** — {e['trend']}")
            col2.metric("This week", f"{e['recent']}/100")
            col3.metric("Change",
                        f"{'+' if e['change']>0 else ''}{e['change']}")
    else:
        st.info("Solve more problems across topics to see evolution!")

    # ── 5. Performance Heatmap ────────────────────────────────────────────────
    if history and topics:
        st.divider()
        st.subheader("🗺️ Performance Heatmap")
        st.caption("Topic vs Difficulty — average thinking score")
        heatmap_data = {}
        for h in history:
            t = h.get("topic", "unknown")
            d = h.get("difficulty", "easy")
            key = (t, d)
            if key not in heatmap_data:
                heatmap_data[key] = []
            heatmap_data[key].append(h["thinking_score"])

        all_topics = list(set(k[0] for k in heatmap_data))
        diffs = ["easy", "medium", "hard"]
        rows = []
        for topic in all_topics:
            row = {"Topic": topic}
            for d in diffs:
                scores = heatmap_data.get((topic, d), [])
                row[d.title()] = round(sum(scores)/len(scores), 0) if scores else 0
            rows.append(row)

        if rows:
            heatmap_df = pd.DataFrame(rows).set_index("Topic")
            # Color cells manually without matplotlib
            def color_score(val):
                if val >= 70: return "background-color: #1a472a; color: white"
                elif val >= 40: return "background-color: #7d6608; color: white"
                elif val > 0:  return "background-color: #641e16; color: white"
                return ""
            st.dataframe(
                heatmap_df.style.applymap(color_score),
                use_container_width=True
            )

    # ── Final Cognitive Report ───────────────────────────────────────────────
    st.divider()
    st.subheader("🧠 Final Cognitive Report")
    st.caption("Your complete performance summary across all dimensions")
    report = api(f"/cognitive-report/?user_id={USER_ID}")
    if report and report.get("total_submissions", 0) > 0:
        grade = report.get("grade", "?")
        overall = report.get("overall_score", 0)
        grade_color = (
            "#FFD700" if grade in ("S","A") else
            "#4AFF91" if grade == "B" else
            "#FFB547" if grade == "C" else "#FF5B6B"
        )
        st.markdown(
            f"<div style='text-align:center; padding:16px; background:#1a1a2e; "
            f"border-radius:12px; border:1px solid #333'>"
            f"<span style='font-size:48px; font-weight:700; color:{grade_color}'>{grade}</span>"
            f"<br><span style='font-size:14px; color:#aaa'>Overall Cognitive Score: {overall}/100</span>"
            f"</div>",
            unsafe_allow_html=True
        )
        st.divider()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🧠 Thinking",   f"{report.get('thinking_score',0)}/100")
        col2.metric("💻 Code",       f"{report.get('code_score',0)}/100")
        col3.metric("🪞 Reflection", f"{report.get('reflection_score',0)}/100")
        col4.metric("🎤 Interview",  f"{report.get('interview_score',0)}/100")

        # Radar-style bar chart
        import pandas as pd
        score_df = pd.DataFrame({
            "Dimension": ["Thinking", "Code", "Reflection", "Interview"],
            "Score": [
                report.get("thinking_score", 0),
                report.get("code_score", 0),
                report.get("reflection_score", 0),
                report.get("interview_score", 0),
            ]
        })
        st.bar_chart(score_df.set_index("Dimension"))
    else:
        st.info("Submit at least one solution to generate your Cognitive Report!")

    # ── Reflection Trend Analytics ────────────────────────────────────────────
    st.divider()
    st.subheader("🪞 Reflection Trend Analytics")
    ref_trend = api(f"/reflection-trend/?user_id={USER_ID}&limit=20") or []
    if len(ref_trend) >= 2:
        import pandas as pd
        ref_trend_rev = ref_trend[::-1]
        ref_df = pd.DataFrame({
            "Attempt": [f"#{i+1}" for i in range(len(ref_trend_rev))],
            "Reflection Score": [r["avg_score"] for r in ref_trend_rev]
        })
        st.line_chart(ref_df.set_index("Attempt"))
        avg_ref = sum(r["avg_score"] for r in ref_trend) // len(ref_trend)
        st.caption(f"Average reflection score: {avg_ref}/100 across {len(ref_trend)} attempts")
    else:
        st.info("Answer reflection questions after solving to see your trend!")

    # ── Interview Trend Analytics ─────────────────────────────────────────────
    st.divider()
    st.subheader("🎤 Interview Trend Analytics")
    int_trend = api(f"/interview-trend/?user_id={USER_ID}&limit=20") or []
    if len(int_trend) >= 2:
        import pandas as pd
        int_trend_rev = int_trend[::-1]
        int_df = pd.DataFrame({
            "Attempt": [f"#{i+1}" for i in range(len(int_trend_rev))],
            "Interview Score": [r["avg_score"] for r in int_trend_rev]
        })
        st.line_chart(int_df.set_index("Attempt"))
        avg_int = sum(r["avg_score"] for r in int_trend) // len(int_trend)
        st.caption(f"Average interview score: {avg_int}/100 across {len(int_trend)} mock interviews")
    else:
        st.info("Complete mock interviews after solving to see your trend!")

    # ── Thinking Patterns ────────────────────────────────────────────────────
    st.divider()
    st.subheader("🔍 Your Thinking Patterns")
    patterns = api(f"/patterns/?user_id={USER_ID}")
    if patterns:
        st.info(f"**Style:** {patterns.get('style','')} · **Trend:** {patterns.get('trend','')}")
        for p in patterns.get("patterns", []):
            if p["type"] == "strength": st.success(p["msg"])
            else: st.warning(p["msg"])

    # History list
    st.subheader("Recent Submissions")
    history = api(f"/history/?user_id={USER_ID}&limit=20") or []
    if history:
        for h in history:
            pi = "✅" if h["passed"]==h["total"] and h["total"]>0 else "⚠️"
            di = "🟢" if h["difficulty"]=="easy" else "🟡" if h["difficulty"]=="medium" else "🔴"
            approach = h.get("code_approach","?")
            with st.expander(f"{pi} {di} {h['problem_id'].replace('_',' ').title()} — 🧠{h['thinking_score']}/100 · {h.get('submitted_at','')[:10]}"):
                c1, c2, c3 = st.columns(3)
                c1.metric("Tests",    f"{h['passed']}/{h['total']}")
                c2.metric("Thinking", f"{h['thinking_score']}/100")
                c3.metric("Approach", approach.replace("_"," ").title())
    else:
        st.info("No submissions yet!")

    # ── Thinking Replay ──────────────────────────────────────────────────────
    st.divider()
    st.subheader("🎬 Thinking Replay")
    st.caption("See how your thinking evolved across attempts on the same problem")

    if history:
        problem_ids = list(dict.fromkeys([h["problem_id"] for h in history]))
        selected_replay = st.selectbox(
            "Select problem to replay:",
            problem_ids,
            format_func=lambda x: x.replace("_", " ").title()
        )

        replay = api(f"/thinking-replay/?user_id={USER_ID}&problem_id={selected_replay}") or []

        if len(replay) == 0:
            st.info("No attempts found for this problem.")
        elif len(replay) == 1:
            st.info("Only 1 attempt — solve again to see your progress!")
        else:
            st.success(f"📈 {len(replay)} attempts found — see how you improved!")
            for attempt in replay:
                num = attempt["attempt_num"]
                score = attempt["thinking_score"]
                change = attempt.get("score_change", 0)
                improved = attempt.get("improved", False)
                approach = attempt.get("code_approach", "?")
                date = attempt.get("submitted_at", "")[:10]

                change_str = f"+{change}" if change > 0 else str(change)
                icon = "📈" if improved else "📉" if change < 0 else "➡️"

                with st.expander(
                    f"{icon} Attempt {num} — 🧠 {score}/100 ({change_str}) · {date}",
                    expanded=(num == len(replay))
                ):
                    c1, c2 = st.columns(2)
                    c1.metric("Thinking Score", f"{score}/100")
                    c2.metric("Approach", approach.replace("_", " ").title())

                    if attempt.get("thinking_text"):
                        st.markdown("**Your Thinking:**")
                        st.info(attempt["thinking_text"])
                    else:
                        st.caption("No thinking explanation was provided")

                    passed = attempt.get("passed", 0)
                    total = attempt.get("total", 0)
                    if passed == total and total > 0:
                        st.success(f"✅ All {total} tests passed")
                    else:
                        st.warning(f"⚠️ {passed}/{total} tests passed")
    else:
        st.info("Solve problems first to see your thinking replay!")

# ═══════════════════════════════════════════════════════
# TAB: LEADERBOARD
# ═══════════════════════════════════════════════════════
elif tab == "🏆 Leaderboard":
    st.subheader("🏆 Thinking Leaderboard")
    st.caption("Ranked by thinking score — not just code correctness!")

    leaders = api("/leaderboard/?limit=10") or []
    medals = ["🥇","🥈","🥉"] + ["🔸"]*7

    if leaders:
        for i, l in enumerate(leaders):
            c1, c2, c3, c4 = st.columns([1,3,2,2])
            c1.markdown(f"### {medals[i]}")
            c2.markdown(f"**{l['display_name']}**")
            c3.metric("Avg Thinking", f"{round(l['avg_thinking_score'],1)}/100")
            c4.metric("🔥 Streak",   f"{l['current_streak']} days")
    else:
        st.info("Be the first on the leaderboard!")

# ═══════════════════════════════════════════════════════
# TAB: ACHIEVEMENTS
# ═══════════════════════════════════════════════════════
elif tab == "🎖️ Achievements":
    st.subheader("🎖️ Achievements")
    achievements = api(f"/achievements/?user_id={USER_ID}") or []

    earned   = [a for a in achievements if a["earned"]]
    unearned = [a for a in achievements if not a["earned"]]

    st.markdown(f"**{len(earned)}/{len(achievements)} Unlocked**")
    st.progress(len(earned)/max(len(achievements),1))

    if earned:
        st.subheader("✅ Earned")
        cols = st.columns(3)
        for i, a in enumerate(earned):
            with cols[i % 3]:
                st.success(f"{a['icon']} **{a['title']}**\n\n{a['desc']}")

    if unearned:
        st.subheader("🔒 Locked")
        cols = st.columns(3)
        for i, a in enumerate(unearned):
            with cols[i % 3]:
                st.write(f"🔒 **{a['title']}**\n\n{a['desc']}")

# ═══════════════════════════════════════════════════════
# TAB: ADMIN
# ═══════════════════════════════════════════════════════
elif tab == "🛠 Admin":
    st.subheader("🛠 Admin Panel")
    admin_stats = api("/admin/stats/") or {}
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Submissions", admin_stats.get("total_submissions",0))
    c2.metric("Labeled",     admin_stats.get("labeled",0))
    c3.metric("Unlabeled",   admin_stats.get("unlabeled",0))
    c4.metric("Engine", "🤖 Neural Net" if admin_stats.get("model_available") else "📏 Rule-Based")

    st.subheader("🧠 Train Model")
    c1, c2 = st.columns(2)
    epochs    = c1.number_input("Epochs", 10, 1000, 150, step=10)
    seed_only = c2.checkbox("Labeled only")
    if st.button("🚀 Train Now", type="primary"):
        res = api("/admin/train/", "POST", {"epochs": int(epochs), "seed_only": seed_only})
        if res: st.success(f"✅ {res.get('message','')}")

    st.subheader("📋 Label Submissions")
    samples = api("/admin/unlabeled/?limit=10") or []
    if not samples:
        st.success("🎉 All submissions labeled!")
    for s in samples:
        with st.expander(f"#{s['id'][:8]} — {s['problem_id']}"):
            if s.get("thinking_text"):
                st.markdown("**🧠 Thinking:**")
                st.text(s["thinking_text"])
            st.markdown("**💻 Code:**")
            st.code(s.get("code",""), language="python")
            c1, c2 = st.columns(2)
            score    = c1.number_input("Score", 0, 100, int(s.get("thinking_score",50)), key=f"sc_{s['id']}")
            approach = c2.selectbox("Approach", ["brute_force","basic","optimized","optimal"], key=f"ap_{s['id']}")
            if st.button("✅ Save", key=f"sv_{s['id']}"):
                res = api("/admin/label/", "POST", {"sample_id": s["id"], "thinking_score": int(score), "approach": approach, "notes": ""})
                if res: st.success("Saved!"); st.rerun()