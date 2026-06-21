import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from PIL import Image

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="GLIS: Gas Lift Intelligent System", 
    layout="wide", 
    page_icon="🛢️"
)

# --- HEADER WITH LOGO ---
try:
    col_l, col_t = st.columns([1, 4])
    with col_l:
        st.image("Well_Performance_App/logo.png", width=150)
    with col_t:
        st.title("Gas Lift Intelligent System (GLIS)")
        st.markdown("##### Smart Design • Optimized Performance | *Option B Specialist Tool*")
except:
    st.title("Gas Lift Intelligent System (GLIS)")
    st.markdown("##### Smart Design • Optimized Performance")

st.divider()

# --- SIDEBAR INPUTS ---
st.sidebar.header("📂 Reservoir & Well Data")
depth_total = st.sidebar.number_input("Total Well Depth (ft)", value=10000)
p_s = st.sidebar.number_input("Static Reservoir Pressure (Ps), psi", value=3000)
p_wf = st.sidebar.number_input("Flowing BHP (Pwf), psi", value=2867)
p_wh = st.sidebar.number_input("Wellhead Pressure (Pwh), psi", value=100)

st.sidebar.header("📂 Injection Settings")
p_ko_surf = st.sidebar.number_input("Surface Kick-off Pressure (Pko), psi", value=1000)
p_so_surf = st.sidebar.number_input("Surface Operating Pressure (Pso), psi", value=950)

st.sidebar.header("📂 Constraints & Gradients")
gs = st.sidebar.number_input("Kill Fluid Gradient (Gs), psi/ft", value=0.455, format="%.3f")
gpko = st.sidebar.number_input("Gas Kick-off Gradient (Gpko), psi/ft", value=0.025, format="%.3f")
gpso = st.sidebar.number_input("Gas Operating Gradient (Gpso), psi/ft", value=0.022, format="%.3f")
min_space = st.sidebar.number_input("Min. Spacing Constraint (ft)", value=300)
min_spread = st.sidebar.number_input("Min. Valve Spread (psi)", value=100)

# --- CALCULATIONS ---

# 1. Construction Points
sfl_depth = depth_total - (p_s / gs)
wfl_depth = depth_total - (p_wf / gs)
p_ko_td = p_ko_surf + (gpko * depth_total)
p_so_td = p_so_surf + (gpso * depth_total)

# 2. Key Intersections
# Point of Balance (POB)
d_pob = (p_so_surf - p_wf + gs * depth_total) / (gs - gpso)
p_pob = p_so_surf + (gpso * d_pob)

# DPOI Logic
p_target = p_pob - 100 
d_dpoi = depth_total - ((p_wf - p_target) / gs)
g_fa = (p_target - p_wh) / d_dpoi # Slope of the red line

# 3. Smart Iterative Valve Selection
final_valves = []
rejections = []
last_valid_d = 0
curr_candidate_d = 0
v_idx = 1

while curr_candidate_d < d_dpoi and v_idx < 15:
    if v_idx == 1:
        candidate_d = (p_ko_surf - 50 - p_wh) / gs
    else:
        p_so_at_d = p_so_surf + (gpso * last_valid_d)
        p_tub_at_d = p_wh + (g_fa * last_valid_d)
        increment = (p_so_at_d - p_tub_at_d) / gs
        candidate_d = last_valid_d + increment

    if candidate_d >= d_dpoi: break

    # VALIDATION
    p_casing_cand = p_so_surf + (gpso * candidate_d)
    p_tubing_cand = p_wh + (g_fa * candidate_d)
    spread = p_casing_cand - p_tubing_cand
    spacing = candidate_d - last_valid_d

    fail_reason = ""
    if v_idx > 1 and spacing < min_space:
        fail_reason = f"Spacing {spacing:.0f}ft < {min_space}ft"
    elif spread < min_spread:
        fail_reason = f"Spread {spread:.0f}psi < {min_spread}psi"

    if fail_reason == "":
        final_valves.append({"ID": f"Valve {v_idx}", "Depth": round(candidate_d, 0), "Pressure": round(p_tubing_cand, 1)})
        last_valid_d = candidate_d
    else:
        rejections.append({"ID": f"Valve {v_idx}", "Attempted Depth": round(candidate_d, 0), "Reason": fail_reason})
    
    curr_candidate_d = candidate_d
    v_idx += 1

final_valves.append({"ID": "Operating Valve", "Depth": round(d_dpoi, 0), "Pressure": round(p_target, 1)})
v_df = pd.DataFrame(final_valves)

# --- VISUALIZATION ---
fig = go.Figure()

# All lines extended to axes (0,0)
fig.add_trace(go.Scatter(x=[0, p_wf], y=[wfl_depth, depth_total], name="Working Fluid Gradient", line=dict(color='#1f77b4', width=3)))
fig.add_trace(go.Scatter(x=[0, p_s], y=[sfl_depth, depth_total], name="Static Fluid Gradient", line=dict(color='#ff7f0e', dash='dash')))
fig.add_trace(go.Scatter(x=[p_ko_surf, p_ko_td], y=[0, depth_total], name="Kick-off Pressure (Casing)", line=dict(color='#2ca02c', dash='dot', width=1)))
fig.add_trace(go.Scatter(x=[p_so_surf, p_so_td], y=[0, depth_total], name="Operating Pressure (Casing)", line=dict(color='#2ca02c', width=3)))
fig.add_trace(go.Scatter(x=[p_wh, p_target], y=[0, d_dpoi], name="Lifted Flowing Gradient", line=dict(color='#d62728', width=3)))

# Reference Points
fig.add_trace(go.Scatter(x=[p_pob], y=[d_pob], name="POB (Balance Point)", mode="markers", 
                         marker=dict(size=14, color='cyan', line=dict(width=2, color='black'))))
fig.add_trace(go.Scatter(x=[p_target], y=[d_dpoi], name="DPOI (Injection)", mode="markers", 
                         marker=dict(size=18, color='yellow', symbol='star', line=dict(width=1, color='red'))))

# Valves
fig.add_trace(go.Scatter(x=v_df['Pressure'], y=v_df['Depth'], mode='markers+text', name="Selected Valves", 
                         text=v_df['ID'], textposition="middle right", 
                         marker=dict(size=10, color='red', symbol='triangle-left', line=dict(width=1, color='black'))))

fig.update_layout(
    title="Gas Lift Geometric Construction",
    xaxis_title="Pressure (psig)", yaxis_title="Depth (ft)",
    yaxis=dict(autorange="reversed", range=[depth_total, 0], gridcolor='#EEEEEE'),
    xaxis=dict(range=[0, max(p_s, p_ko_td) + 200], gridcolor='#EEEEEE'),
    template="plotly_white", height=800,
    legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
    margin=dict(r=150)
)

# --- UI LAYOUT ---
t1, t2, t3 = st.tabs(["📈 Design Construction", "🤖 Engineer's Assistant", "📚 Gas Lift Academy"])

with t1:
    st.plotly_chart(fig, use_container_width=True)

with t2:
    st.subheader("📋 Design Verdict")
    st.dataframe(v_df, hide_index=True)
    
    if rejections:
        st.warning("⚠️ Optimization Log: Rejected Candidates")
        st.write("Candidates below did not fulfill mechanical stability constraints and were bypassed:")
        st.dataframe(pd.DataFrame(rejections), hide_index=True)

    st.divider()
    st.subheader("🧮 Technical Workings")
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        st.write("**Fluid Level Calcs:**")
        st.latex(rf"SFL = {depth_total} - \frac{{{p_s}}}{{{gs}}} = {sfl_depth:.0f} \text{{ ft}}")
        st.latex(rf"WFL = {depth_total} - \frac{{{p_wf}}}{{{gs}}} = {wfl_depth:.0f} \text{{ ft}}")
    with col_w2:
        st.write("**Casing Pressure at Depth:**")
        st.latex(rf"P_{{ko\_td}} = {p_ko_surf} + ({gpko} \times {depth_total}) = {p_ko_td:.1f} \text{{ psi}}")
        st.latex(rf"P_{{so\_td}} = {p_so_surf} + ({gpso} \times {depth_total}) = {p_so_td:.1f} \text{{ psi}}")

with t3:
    st.header("📚 Gas Lift Academy: Tailored Theory")
    with st.expander("1. Mechanism of Gas Lift"):
        st.write("Gas lift increases production by reducing the weight of the fluid column. By injecting gas, we lower the flowing gradient (shown by the change from the BLUE line to the RED line).")
    with st.expander("2. Point of Balance (POB) vs DPOI"):
        st.write("The POB is where tubing and casing pressures are equal. Industry standard places the operating valve (DPOI) 100 psi offset from this point for stability.")
