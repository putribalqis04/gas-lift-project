import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="GLIS: Gas Lift Intelligent System", layout="wide", page_icon="🚀")

# --- LOGO & HEADER FAIL-SAFE ---
logo_file = "Well_Performance_App/logo.png"
if not os.path.exists(logo_file):
    logo_file = "Well_Performance_App/logo.png.jpeg"
if not os.path.exists(logo_file):
    logo_file = "logo.png"
if not os.path.exists(logo_file):
    logo_file = "logo.png.jpeg"

try:
    col_l, col_t = st.columns([1, 4])
    with col_l:
        st.image(logo_file, width=150)
    with col_t:
        st.title("Gas Lift Intelligent System (GLIS)")
        st.markdown("##### Smart Design • Optimized Performance | *Option B Specialist Tool*")
except:
    st.title("🚀 Gas Lift Intelligent System (GLIS)")
    st.markdown("##### Smart Design • Optimized Performance")

st.divider()

# --- SIDEBAR INPUTS ---
st.sidebar.header("📂 Field Data Input")
depth_total = st.sidebar.number_input("Total Well Depth (ft)", value=10000)
p_s = st.sidebar.number_input("Static Reservoir Pressure (Ps), psi", value=3000)
p_wf = st.sidebar.number_input("Flowing BHP (Pwf), psi", value=2867)
p_wh = st.sidebar.number_input("Wellhead Pressure (Pwh), psi", value=100)

st.sidebar.header("📂 Injection Setup")
p_ko_surf = st.sidebar.number_input("Surface Kick-off Pressure (Pko), psi", value=1000)
p_so_surf = st.sidebar.number_input("Surface Operating Pressure (Pso), psi", value=950)

st.sidebar.header("📂 Design Constraints")
gs = st.sidebar.number_input("Kill Fluid Gradient (Gs), psi/ft", value=0.455, format="%.3f")
gpko = st.sidebar.number_input("Gas Kick-off Gradient (Gpko), psi/ft", value=0.025, format="%.3f")
gpso = st.sidebar.number_input("Gas Operating Gradient (Gpso), psi/ft", value=0.022, format="%.3f")
min_space = st.sidebar.number_input("Min. Spacing Constraint (ft)", value=300)
min_spread = st.sidebar.number_input("Min. Valve Spread (psi)", value=100)

# --- CALCULATIONS ---
# Fluid levels and Casing at Depth
sfl_depth = depth_total - (p_s / gs)    
wfl_depth = depth_total - (p_wf / gs)   
p_ko_td = p_ko_surf + (gpko * depth_total) # Pko @ Depth
p_so_td = p_so_surf + (gpso * depth_total) # Pso @ Depth

# Point of Balance (POB)
d_pob = (p_so_surf - p_wf + gs * depth_total) / (gs - gpso)
p_pob = p_so_surf + (gpso * d_pob)

# DPOI Logic (100psi offset from POB)
p_target = p_pob - 100 
d_dpoi = depth_total - ((p_wf - p_target) / gs)
g_fa = (p_target - p_wh) / d_dpoi # Lifted gradient slope

# Smart Valve Logic with Rejection Logging
final_valves = []
rejections = []
last_valid_d = 0
v_idx = 1
curr_cand_d = 0

while curr_cand_d < d_dpoi and v_idx < 15:
    if v_idx == 1:
        candidate_d = (p_ko_surf - 50 - p_wh) / gs
    else:
        p_so_at_d = p_so_surf + (gpso * last_valid_d)
        p_tub_at_d = p_wh + (g_fa * last_valid_d)
        increment = (p_so_at_d - p_tub_at_d) / gs
        candidate_d = last_valid_d + increment
    if candidate_d >= d_dpoi: break
    
    # Validation Rules
    p_cas_cand = p_so_surf + (gpso * candidate_d)
    p_tub_cand = p_wh + (g_fa * candidate_d)
    spread = p_cas_cand - p_tub_cand
    spacing = candidate_d - last_valid_d

    if (v_idx == 1 or spacing >= min_space) and spread >= min_spread:
        final_valves.append({"ID": f"Valve {v_idx}", "Depth": round(candidate_d, 0), "Pressure": round(p_tub_cand, 1), "Status": "Accepted"})
        last_valid_d = candidate_d
    else:
        reason = "Spacing" if spacing < min_space else "Spread"
        rejections.append({"ID": f"Valve {v_idx}", "Depth": round(candidate_d, 0), "Reason": f"Low {reason}"})
    
    curr_cand_d = candidate_d
    v_idx += 1

final_valves.append({"ID": "Operating Valve", "Depth": round(d_dpoi, 0), "Pressure": round(p_target, 1), "Status": "DPOI"})
v_df = pd.DataFrame(final_valves)

# --- UI TABS ---
tab1, tab2, tab3 = st.tabs(["📈 Design Construction", "🤖 Engineer's Assistant", "📚 Gas Lift Academy"])

with tab1:
    fig = go.Figure()
    # Gradient Lines (all touching axes)
    fig.add_trace(go.Scatter(x=[0, p_wf], y=[wfl_depth, depth_total], name="Working Fluid Gradient", line=dict(color='#1f77b4', width=3)))
    fig.add_trace(go.Scatter(x=[0, p_s], y=[sfl_depth, depth_total], name="Static Fluid Gradient", line=dict(color='#ff7f0e', dash='dash')))
    
    # Casing Lines
    fig.add_trace(go.Scatter(x=[p_ko_surf, p_ko_td], y=[0, depth_total], name="Kick-off Casing (Pko)", line=dict(color='#2ca02c', dash='dot', width=1.5)))
    fig.add_trace(go.Scatter(x=[p_so_surf, p_so_td], y=[0, depth_total], name="Operating Casing (Pso)", line=dict(color='#2ca02c', width=3)))
    
    # Lifted Gradient Line
    fig.add_trace(go.Scatter(x=[p_wh, p_target], y=[0, d_dpoi], name="Lifted Flowing Gradient", line=dict(color='#d62728', width=3)))
    
    # Construction Points
    fig.add_trace(go.Scatter(x=[p_pob], y=[d_pob], name="POB (Balance Point)", mode="markers", marker=dict(size=12, color='cyan', line=dict(width=2, color='black'))))
    fig.add_trace(go.Scatter(x=[p_target], y=[d_dpoi], name="DPOI (Injection Point)", mode="markers", marker=dict(size=16, color='yellow', symbol='star', line=dict(width=1, color='red'))))
    
    # Valve Markers
    fig.add_trace(go.Scatter(x=v_df['Pressure'], y=v_df['Depth'], mode='markers+text', name="Selected Valves", text=v_df['ID'], textposition="middle right", marker=dict(size=10, color='red', symbol='triangle-left')))

    fig.update_layout(yaxis=dict(autorange="reversed", range=[depth_total, 0]), xaxis=dict(range=[0, max(p_s, p_ko_td)+200]), template="plotly_white", height=800, legend=dict(yanchor="top", y=0.99, xanchor="left", x=1.02))
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("💡 Lift Method Advisor")
    estimated_rate = (p_s - p_wf) * 0.5 
    
    col_a1, col_a2 = st.columns([1, 1])
    with col_a1:
        st.write("**Current Well Conditions:**")
        st.write(f"- Reservoir Pressure: **{p_s} psi**")
        st.write(f"- Estimated Productivity: **{'Low' if estimated_rate < 300 else 'High'}**")
    with col_a2:
        st.write("**Recommended Lift Method:**")
        if estimated_rate < 300:
            st.success("✅ **Intermittent Gas Lift**")
            st.caption("**Reason:** Low production rate and insufficient continuous gas injection requirement.")
        else:
            st.success("✅ **Continuous Gas Lift**")
            st.caption("**Reason:** High production rate detected. Continuous injection will maintain stable drawdown.")

    st.divider()
    c_v1, c_v2 = st.columns(2)
    with c_v1:
        st.subheader("✅ Final Valve Schedule")
        st.dataframe(v_df[['ID', 'Depth', 'Status']], hide_index=True)
    with c_v2:
        st.subheader("❌ Rejected Candidates")
        if rejections: st.dataframe(pd.DataFrame(rejections), hide_index=True)
        else: st.write("All candidates satisfied constraints.")

    st.divider()
    st.subheader("🧮 Technical Workings")
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        st.write("**Fluid Level Calcs:**")
        st.latex(rf"SFL = {depth_total} - \frac{{{p_s}}}{{{gs}}} = {sfl_depth:.0f} \text{{ ft}}")
        st.latex(rf"WFL = {depth_total} - \frac{{{p_wf}}}{{{gs}}} = {wfl_depth:.0f} \text{{ ft}}")
    with col_w2:
        st.write("**Casing P at Depth:**")
        st.latex(rf"P_{{ko\_td}} = {p_ko_surf} + ({gpko} \times {depth_total}) = {p_ko_td:.1f} \text{{ psi}}")
        st.latex(rf"P_{{so\_td}} = {p_so_surf} + ({gpso} \times {depth_total}) = {p_so_td:.1f} \text{{ psi}}")

with tab3:
    st.header("📚 Gas Lift Academy")
    with st.expander("Analytical Derivations"):
        st.write("Formula for Stage 1 unloading depth:")
        st.latex(r"DV_1 = \frac{P_{ko} - 50 - P_{wh}}{G_{kill}}")
        st.write("Formula for Point of Balance (POB):")
        st.latex(r"D_{POB} = \frac{P_{so} - P_{wf} + (G_s \cdot Depth_{Total})}{G_s - G_{gas\_so}}")
