import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="UTM Gas Lift Graphical Tool", layout="wide", page_icon="📈")

st.title("📈 Gas Lift Design: Exact Graphical Method")
st.markdown("### Based on Chapter 3: Slide 18 logic (POB & DPOI Construction)")

# --- SIDEBAR INPUTS (Example 3, Slide 17-18) ---
st.sidebar.header("📂 1. Reservoir & Well Data")
depth_total = st.sidebar.number_input("Total well depth (ft)", value=10000)
p_s = st.sidebar.number_input("Static Reservoir Pressure (Ps), psig", value=3000)
p_wf = st.sidebar.number_input("Flowing Bottomhole Pressure (Pwf), psig", value=2867)
p_wh = st.sidebar.number_input("Wellhead Pressure (Pwh), psig", value=100)

st.sidebar.header("📂 2. Casing Pressures (at Surface)")
p_ko_surf = st.sidebar.number_input("Kick-off Pressure (Pko), psig", value=1000)
p_so_surf = st.sidebar.number_input("Surface Operating Pressure (Pso), psig", value=950)

st.sidebar.header("📂 3. Gradients (psi/ft)")
gs = st.sidebar.number_input("Fluid Gradient (Gs), psi/ft", value=0.455, format="%.3f")
gpko = st.sidebar.number_input("Gas Kick-off Gradient (Gpko), psi/ft", value=0.025, format="%.3f")
gpso = st.sidebar.number_input("Gas Operating Gradient (Gpso), psi/ft", value=0.022, format="%.3f")

# --- CALCULATIONS ---

# 1. Calculate Fluid Levels (Slide 2 & 10)
# WFL is where P=0 on the Gs gradient line coming up from Pwf
# Equation: P = Pwf - Gs * (Depth_Total - Depth) -> Set P=0
wfl_depth = depth_total - (p_wf / gs)
sfl_depth = depth_total - (p_s / gs)

# 2. Points for Casing Lines at Total Depth
p_ko_td = p_ko_surf + (gpko * depth_total)
p_so_td = p_so_surf + (gpso * depth_total)

# 3. Find Point of Balance (POB)
# Intersection of:
# Line A (Tubing): P = Pwf - Gs * (Depth_Total - D)
# Line B (Casing): P = Pso_surf + Gpso * D
# Pwf - Gs*Depth_Total + Gs*D = Pso_surf + Gpso*D
# D * (Gs - Gpso) = Pso_surf - Pwf + Gs*Depth_Total
d_pob = (p_so_surf - p_wf + gs * depth_total) / (gs - gpso)
p_pob = p_so_surf + (gpso * d_pob)

# 4. Find Deepest Point of Injection (DPOI)
# Step: "100psi to the left from POB and go UP until touch WFL-Pwf line"
p_target = p_pob - 100
# Find depth on Line A where P = p_target
# p_target = Pwf - Gs * (Depth_Total - D)
# Depth_Total - D = (Pwf - p_target) / Gs
d_dpoi = depth_total - ((p_wf - p_target) / gs)

# --- VISUALIZATION ---
fig = go.Figure()

# Line 1: WFL to Pwf
fig.add_trace(go.Scatter(x=[0, p_wf], y=[wfl_depth, depth_total], 
                         name="WFL to Pwf Line (Gfb)", line=dict(color='blue', width=3)))

# Line 2: SFL to Ps
fig.add_trace(go.Scatter(x=[0, p_s], y=[sfl_depth, depth_total], 
                         name="SFL to Ps Line (Gs)", line=dict(color='orange', dash='dash')))

# Line 3: Pko (Surface to TD)
fig.add_trace(go.Scatter(x=[p_ko_surf, p_ko_td], y=[0, depth_total], 
                         name="Pko Line", line=dict(color='green', dash='dot')))

# Line 4: Pso (Surface to TD)
fig.add_trace(go.Scatter(x=[p_so_surf, p_so_td], y=[0, depth_total], 
                         name="Pso Line", line=dict(color='green', width=3)))

# Line 5: Wellhead to DPOI
fig.add_trace(go.Scatter(x=[p_wh, p_target], y=[0, d_dpoi], 
                         name="Flowing Gradient (Above Injection)", line=dict(color='red', width=2)))

# Intersection Points
fig.add_trace(go.Scatter(x=[p_pob], y=[d_pob], name="POB (Balance)", 
                         mode="markers", marker=dict(size=12, color='black', symbol='circle')))

fig.add_trace(go.Scatter(x=[p_target], y=[d_dpoi], name="DPOI (Injection)", 
                         mode="markers", marker=dict(size=15, color='red', symbol='star')))

fig.update_layout(
    title="Exact Graphical Gas Lift Design",
    xaxis_title="Pressure (psig)",
    yaxis_title="Depth (ft)",
    yaxis=dict(autorange="reversed", range=[depth_total + 500, 0]),
    xaxis=dict(range=[0, p_s + 500]),
    template="plotly_white",
    height=800,
    legend=dict(yanchor="bottom", y=0.01, xanchor="right", x=0.99)
)

# --- UI LAYOUT ---
col_plot, col_res = st.columns([2, 1])

with col_plot:
    st.plotly_chart(fig, use_container_width=True)

with col_res:
    st.success("### System Construction")
    st.metric("Point of Balance (POB)", f"{d_pob:.0f} ft")
    st.metric("Injection Depth (DPOI)", f"{d_dpoi:.0f} ft")
    
    st.divider()
    st.markdown(f"""
    **Graphical Steps Followed:**
    1. **Intersection:** POB found at **{p_pob:.1f} psi**.
    2. **Offset:** Subtracted **100 psi** differential across valve.
    3. **Intersection:** DPOI found by projecting **{p_pob - 100:.1f} psi** onto the blue flowing line.
    4. **Result:** Valve should be placed at **{d_dpoi:.0f} ft**.
    """)
    
    with st.expander("📊 View Reference Points"):
        st.write(f"WFL: {wfl_depth:.0f} ft")
        st.write(f"SFL: {sfl_depth:.0f} ft")
        st.write(f"Pko @ TD: {p_ko_td:.0f} psi")
