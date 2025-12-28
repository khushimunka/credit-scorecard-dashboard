def clamp(x, lo=0, hi=100):
    return max(lo, min(hi, x))

def score_quant(inputs):
    # weights sum to 1.0
    w = {
        "Current Ratio": 0.10,
        "Quick Ratio": 0.05,
        "DSCR": 0.12,
        "Interest Coverage": 0.10,
        "Debt-to-Equity": 0.10,
        "EBITDA Margin (%)": 0.10,
        "ROCE (%)": 0.08,
        "Revenue Growth YoY (%)": 0.10,
        "Operating Cash Flow / EBITDA": 0.10,
        "Receivables Days": 0.15
    }

    subs = {}

    # higher is better
    subs["Current Ratio"] = clamp((inputs["Current Ratio"] / 2.0) * 100)              # 2.0 ~ 100
    subs["Quick Ratio"] = clamp((inputs["Quick Ratio"] / 1.5) * 100)                  # 1.5 ~ 100
    subs["DSCR"] = clamp((inputs["DSCR"] / 3.0) * 100)                                # 3.0 ~ 100
    subs["Interest Coverage"] = clamp((inputs["Interest Coverage"] / 8.0) * 100)      # 8x ~ 100
    subs["Debt-to-Equity"] = clamp((1.0 - min(inputs["Debt-to-Equity"], 1.5)/1.5) * 100) # lower better
    subs["EBITDA Margin (%)"] = clamp((inputs["EBITDA Margin (%)"] / 25.0) * 100)     # 25% ~ 100
    subs["ROCE (%)"] = clamp((inputs["ROCE (%)"] / 18.0) * 100)                       # 18% ~ 100
    subs["Revenue Growth YoY (%)"] = clamp((inputs["Revenue Growth YoY (%)"] / 15.0) * 100) # 15% ~ 100
    subs["Operating Cash Flow / EBITDA"] = clamp((inputs["Operating Cash Flow / EBITDA"] / 1.0) * 100) # 1.0 ~ 100
    subs["Receivables Days"] = clamp((1.0 - min(inputs["Receivables Days"], 120)/120) * 100) # lower better

    score = sum(subs[k] * w[k] for k in w)
    contrib = {k: subs[k] * w[k] for k in w}
    return round(score, 2), subs, contrib, w

def score_qual(inputs):
    # scale 1-5 to 0-100, weights sum to 1.0
    w = {
        "Timely & Reliable Reporting (1-5)": 0.12,
        "Loan Repayment Track Record (1-5)": 0.15,
        "Tax & Statutory Compliance (1-5)": 0.10,
        "Governance & Transparency (1-5)": 0.12,
        "Management Capability (1-5)": 0.12,
        "Technology & Innovation (1-5)": 0.10,
        "Customer Concentration Risk (1-5)": 0.10,
        "Industry Growth Outlook (1-5)": 0.10,
        "Legal/Regulatory Sensitivity (1-5)": 0.09
    }

    subs = {}
    for k in w:
        subs[k] = clamp(((inputs[k] - 1) / 4) * 100)  # 1->0, 5->100

    score = sum(subs[k] * w[k] for k in w)
    contrib = {k: subs[k] * w[k] for k in w}
    return round(score, 2), subs, contrib, w

def decide_and_covenants(q_score, qual_score, quant_subs, qual_subs):
    final = round(q_score * 0.55 + qual_score * 0.45, 2)

    covenants = []

    # covenant triggers based on weak areas
    if quant_subs["DSCR"] < 60:
        covenants.append("Maintain DSCR >= 2.0 on a quarterly basis; breach triggers review.")
    if quant_subs["Receivables Days"] < 60:
        covenants.append("Monthly aging report; cap receivables days at 75; excess routed via escrow/collection account.")
    if quant_subs["Debt-to-Equity"] < 60:
        covenants.append("No additional funded debt without lender consent; maintain D/E <= 0.8.")
    if quant_subs["Operating Cash Flow / EBITDA"] < 70:
        covenants.append("Quarterly cash-flow monitoring; maintain OCF/EBITDA >= 0.8.")
    if qual_subs.get("Customer Concentration Risk (1-5)", 100) < 50:
        covenants.append("Customer concentration monitoring; top-1 customer share not to exceed agreed threshold.")
    if qual_subs.get("Governance & Transparency (1-5)", 100) < 50:
        covenants.append("Enhanced reporting: quarterly MIS pack + annual audited statements within defined timelines.")

    if final >= 80:
        decision = "APPROVE"
    elif final >= 65:
        decision = "APPROVE WITH COVENANTS"
        if not covenants:
            covenants.append("Standard covenants: quarterly financials, no material adverse change, and negative pledge.")
    else:
        decision = "REJECT"
        covenants = ["Not applicable (proposal not approved)."]

    return final, decision, covenants

def run_model(df):
    q = dict(zip(df[df["group"]=="quant"]["metric"], df[df["group"]=="quant"]["value"]))
    qual = dict(zip(df[df["group"]=="qual"]["metric"], df[df["group"]=="qual"]["value"]))

    q_score, q_subs, q_contrib, q_w = score_quant(q)
    qual_score, qual_subs, qual_contrib, qual_w = score_qual(qual)
    final, decision, covenants = decide_and_covenants(q_score, qual_score, q_subs, qual_subs)

    return {
        "quant_score": q_score,
        "qual_score": qual_score,
        "final_score": final,
        "decision": decision,
        "covenants": covenants,
        "q_subs": q_subs, "q_contrib": q_contrib, "q_w": q_w,
        "qual_subs": qual_subs, "qual_contrib": qual_contrib, "qual_w": qual_w
    }
