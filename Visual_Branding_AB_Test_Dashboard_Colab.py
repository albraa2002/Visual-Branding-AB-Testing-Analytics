# ============================================================
#  Visual Branding & A/B Testing ROI Dashboard
#  Google Colab — Single-Cell, Zero-Bug Script
# ============================================================

# ── 0. Install / import ─────────────────────────────────────
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from IPython.display import display, HTML

# ── 1. GENERATE DATA ────────────────────────────────────────
np.random.seed(42)
N = 3000

dates = pd.date_range("2025-01-01", "2025-12-31", freq="D")
visual_styles = ["Modern Minimalist", "Bohemian Vibe", "Aggressive Bold", "Corporate Trust"]
platforms     = ["Meta Ads", "TikTok Ads"]
campaign_ids  = [f"CMP-{str(i).zfill(4)}" for i in range(1, 101)]

# Style-level parameters
style_params = {
    # (imp_mult_lo, imp_mult_hi, ctr_lo, ctr_hi, cr_lo, cr_hi, aov_lo, aov_hi, spend_lo, spend_hi)
    "Modern Minimalist": dict(imp_lo=200, imp_hi=400, ctr_lo=0.020, ctr_hi=0.030,
                              cr_lo=0.040, cr_hi=0.070, aov_lo=55, aov_hi=75,
                              spend_lo=80,  spend_hi=220),
    "Bohemian Vibe":     dict(imp_lo=100, imp_hi=250, ctr_lo=0.025, ctr_hi=0.035,
                              cr_lo=0.060, cr_hi=0.080, aov_lo=65, aov_hi=80,
                              spend_lo=50,  spend_hi=160),
    "Aggressive Bold":   dict(imp_lo=350, imp_hi=500, ctr_lo=0.025, ctr_hi=0.035,
                              cr_lo=0.010, cr_hi=0.025, aov_lo=40, aov_hi=55,
                              spend_lo=150, spend_hi=300),
    "Corporate Trust":   dict(imp_lo=150, imp_hi=300, ctr_lo=0.005, ctr_hi=0.015,
                              cr_lo=0.025, cr_hi=0.045, aov_lo=50, aov_hi=70,
                              spend_lo=70,  spend_hi=250),
}

rows = []
for _ in range(N):
    date   = dates[np.random.randint(len(dates))]
    style  = np.random.choice(visual_styles)
    plat   = np.random.choice(platforms)
    cmp_id = np.random.choice(campaign_ids)
    p      = style_params[style]

    # Corporate Trust has worse CTR on TikTok
    ctr_adj = 0.4 if (style == "Corporate Trust" and plat == "TikTok Ads") else 1.0

    spend       = np.random.uniform(p["spend_lo"], p["spend_hi"])
    imp_mult    = np.random.uniform(p["imp_lo"],   p["imp_hi"])
    impressions = int(spend * imp_mult)
    ctr         = np.random.uniform(p["ctr_lo"],   p["ctr_hi"]) * ctr_adj
    clicks      = max(1, int(impressions * ctr))
    cr          = np.random.uniform(p["cr_lo"],    p["cr_hi"])
    purchases   = max(0, int(clicks * cr))
    aov         = np.random.uniform(p["aov_lo"],   p["aov_hi"])
    revenue     = round(purchases * aov, 2)

    rows.append({
        "Date":        date,
        "Campaign_ID": cmp_id,
        "Visual_Style": style,
        "Platform":    plat,
        "Spend_USD":   round(spend, 2),
        "Impressions": impressions,
        "Clicks":      clicks,
        "Purchases":   purchases,
        "Revenue_USD": revenue,
    })

df = pd.DataFrame(rows).sort_values("Date").reset_index(drop=True)
print(f"✅ Data generated: {len(df):,} rows  |  {df['Date'].min().date()} → {df['Date'].max().date()}")

# ── 2. KPI CALCULATIONS ─────────────────────────────────────
total_spend   = df["Spend_USD"].sum()
total_revenue = df["Revenue_USD"].sum()
overall_roas  = total_revenue / total_spend

style_kpi = (
    df.groupby("Visual_Style")
      .agg(
          Total_Spend   =("Spend_USD",   "sum"),
          Total_Revenue =("Revenue_USD", "sum"),
          Total_Clicks  =("Clicks",      "sum"),
          Total_Imps    =("Impressions", "sum"),
          Total_Purch   =("Purchases",   "sum"),
      )
      .assign(
          ROAS = lambda x: x["Total_Revenue"] / x["Total_Spend"],
          CTR  = lambda x: x["Total_Clicks"]  / x["Total_Imps"] * 100,
          CPC  = lambda x: x["Total_Spend"]   / x["Total_Clicks"],
          CPA  = lambda x: x["Total_Spend"]   / x["Total_Purch"].replace(0, np.nan),
      )
      .reset_index()
)

best_style = style_kpi.loc[style_kpi["ROAS"].idxmax(), "Visual_Style"]
best_roas  = style_kpi["ROAS"].max()

print(f"💰 Total Spend :  ${total_spend:,.2f}")
print(f"📈 Overall ROAS:  {overall_roas:.2f}x")
print(f"🏆 Best Style  :  {best_style}  ({best_roas:.2f}x ROAS)")

# ── 3. PLOTLY FIGURES ────────────────────────────────────────
PALETTE = {
    "Modern Minimalist": "#FF2D78",   # Hot Pink
    "Bohemian Vibe":     "#00F5FF",   # Cyan
    "Aggressive Bold":   "#FFE600",   # Yellow
    "Corporate Trust":   "#BF00FF",   # Violet
}
PAPER_BG = "rgba(0,0,0,0)"
PLOT_BG  = "rgba(255,255,255,0.03)"
FONT_CLR = "#E5E7EB"
GRID_CLR = "rgba(255,255,255,0.07)"

axis_style = dict(
    color=FONT_CLR, gridcolor=GRID_CLR,
    showline=True, linecolor="rgba(255,255,255,0.15)",
    tickfont=dict(color=FONT_CLR, size=11),
    titlefont=dict(color=FONT_CLR, size=12),
)

def base_layout(**kwargs):
    return dict(
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=dict(color=FONT_CLR, family="'DM Sans', sans-serif"),
        margin=dict(l=50, r=30, t=50, b=50),
        legend=dict(
            bgcolor="rgba(255,255,255,0.05)",
            bordercolor="rgba(255,255,255,0.1)",
            borderwidth=1,
            font=dict(color=FONT_CLR, size=11),
        ),
        **kwargs,
    )

# ── Fig 1: Bubble Scatter — CPC vs CTR ──────────────────────
fig_scatter = go.Figure()
for _, row in style_kpi.iterrows():
    is_winner = row["Visual_Style"] == best_style
    fig_scatter.add_trace(go.Scatter(
        x=[row["CTR"]],
        y=[row["CPC"]],
        mode="markers+text",
        name=row["Visual_Style"],
        text=["★ " + row["Visual_Style"] if is_winner else row["Visual_Style"]],
        textposition="top center",
        textfont=dict(size=11, color=PALETTE[row["Visual_Style"]]),
        marker=dict(
            size=[row["Total_Spend"] / 800],
            color=PALETTE[row["Visual_Style"]],
            opacity=0.85,
            line=dict(width=2, color="white"),
        ),
        hovertemplate=(
            f"<b>{row['Visual_Style']}</b><br>"
            f"CTR: {row['CTR']:.2f}%<br>"
            f"CPC: ${row['CPC']:.2f}<br>"
            f"Total Spend: ${row['Total_Spend']:,.0f}<extra></extra>"
        ),
    ))

fig_scatter.update_layout(
    **base_layout(
        title=dict(text="CPC vs. CTR by Visual Style", font=dict(size=16, color=FONT_CLR)),
        xaxis=dict(title="CTR (%)", **axis_style),
        yaxis=dict(title="CPC ($)", **axis_style),
        showlegend=True,
        height=420,
    )
)

# ── Fig 2: Horizontal Bar — ROAS by Visual Style ─────────────
roas_sorted = style_kpi.sort_values("ROAS")
bar_colors  = [
    "#00FF88" if s == best_style else PALETTE[s]
    for s in roas_sorted["Visual_Style"]
]

fig_roas = go.Figure(go.Bar(
    x=roas_sorted["ROAS"],
    y=roas_sorted["Visual_Style"],
    orientation="h",
    marker=dict(
        color=bar_colors,
        line=dict(width=0),
        opacity=0.9,
    ),
    text=[f"{'🏆 ' if s == best_style else ''}{v:.2f}x"
          for s, v in zip(roas_sorted["Visual_Style"], roas_sorted["ROAS"])],
    textposition="outside",
    textfont=dict(color=FONT_CLR, size=12),
    hovertemplate="<b>%{y}</b><br>ROAS: %{x:.2f}x<extra></extra>",
))

fig_roas.add_vline(
    x=overall_roas, line_dash="dash",
    line_color="rgba(255,255,255,0.35)", line_width=1.5,
    annotation_text=f"Overall avg {overall_roas:.2f}x",
    annotation_font=dict(color="rgba(255,255,255,0.55)", size=10),
    annotation_position="top right",
)

fig_roas.update_layout(
    **base_layout(
        title=dict(text="Average ROAS by Visual Style", font=dict(size=16, color=FONT_CLR)),
        xaxis=dict(title="ROAS (Revenue / Spend)", **axis_style),
        yaxis=dict(title="", **axis_style),
        showlegend=False,
        height=420,
    )
)

# ── Fig 3: Line — Cumulative Revenue Trend ───────────────────
fig_trend = go.Figure()
df_sorted = df.sort_values("Date")

for style in visual_styles:
    sub = df_sorted[df_sorted["Visual_Style"] == style].copy()
    sub["Cumulative_Revenue"] = sub["Revenue_USD"].cumsum()
    is_winner = style == best_style
    fig_trend.add_trace(go.Scatter(
        x=sub["Date"],
        y=sub["Cumulative_Revenue"],
        mode="lines",
        name=("★ " if is_winner else "") + style,
        line=dict(
            color=PALETTE[style],
            width=3 if is_winner else 1.8,
            dash="solid" if is_winner else "solid",
        ),
        opacity=1.0 if is_winner else 0.75,
        hovertemplate=(
            f"<b>{style}</b><br>"
            "Date: %{x|%b %d}<br>"
            "Cumulative Revenue: $%{y:,.0f}<extra></extra>"
        ),
    ))

fig_trend.update_layout(
    **base_layout(
        title=dict(text="Cumulative Revenue Trend by Visual Style (2025)", font=dict(size=16, color=FONT_CLR)),
        xaxis=dict(title="Date", **axis_style),
        yaxis=dict(title="Cumulative Revenue (USD)", tickprefix="$", **axis_style),
        height=400,
        hovermode="x unified",
    )
)

# ── 4. CONVERT FIGURES TO HTML DIVS ──────────────────────────
config = dict(displayModeBar=False, responsive=True)
div_scatter = fig_scatter.to_html(full_html=False, include_plotlyjs=False, config=config)
div_roas    = fig_roas.to_html(full_html=False, include_plotlyjs=False, config=config)
div_trend   = fig_trend.to_html(full_html=False, include_plotlyjs=False, config=config)

# ── 5. BUILD HTML DASHBOARD ───────────────────────────────────
roas_color = "#00FF88"
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Visual Branding & A/B Testing ROI Dashboard</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet"/>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  :root {{
    --bg:        #111827;
    --surface:   rgba(255,255,255,0.04);
    --border:    rgba(255,255,255,0.09);
    --pink:      #FF2D78;
    --cyan:      #00F5FF;
    --yellow:    #FFE600;
    --violet:    #BF00FF;
    --green:     #00FF88;
    --text:      #E5E7EB;
    --muted:     #9CA3AF;
  }}

  body {{
    background: var(--bg);
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
    min-height: 100vh;
    padding: 28px 32px 48px;
    background-image:
      radial-gradient(ellipse 60% 40% at 20% 10%, rgba(191,0,255,0.08) 0%, transparent 60%),
      radial-gradient(ellipse 50% 35% at 80% 90%, rgba(0,245,255,0.06) 0%, transparent 55%);
  }}

  /* ── Header ── */
  .header {{
    margin-bottom: 32px;
  }}
  .header-eyebrow {{
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--cyan);
    margin-bottom: 6px;
  }}
  .header h1 {{
    font-size: clamp(22px, 3vw, 32px);
    font-weight: 700;
    letter-spacing: -0.02em;
    line-height: 1.15;
  }}
  .header h1 span {{ color: var(--pink); }}
  .header-sub {{
    margin-top: 6px;
    color: var(--muted);
    font-size: 14px;
  }}
  .header-divider {{
    margin-top: 20px;
    height: 1px;
    background: linear-gradient(90deg, var(--pink), var(--cyan), transparent);
    opacity: 0.35;
  }}

  /* ── KPI Cards ── */
  .kpi-row {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 18px;
    margin-bottom: 24px;
  }}
  .kpi-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 22px 24px;
    backdrop-filter: blur(12px);
    position: relative;
    overflow: hidden;
    transition: border-color 0.25s;
  }}
  .kpi-card::before {{
    content: '';
    position: absolute;
    inset: 0;
    border-radius: inherit;
    padding: 1px;
    background: linear-gradient(135deg, rgba(255,255,255,0.08), transparent);
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: destination-out;
    mask-composite: exclude;
    pointer-events: none;
  }}
  .kpi-card:hover {{ border-color: rgba(255,255,255,0.18); }}
  .kpi-label {{
    font-size: 11px;
    font-family: 'Space Mono', monospace;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 10px;
  }}
  .kpi-value {{
    font-size: clamp(26px, 3vw, 36px);
    font-weight: 700;
    letter-spacing: -0.03em;
    line-height: 1;
  }}
  .kpi-value.pink   {{ color: var(--pink);   }}
  .kpi-value.cyan   {{ color: var(--cyan);   }}
  .kpi-value.green  {{ color: var(--green);  }}
  .kpi-sub {{
    margin-top: 8px;
    font-size: 12px;
    color: var(--muted);
  }}
  .kpi-badge {{
    display: inline-block;
    margin-top: 10px;
    padding: 3px 10px;
    border-radius: 99px;
    font-size: 11px;
    font-weight: 600;
    background: rgba(0,255,136,0.12);
    color: var(--green);
    border: 1px solid rgba(0,255,136,0.25);
  }}

  /* ── Charts Grid ── */
  .charts-mid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 18px;
    margin-bottom: 18px;
  }}
  .charts-full {{
    width: 100%;
  }}
  .chart-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 6px 4px 4px;
    backdrop-filter: blur(12px);
    overflow: hidden;
    transition: border-color 0.25s;
  }}
  .chart-card:hover {{ border-color: rgba(255,255,255,0.16); }}

  /* neon accent borders per card */
  .card-pink  {{ border-top: 2px solid var(--pink);   }}
  .card-cyan  {{ border-top: 2px solid var(--cyan);   }}
  .card-green {{ border-top: 2px solid var(--green);  }}

  /* ── Footer ── */
  .footer {{
    margin-top: 36px;
    text-align: center;
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.1em;
    color: rgba(255,255,255,0.18);
  }}

  @media (max-width: 900px) {{
    .kpi-row, .charts-mid {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>

<!-- ── Header ────────────────────────────────────────── -->
<div class="header">
  <div class="header-eyebrow">Performance Marketing Intelligence</div>
  <h1>Visual Branding &amp; <span>A/B Testing</span> ROI Dashboard</h1>
  <div class="header-sub">Jan 2025 – Dec 2025 &nbsp;·&nbsp; Meta Ads &amp; TikTok Ads &nbsp;·&nbsp; 4 Creative Styles</div>
  <div class="header-divider"></div>
</div>

<!-- ── KPI Cards ──────────────────────────────────────── -->
<div class="kpi-row">
  <div class="kpi-card">
    <div class="kpi-label">Total Ad Spend</div>
    <div class="kpi-value pink">${total_spend:,.0f}</div>
    <div class="kpi-sub">Across all campaigns &amp; platforms</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Overall ROAS</div>
    <div class="kpi-value green">{overall_roas:.2f}x</div>
    <div class="kpi-sub">Revenue / Total Spend</div>
    <span class="kpi-badge">↑ Neon Green = Profitable</span>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">🏆 Best Visual Style by ROAS</div>
    <div class="kpi-value cyan" style="font-size:22px; padding-top:4px;">{best_style}</div>
    <div class="kpi-sub">{best_roas:.2f}x ROAS — highest converting creative</div>
  </div>
</div>

<!-- ── Mid Row: Scatter + Bar ─────────────────────────── -->
<div class="charts-mid">
  <div class="chart-card card-pink">
    {div_scatter}
  </div>
  <div class="chart-card card-cyan">
    {div_roas}
  </div>
</div>

<!-- ── Full Width: Trend ──────────────────────────────── -->
<div class="charts-full">
  <div class="chart-card card-green">
    {div_trend}
  </div>
</div>

<!-- ── Footer ────────────────────────────────────────── -->
<div class="footer">
  GENERATED · VISUAL_BRANDING_AB_TEST_DASHBOARD · 3,000 SYNTHETIC DATA POINTS · PLOTLY 2.27.0
</div>

</body>
</html>"""

# ── 6. EXPORT & DOWNLOAD ─────────────────────────────────────
output_file = "Visual_Branding_AB_Test_Dashboard.html"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\n✅ Dashboard saved as '{output_file}'")
print(f"📦 File size: {len(html) / 1024:.1f} KB")

# Auto-download in Colab
try:
    from google.colab import files
    files.download(output_file)
    print("⬇️  Download triggered.")
except ImportError:
    print("ℹ️  Not in Colab — open the HTML file manually from your working directory.")
