import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="GLIS: Gas Lift Intelligent System", layout="wide", page_icon="🚀")

# --- APP TITLE ---
st.title("🚀 GLIS: Gas Lift Intelligent System")
st.markdown("##### Professional Gas Lift Design & Diagnostic Suite | Option B Specialist")
st.divider()

# --- SIDEBAR INPUTS ---
st.sidebar.header("📁 Field Data Input")
depth_total = st.sidebar.number_input("Total Well Depth (ft)", value=10000)
p_s = st.sidebar.number_input("Static Reservoir Pressure (Ps), psi", value=3000)
p_wf = st.sidebar.number_input("Flowing BHP (Pwf), psi", value=2867)
p_wh = st.sidebar.number_input("Wellhead Pressure (Pwh), psi", value=100)

st.sidebar.header("📁 Injection Setup")
p_ko_surf = st.sidebar.number_input("Surface Kick-off Pressure (Pko), psi", value=1000)
p_so_surf = st.sidebar.number_input("Surface Operating Pressure (Pso), psi", value=950)

st.sidebar.header("📁 Design Constraints")
gs = st.sidebar.number_input("Kill Fluid Gradient (Gs), psi/ft", value=0.455, format="%.3f")
gpko = st.sidebar.number_input("Gas Kick-off Gradient (Gpko), psi/ft", value=0.025, format="%.3f")
gpso = st.sidebar.number_input("Gas Operating Gradient (Gpso), psi/ft", value=0.022, format="%.3f")
min_space = st.sidebar.number_input("Min. Spacing Constraint (ft)", value=300)
min_spread = st.sidebar.number_input("Min. Valve Spread (psi)", value=100)

# --- CALCULATIONS ---

# 1. Graphical Construction Points (Using requested formulas)
sfl_depth = depth_total - (p_s / gs)    # SFL Line Calculation
wfl_depth = depth_total - (p_wf / gs)   # WFL Line Calculation
p_ko_td = p_ko_surf + (gpko * depth_total) # Pko @ Depth
p_so_td = p_so_surf + (gpso * depth_total) # Pso @ Depth

# 2. Key Intersections
# Point of Balance (POB)
d_pob = (p_so_surf - p_wf + gs * depth_total) / (gs - gpso)
p_pob = p_so_surf + (gpso * d_pob)

# DPOI Logic (100psi offset from POB)
p_target = p_pob - 100 
d_dpoi = depth_total - ((p_wf - p_target) / gs)
g_fa = (p_target - p_wh) / d_dpoi # Lifted gradient slope

# 3. Iterative Valve Selection with Rejection Logging
final_valves = []
rejections = []
last_valid_d = 0
v_idx = 1
curr_candidate_d = 0

while curr_candidate_d < d_dpoi and v_idx < 15:
    if v_idx == 1:
        candidate_d = (p_ko_surf - 50 - p_wh) / gs
    else:
        p_so_at_d = p_so_surf + (gpso * last_valid_d)
        p_tub_at_d = p_wh + (g_fa * last_valid_d)
        increment = (p_so_at_d - p_tub_at_d) / gs
        candidate_d = last_valid_d + increment

    if candidate_d >= d_dpoi: break

    # Validation Checks
    p_casing_cand = p_so_surf + (gpso * candidate_d)
    p_tubing_cand = p_wh + (g_fa * candidate_d)
    spread = p_casing_cand - p_tubing_cand
    spacing = candidate_d - last_valid_d

    fail_reason = ""
    if v_idx > 1 and spacing < min_space:
        fail_reason = f"Insufficient Spacing ({spacing:.0f} ft)"
    elif spread < min_spread:
        fail_reason = f"Insufficient Spread ({spread:.0f} psi)"

    if fail_reason == "":
        final_valves.append({"ID": f"Valve {v_idx}", "Depth": round(candidate_d, 0), "Pressure": round(p_tubing_cand, 1)})
        last_valid_d = candidate_d
    else:
        rejections.append({"ID": f"Candidate {v_idx}", "Attempted Depth": round(candidate_d, 0), "Reason": fail_reason})
    
    curr_candidate_d = candidate_d
    v_idx += 1

final_valves.append({"ID": "Operating Valve", "Depth": round(d_dpoi, 0), "Pressure": round(p_target, 1)})
v_df = pd.DataFrame(final_valves)

# --- UI LAYOUT ---
tab1, tab2, tab3 = st.tabs(["📈 Design Construction", "🤖 Engineer's Assistant", "📚 Gas Lift Academy"])

with tab1:
    fig = go.Figure()
    # Gradient Lines
    fig.add_trace(go.Scatter(x=[0, p_wf], y=[wfl_depth, depth_total], name="Working Fluid Gradient", line=dict(color='#1f77b4', width=3)))
    fig.add_trace(go.Scatter(x=[0, p_s], y=[sfl_depth, depth_total], name="Static Fluid Gradient", line=dict(color='#ff7f0e', dash='dash')))
    fig.add_trace(go.Scatter(x=[p_ko_surf, p_ko_td], y=[0, depth_total], name="Kick-off Casing (Pko)", line=dict(color='#2ca02c', dash='dot', width=1.5)))
    fig.add_trace(go.Scatter(x=[p_so_surf, p_so_td], y=[0, depth_total], name="Operating Casing (Pso)", line=dict(color='#2ca02c', width=3)))
    fig.add_trace(go.Scatter(x=[p_wh, p_target], y=[0, d_dpoi], name="Lifted Flowing Gradient", line=dict(color='#d62728', width=3)))
    
    # Construction Points
    fig.add_trace(go.Scatter(x=[p_pob], y=[d_pob], name="POB (Balance Point)", mode="markers", marker=dict(size=14, color='cyan', line=dict(width=2, color='black'))))
    fig.add_trace(go.Scatter(x=[p_target], y=[d_dpoi], name="DPOI (Injection Point)", mode="markers", marker=dict(size=18, color='yellow', symbol='star', line=dict(width=1, color='red'))))
    
    # Selected Valves
    fig.add_trace(go.Scatter(x=v_df['Pressure'], y=v_df['Depth'], mode='markers+text', name="Final Valves", text=v_df['ID'], textposition="middle right", marker=dict(size=10, color='red', symbol='triangle-left')))

    fig.update_layout(yaxis=dict(autorange="reversed"), template="plotly_white", height=700, xaxis_title="Pressure (psig)", yaxis_title="Depth (ft)", legend=dict(yanchor="top", y=0.99, xanchor="left", x=1.02))
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("📋 Final Valve Schedule")
    st.dataframe(v_df, hide_index=True, use_container_width=True)
    
    if rejections:
        st.warning("⚠️ Rejected Valve Candidates")
        st.dataframe(pd.DataFrame(rejections), hide_index=True, use_container_width=True)

    st.divider()
    st.subheader("🧮 Technical Calculation Summary")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        st.write("**Fluid Level Construction:**")
        st.latex(rf"SFL = {depth_total} - \frac{{{p_s}}}{{{gs}}} = {sfl_depth:.0f} \text{{ ft}}")
        st.latex(rf"WFL = {depth_total} - \frac{{{p_wf}}}{{{gs}}} = {wfl_depth:.0f} \text{{ ft}}")
    with col_f2:
        st.write("**Casing Pressure at TD:**")
        st.latex(rf"P_{{ko\_depth}} = {p_ko_surf} + ({gpko} \times {depth_total}) = {p_ko_td:.1f} \text{{ psi}}")
        st.latex(rf"P_{{so\_depth}} = {p_so_surf} + ({gpso} \times {depth_total}) = {p_so_td:.1f} \text{{ psi}}")

with tab3:
    st.header("📖 Gas Lift Academy")
    with st.expander("1. Construction Formulas Used"):
        st.write("The app uses the following formulas as per industry standards:")
        st.markdown("- **Static Fluid Level (SFL):** Depth where reservoir pressure is balanced by the static fluid column.")
        st.latex(r"SFL = Depth_{Total} - \frac{P_s}{G_s}")
        st.markdown("- **Working Fluid Level (WFL):** Depth representing the fluid column height under flowing conditions.")
        st.latex(r"WFL = Depth_{Total} - \frac{P_{wf}}{G_s}")
        st.markdown("- **Casing Pressure Profile:** Calculated by accounting for the gas column weight.")
        st.latex(r"P_{casing\_at\_depth} = P_{surface} + (G_{gas} \times Depth)")
