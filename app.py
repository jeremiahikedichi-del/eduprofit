import streamlit as st
import pandas as pd
import math

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="EduProfit — Course Revenue Predictor",
    page_icon="📈",
    layout="wide",
)

# ─────────────────────────────────────────────
#  STYLING
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'Syne', sans-serif; }
.stApp { background: #0d0f14; color: #e8e3d9; }
h1, h2, h3 { font-family: 'Syne', sans-serif !important; font-weight: 800 !important; }

.main-title {
    font-family: 'Syne', sans-serif; font-size: 3rem; font-weight: 800;
    letter-spacing: -0.03em; color: #e8e3d9; line-height: 1.1;
}
.main-subtitle {
    font-family: 'DM Mono', monospace; font-size: 0.85rem; color: #8a8070;
    letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 2.5rem;
}
.accent { color: #c8f060; }
.section-label {
    font-family: 'DM Mono', monospace; font-size: 0.7rem; letter-spacing: 0.15em;
    text-transform: uppercase; color: #c8f060; margin-bottom: 0.5rem; margin-top: 1.5rem;
}
.metric-block {
    background: #161a22; border: 1px solid #252b38;
    border-radius: 8px; padding: 1.25rem 1.5rem; margin-bottom: 0.75rem;
}
.metric-label {
    font-family: 'DM Mono', monospace; font-size: 0.7rem; letter-spacing: 0.12em;
    text-transform: uppercase; color: #8a8070; margin-bottom: 0.2rem;
}
.metric-value { font-family: 'Syne', sans-serif; font-size: 1.6rem; font-weight: 700; color: #e8e3d9; }
.metric-value.positive { color: #c8f060; }
.metric-value.negative { color: #ff6b6b; }
.metric-value.neutral  { color: #60c8f0; }
.result-section {
    background: #161a22; border: 1px solid #252b38;
    border-radius: 10px; padding: 1.5rem; margin-bottom: 1rem;
}
.result-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 0.5rem 0; border-bottom: 1px solid #1e2330; font-size: 0.92rem;
}
.result-row:last-child { border-bottom: none; }
.result-row .label { color: #8a8070; }
.result-row .value { font-family: 'DM Mono', monospace; color: #e8e3d9; }
.result-row .value.green { color: #c8f060; }
.result-row .value.red   { color: #ff6b6b; }
.total-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 0.75rem 0 0.25rem 0; font-size: 1rem; font-weight: 700;
}
.summary-banner {
    background: linear-gradient(135deg, #1a2010 0%, #0f1a08 100%);
    border: 1px solid #3a5020; border-radius: 10px; padding: 2rem; margin-bottom: 2rem;
}
.tbill-info {
    background: #0f1520; border: 1px solid #1e3050; border-left: 3px solid #60c8f0;
    border-radius: 6px; padding: 0.75rem 1rem; margin-top: 0.5rem;
    font-family: 'DM Mono', monospace; font-size: 0.78rem; color: #8ab8d0; line-height: 1.6;
}
.warn-info {
    background: #1a1500; border: 1px solid #3a3000; border-left: 3px solid #f0c860;
    border-radius: 6px; padding: 0.75rem 1rem; margin-top: 0.5rem;
    font-family: 'DM Mono', monospace; font-size: 0.78rem; color: #c0a040; line-height: 1.6;
}
.divider { border: none; border-top: 1px solid #252b38; margin: 1.5rem 0; }
.stNumberInput > div > div > input,
.stTextInput > div > div > input,
.stSelectbox > div > div {
    background: #1a1f2e !important; border: 1px solid #252b38 !important;
    color: #e8e3d9 !important; font-family: 'DM Mono', monospace !important;
    border-radius: 6px !important;
}
.stSlider > div { padding: 0 !important; }
.stButton > button {
    background: #c8f060 !important; color: #0d0f14 !important;
    font-family: 'Syne', sans-serif !important; font-weight: 700 !important;
    border: none !important; border-radius: 6px !important;
    padding: 0.5rem 1.5rem !important; letter-spacing: 0.02em;
}
.stButton > button:hover { background: #d8ff70 !important; }
section[data-testid="stSidebar"] {
    background: #0f1118 !important; border-right: 1px solid #1e2330 !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def naira(n):
    return f"₦{n:,.0f}"

def calc_admin_fee(price):
    """
    Admin fee is a markup ON TOP of the course price.
    Student pays: price + admin_fee
    Refundable deposit = full course price (untouched)
    """
    return min(price * 0.10, 10_000)

def calc_tbill_interest(principal, annual_rate_pct, holding_months, tenor_days):
    """
    T-bill interest using Bamboo/CBN simple interest formula per rollover.

    Each rollover:
      Gross Interest = Pool × Annual Rate × (Tenor Days / 365)
      Pool reinvested = Previous Pool + Gross Interest
    Leftover days after complete rollovers are ignored.

    Example: ₦5,000,000, 14.99% annual, 83-day tenor, 6-month holding
      Rollover 1: ₦5,000,000 × 14.99% × (83/365) = ₦170,434  → pool = ₦5,170,434
      Rollover 2: ₦5,170,434 × 14.99% × (83/365) = ₦176,244  → pool = ₦5,346,678
      Total interest = ₦346,678

    Returns: (total_interest, num_rollovers, leftover_days, effective_rate_pct)
    """
    annual_rate   = annual_rate_pct / 100
    holding_days  = holding_months * 30.44

    num_rollovers = int(holding_days // tenor_days)
    leftover_days = holding_days - (num_rollovers * tenor_days)

    pool           = principal
    total_interest = 0

    for _ in range(num_rollovers):
        gross_interest = pool * annual_rate * (tenor_days / 365)
        pool          += gross_interest
        total_interest += gross_interest

    effective_rate = (total_interest / principal) * 100 if principal > 0 else 0

    return total_interest, num_rollovers, int(leftover_days), effective_rate


def run_model(course):
    p              = course
    students       = p["students"]
    price          = p["price"]
    admin_fee      = calc_admin_fee(price)
    total_charged  = price + admin_fee   # what student actually pays
    refundable     = price               # full course price is refundable
    holding        = p["holding_months"]
    comp_rate      = p["completion_rate"] / 100
    tenor_days     = p["tbill_tenor_days"]
    tbill_pct      = p["tbill_annual_rate"]

    completers     = round(students * comp_rate)
    non_completers = students - completers

    total_admin_fees   = admin_fee * students
    forfeited_deposits = refundable * non_completers
    deposit_pool       = refundable * students

    tbill_interest, num_rollovers, leftover_days, effective_rate = calc_tbill_interest(
        deposit_pool, tbill_pct, holding, tenor_days
    )

    gross_income  = total_admin_fees + forfeited_deposits + tbill_interest
    total_refunds = refundable * completers

    instructor_cost       = total_charged * (p["instructor_pct"] / 100) * students
    marketing_cost        = p["marketing"]
    content_creation_cost = p["content_creation"]
    tech_cost             = p["tech"] * holding
    other_cost            = p["other"] * holding
    pay_proc_cost         = gross_income * (p["pay_proc_pct"] / 100)

    total_expenses = (instructor_cost + marketing_cost + content_creation_cost +
                      tech_cost + other_cost + pay_proc_cost)

    net_profit = gross_income - total_expenses

    return {
        "students":           students,
        "completers":         completers,
        "non_completers":     non_completers,
        "comp_rate":          comp_rate * 100,
        "total_charged":      total_charged,
        "admin_fee":          admin_fee,
        "total_admin_fees":   total_admin_fees,
        "forfeited_deposits": forfeited_deposits,
        "deposit_pool":       deposit_pool,
        "tbill_interest":     tbill_interest,
        "num_rollovers":      num_rollovers,
        "leftover_days":      leftover_days,
        "effective_rate":     effective_rate,
        "tenor_days":         tenor_days,
        "tbill_tenor_rate":   tbill_pct,
        "gross_income":       gross_income,
        "total_refunds":      total_refunds,
        "instructor_cost":    instructor_cost,
        "marketing_cost":     marketing_cost,
        "content_cost":       content_creation_cost,
        "tech_cost":          tech_cost,
        "other_cost":         other_cost,
        "pay_proc_cost":      pay_proc_cost,
        "total_expenses":     total_expenses,
        "net_profit":         net_profit,
    }

# ─────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="main-title">EduProfit<span class="accent">.</span></div>
<div class="main-subtitle">Online Course Revenue &amp; Profit Predictor</div>
""", unsafe_allow_html=True)
st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  COURSE INPUT
# ─────────────────────────────────────────────
if "num_courses" not in st.session_state:
    st.session_state.num_courses = 1

left_col, right_col = st.columns([1.1, 0.9], gap="large")

TENOR_OPTIONS = {
    "91 days  (~3 months)":  91,
    "182 days (~6 months)":  182,
    "364 days (~12 months)": 364,
}

with left_col:
    st.markdown('<div class="section-label">📚 Course Configuration</div>', unsafe_allow_html=True)

    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.markdown(f"**{st.session_state.num_courses} course(s) configured**")
    with col_b:
        if st.button("＋ Add Course"):
            st.session_state.num_courses += 1
        if st.session_state.num_courses > 1:
            if st.button("－ Remove"):
                st.session_state.num_courses -= 1

    courses_input = []

    for i in range(st.session_state.num_courses):
        with st.expander(f"Course {i+1}", expanded=(i == 0)):

            # Basic Info
            st.markdown('<div class="section-label">Basic Info</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                name  = st.text_input("Course Name", value=f"Course {i+1}", key=f"name_{i}")
                price = st.number_input("Course Price (₦)", min_value=1000, value=50000, step=1000, key=f"price_{i}")
                admin = calc_admin_fee(price)
                st.markdown(
                    f'<div style="font-family:\'DM Mono\',monospace;font-size:0.8rem;color:#8a8070;">'
                    f'Admin fee (markup): <span style="color:#c8f060;">{naira(admin)}</span>'
                    f'&nbsp;|&nbsp;Student pays: <span style="color:#60c8f0;">{naira(price + admin)}</span>'
                    f'&nbsp;|&nbsp;Refundable: <span style="color:#e8e3d9;">{naira(price)}</span></div>',
                    unsafe_allow_html=True
                )
            with c2:
                students       = st.number_input("Expected Students", min_value=1, value=100, key=f"students_{i}")
                holding_months = st.number_input("Holding Period (months)", min_value=3, max_value=60, value=6, key=f"holding_{i}")
                completion     = st.slider("Completion Rate (%)", 0, 100, 15, key=f"comp_{i}")

            # T-bill Settings
            st.markdown('<div class="section-label">🏦 T-bill Investment Settings</div>', unsafe_allow_html=True)
            t1, t2 = st.columns(2)
            with t1:
                tenor_label      = st.selectbox("T-bill Tenor", list(TENOR_OPTIONS.keys()), key=f"tenor_{i}")
            with t2:
                tbill_tenor_rate = st.number_input(
                    "Annual T-bill Rate (%)",
                    min_value=0.0, max_value=100.0, value=14.99, step=0.01, key=f"tbill_{i}",
                    help="The annualised rate quoted by CBN/your platform (e.g. 14.99%). Interest per rollover = Pool × Rate × (Tenor days / 365)"
                )

            tenor_days = TENOR_OPTIONS[tenor_label]
            holding_days_approx = holding_months * 30.44

            # Live preview
            deposit_pool_preview = price * students
            p_interest, p_rollovers, p_leftover, p_eff = calc_tbill_interest(
                deposit_pool_preview, tbill_tenor_rate, holding_months, tenor_days
            )

            rollover_note = f"{p_rollovers}x {tenor_days}-day rollover{'s' if p_rollovers != 1 else ''}"
            if p_leftover > 0:
                rollover_note += f" ({p_leftover} leftover days ignored — not counted)"

            if tenor_days <= holding_days_approx:
                st.markdown(
                    f'<div class="tbill-info">'
                    f'Pool: <b style="color:#e8e3d9;">{naira(deposit_pool_preview)}</b> &nbsp;·&nbsp; '
                    f'{rollover_note}<br>'
                    f'Effective return over {holding_months} months: '
                    f'<b style="color:#c8f060;">{p_eff:.2f}%</b> &nbsp;·&nbsp; '
                    f'Interest earned: <b style="color:#c8f060;">{naira(p_interest)}</b>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<div class="warn-info">'
                    f'⚠ T-bill tenor ({tenor_days} days) exceeds your holding period '
                    f'({holding_months} months ≈ {int(holding_days_approx)} days). '
                    f'The bill won\'t mature before refunds are due. '
                    f'Use a shorter tenor or extend the holding period.'
                    f'</div>',
                    unsafe_allow_html=True
                )

            # Expenses
            st.markdown('<div class="section-label">Expenses</div>', unsafe_allow_html=True)
            e1, e2 = st.columns(2)
            with e1:
                content_creation = st.number_input(
                    "Content Creation Cost (₦)", min_value=0, value=200000, step=10000, key=f"content_{i}",
                    help="One-time cost to produce this course"
                )
                marketing = st.number_input(
                    "Marketing Budget (₦)", min_value=0, value=100000, step=10000, key=f"marketing_{i}",
                    help="Total spend to fill this cohort"
                )
                instructor_pct = st.number_input(
                    "Instructor Revenue Share (%)", min_value=0.0, max_value=100.0, value=20.0, step=1.0, key=f"instructor_{i}"
                )
            with e2:
                tech         = st.number_input("Tech/Hosting per month (₦)", min_value=0, value=10000, step=1000, key=f"tech_{i}")
                pay_proc_pct = st.number_input("Payment Processing Fee (%)", min_value=0.0, max_value=10.0, value=1.5, step=0.1, key=f"payproc_{i}")
                other        = st.number_input("Other Monthly Costs (₦)", min_value=0, value=5000, step=1000, key=f"other_{i}")

            courses_input.append({
                "name":             name,
                "price":            price,
                "students":         students,
                "holding_months":   holding_months,
                "completion_rate":  completion,
                "tbill_annual_rate": tbill_tenor_rate,
                "tbill_tenor_days": tenor_days,
                "content_creation": content_creation,
                "marketing":        marketing,
                "instructor_pct":   instructor_pct,
                "tech":             tech,
                "pay_proc_pct":     pay_proc_pct,
                "other":            other,
            })

# ─────────────────────────────────────────────
#  RESULTS
# ─────────────────────────────────────────────
with right_col:
    st.markdown('<div class="section-label">📊 Prediction Results</div>', unsafe_allow_html=True)

    all_results = [run_model(c) for c in courses_input]

    # Summary banner (multi-course only)
    if len(all_results) > 1:
        total_income   = sum(r["gross_income"]   for r in all_results)
        total_expenses = sum(r["total_expenses"] for r in all_results)
        total_profit   = sum(r["net_profit"]     for r in all_results)
        total_refunds  = sum(r["total_refunds"]  for r in all_results)
        profit_class   = "positive" if total_profit >= 0 else "negative"

        st.markdown(f"""
        <div class="summary-banner">
            <div class="metric-label">Total Net Profit — All Courses</div>
            <div class="metric-value {profit_class}">{naira(total_profit)}</div>
            <div style="margin-top:1rem;display:flex;gap:2rem;">
                <div>
                    <div class="metric-label">Gross Income</div>
                    <div style="font-family:'DM Mono',monospace;color:#e8e3d9;font-size:1rem;">{naira(total_income)}</div>
                </div>
                <div>
                    <div class="metric-label">Total Expenses</div>
                    <div style="font-family:'DM Mono',monospace;color:#e8e3d9;font-size:1rem;">{naira(total_expenses)}</div>
                </div>
                <div>
                    <div class="metric-label">Refunds to Pay</div>
                    <div style="font-family:'DM Mono',monospace;color:#60c8f0;font-size:1rem;">{naira(total_refunds)}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Per-course results
    for i, (course, r) in enumerate(zip(courses_input, all_results)):
        profit_class = "positive" if r["net_profit"] >= 0 else "negative"

        with st.expander(f"📘 {course['name']} — {naira(r['net_profit'])} profit", expanded=True):

            m1, m2, m3 = st.columns(3)
            with m1:
                st.markdown(f"""<div class="metric-block">
                    <div class="metric-label">Gross Income</div>
                    <div class="metric-value neutral">{naira(r['gross_income'])}</div>
                </div>""", unsafe_allow_html=True)
            with m2:
                st.markdown(f"""<div class="metric-block">
                    <div class="metric-label">Total Expenses</div>
                    <div class="metric-value">{naira(r['total_expenses'])}</div>
                </div>""", unsafe_allow_html=True)
            with m3:
                st.markdown(f"""<div class="metric-block">
                    <div class="metric-label">Net Profit</div>
                    <div class="metric-value {profit_class}">{naira(r['net_profit'])}</div>
                </div>""", unsafe_allow_html=True)

            # Students
            st.markdown(f"""
            <div class="result-section">
                <div style="font-family:'DM Mono',monospace;font-size:0.7rem;letter-spacing:0.12em;text-transform:uppercase;color:#c8f060;margin-bottom:0.75rem;">Students</div>
                <div class="result-row"><span class="label">Enrolled</span><span class="value">{r['students']}</span></div>
                <div class="result-row"><span class="label">Completers ({r['comp_rate']:.0f}%)</span><span class="value green">{r['completers']}</span></div>
                <div class="result-row"><span class="label">Non-completers</span><span class="value red">{r['non_completers']}</span></div>
            </div>
            """, unsafe_allow_html=True)

            # Rollover description
            rollover_desc = f"{r['num_rollovers']}x {r['tenor_days']}-day bill"
            if r['leftover_days'] > 0:
                rollover_desc += f" + {r['leftover_days']} days simple interest"

            # Income
            st.markdown(f"""
            <div class="result-section">
                <div style="font-family:'DM Mono',monospace;font-size:0.7rem;letter-spacing:0.12em;text-transform:uppercase;color:#c8f060;margin-bottom:0.75rem;">Income Breakdown</div>
                <div class="result-row"><span class="label">Admin fees collected</span><span class="value">{naira(r['total_admin_fees'])}</span></div>
                <div class="result-row"><span class="label">Forfeited deposits</span><span class="value">{naira(r['forfeited_deposits'])}</span></div>
                <div class="result-row"><span class="label">Deposit pool invested</span><span class="value">{naira(r['deposit_pool'])}</span></div>
                <div class="result-row"><span class="label">T-bill structure</span><span class="value" style="font-size:0.8rem;color:#8a8070;">{rollover_desc}</span></div>
                <div class="result-row"><span class="label">Effective yield over period</span><span class="value green">{r['effective_rate']:.2f}%</span></div>
                <div class="result-row"><span class="label">T-bill interest earned</span><span class="value green">{naira(r['tbill_interest'])}</span></div>
                <div class="total-row"><span>Gross Income</span><span style="font-family:'DM Mono',monospace;color:#60c8f0;">{naira(r['gross_income'])}</span></div>
                <div class="result-row"><span class="label">Refunds to pay out</span><span class="value red">-{naira(r['total_refunds'])}</span></div>
            </div>
            """, unsafe_allow_html=True)

            # Expenses
            st.markdown(f"""
            <div class="result-section">
                <div style="font-family:'DM Mono',monospace;font-size:0.7rem;letter-spacing:0.12em;text-transform:uppercase;color:#c8f060;margin-bottom:0.75rem;">Expense Breakdown</div>
                <div class="result-row"><span class="label">Content creation</span><span class="value">{naira(r['content_cost'])}</span></div>
                <div class="result-row"><span class="label">Marketing</span><span class="value">{naira(r['marketing_cost'])}</span></div>
                <div class="result-row"><span class="label">Instructor payouts</span><span class="value">{naira(r['instructor_cost'])}</span></div>
                <div class="result-row"><span class="label">Tech/hosting ({course['holding_months']} months)</span><span class="value">{naira(r['tech_cost'])}</span></div>
                <div class="result-row"><span class="label">Payment processing</span><span class="value">{naira(r['pay_proc_cost'])}</span></div>
                <div class="result-row"><span class="label">Other ({course['holding_months']} months)</span><span class="value">{naira(r['other_cost'])}</span></div>
                <div class="total-row"><span>Total Expenses</span><span style="font-family:'DM Mono',monospace;color:#ff6b6b;">{naira(r['total_expenses'])}</span></div>
            </div>
            """, unsafe_allow_html=True)

    # Chart
    if len(all_results) >= 1:
        st.markdown('<div class="section-label" style="margin-top:1rem;">Income Sources — All Courses</div>', unsafe_allow_html=True)
        chart_data = pd.DataFrame({
            "Course":             [c["name"] for c in courses_input],
            "Admin Fees":         [r["total_admin_fees"]   for r in all_results],
            "Forfeited Deposits": [r["forfeited_deposits"] for r in all_results],
            "T-bill Interest":    [r["tbill_interest"]     for r in all_results],
        }).set_index("Course")
        st.bar_chart(chart_data, color=["#c8f060", "#60c8f0", "#f0a060"])