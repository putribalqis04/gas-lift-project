import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="UTM Graphical Gas Lift Tool", layout="wide", page_icon="📈")

st.title("📈 Gas Lift Design: Graphical Method")
st.markdown("### Determination of Injection Point (DPOI) - Slide 10/18 Logic")

# --- SIDEBAR INPUTS (Default values from Example 3, Slide 17-18) ---
st.sidebar.header("📂 1. Reservoir & Well Data")
depth_total = st.sidebar.number_input("Total well depth (ft)", value=10000)
p_s = st.sidebar.number_input("Static Reservoir Pressure (Ps), psig", value=3000)
p_wf = st.sidebar.number_input("Flowing Bottomhole Pressure (Pwf), psig", value=2867)
p_wh = st.sidebar.number_input("Wellhead Pressure (Pwh), psig", value=100)

st.sidebar.header("📂 2. Casing Pressures")
p_ko = st.sidebar.number_input("Kick-off Pressure (Pko), psig", value=1000)
p_so = st.sidebar.number_input("Surface Operating Pressure (Pso), psig", value=950)

st.sidebar.header("📂 3. Gradients (psi/ft)")
gs = st.sidebar.number_input("Fluid Gradient (Gs/Gfb), psi/ft", value=0.455, format="%.3f")
gpko = st.sidebar.number_input("Gas Kick-off Gradient (Gpko), psi/ft", value=0.025, format="%.3f")
gpso = st.sidebar.number_input("Gas Operating Gradient (Gpso), psi/ft", value=0.022, format="%.3f")

# --- CALCULATIONS ---

# 1. Calculate Fluid Levels (Slide 2 & 10)
# SFL = Depth - (Ps / Gs)
sfl_depth = depth_total - (p_s / gs)
# WFL = Depth - (Pwf / Gs)
wfl_depth = depth_total - (p_wf / gs)

# 2. Points for lines
z = np.linspace(0, depth_total, 100)

# Casing Lines
line_pko = p_ko + (gpko * z)
line_pso = p_so + (gpso * z)

# Tubing Flowing Gradient (Below Injection - Gfb)
# Starts at Pwf at total depth and goes UP with slope Gs
line_gfb = p_wf - (gs * (depth_total - z))

# 3. Intersection Points (Slide 10/18)
# Point of Balance (POB): Where line_gfb == line_pso
# Pso + Gpso*D = Pwf - Gs*(Depth - D) -> Solve for D
d_pob = (p_wf - p_so - gs * depth_total) / (gpso - gs)
p_pob = p_so + (gpso * d_pob)

# Deepest Point of Injection (DPOI)
# DPOI is where Tubing Gradient = Casing Pressure - 100 psi (Slide 18 Step 12)
d_dpoi = (p_wf - (p_so - 100) - gs * depth_total) / (gpso - gs)
p_dpoi_casing = p_so + (gpso * d_dpoi)
p_dpoi_tubing = p_dpoi_casing - 100

# --- VISUALIZATION ---
fig = go.Figure()

# Casing Pressure Lines
fig.add_trace(go.Scatter(x=line_pko, y=z, name="Pko (Kick-off)", line=dict(color='green', dash='dot')))
fig.add_trace(go.Scatter(x=line_pso, y=z, name="Pso (Operating)", line=dict(color='green', width=3)))

# Tubing Pressure Line (Gfb)
fig.add_trace(go.Scatter(x=line_gfb, y=z, name="Gfb (Tubing Gradient)", line=dict(color='blue', width=3)))

# SFL and WFL lines (Horizontal markers)
fig.add_hline(y=sfl_depth, line_dash="dash", line_color="orange", annotation_text=f"SFL: {sfl_depth:.0f} ft")
fig.add_hline(y=wfl_depth, line_dash="dash", line_color="red", annotation_text=f"WFL: {wfl_depth:.0f} ft")

# POB and DPOI Markers
fig.add_trace(go.Scatter(x=[p_pob], y=[d_pob], name="POB (Balance)", mode="markers", marker=dict(size=12, color='black', symbol='circle')))
fig.add_trace(go.Scatter(x=[p_dpoi_tubing], y=[d_dpoi], name="DPOI (Injection)", mode="markers", marker=dict(size=15, color='red', symbol='star')))

fig.update_layout(
    title="Graphical Gas Lift Design (Pressure-Depth)",
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
    st.success("### Design Results")
    st.metric("SFL (Static Fluid Level)", f"{sfl_depth:.1f} ft")
    st.metric("WFL (Working Fluid Level)", f"{wfl_depth:.1f} ft")
    st.metric("POB (Balance Depth)", f"{d_pob:.1f} ft")
    st.metric("DPOI (Injection Depth)", f"{d_dpoi:.1f} ft", delta="Target Valve")
    
    st.divider()
    st.info("""
    **How to read the graph:**
    - **POB (Black Circle):** Where casing and tubing pressures are exactly equal.
    - **DPOI (Red Star):** The actual valve depth, allowing for a **100 psi** differential (Step 12, Slide 18).
    """)

# Data Table
with st.expander("📊 View Data Points"):
    st.write("Calculated based on your input gradients:")
    st.dataframe(pd.DataFrame({
        "Depth (ft)": [0, sfl_depth, wfl_depth, d_dpoi, d_pob, depth_total],
        "Casing P (psi)": [p_so, p_so + gpso*sfl_depth, p_so + gpso*wfl_depth, p_dpoi_casing, p_pob, p_so + gpso*depth_total],
        "Tubing P (psi)": [p_wh, 0, 0, p_dpoi_tubing, p_pob, p_wf]
    }).round(1))
