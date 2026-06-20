import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="UTM Gas Lift Diagnostic Tool", layout="wide", page_icon="🤖")

st.title("🤖 Gas Lift Design & Diagnostic Assistant")
st.markdown("### Exact Graphical Method with Automated Engineering Interpretation")

# --- SIDEBAR INPUTS ---
st.sidebar.header("📂 1. Reservoir & Well Data")
depth_total = st.sidebar.number_input("Total well depth (ft)", value=10000)
p_s = st.sidebar.number_input("Static Pressure (Ps), psig", value=3000)
p_wf = st.sidebar.number_input("Flowing Pressure (Pwf), psig", value=2867)
p_wh = st.sidebar.number_input("Wellhead Pressure (Pwh), psig", value=100)

st.sidebar.header("📂 2. Casing Pressures")
p_ko_surf = st.sidebar.number_input("Kick-off Pressure (Pko), psig", value=1000)
p_so_surf = st.sidebar.number_input("Operating Pressure (Pso), psig", value=950)

st.sidebar.header("📂 3. Gradients")
gs = st.sidebar.number_input("Fluid Gradient (Gs), psi/ft", value=0.455, format="%.3f")
gpko = st.sidebar.number_input("Gas Kick-off Gradient, psi/ft", value=0.025, format="%.3f")
gpso = st.sidebar.number_input("Gas Operating Gradient, psi/ft", value=0.022, format="%.3f")

# --- CALCULATIONS ---
wfl_depth = depth_total - (p_wf / gs)
sfl_depth = depth_total - (p_s / gs)
p_ko_td = p_ko_surf + (gpko * depth_total)
p_so_td = p_so_surf + (gpso * depth_total)

# Point of Balance (POB)
d_pob = (p_so_surf - p_wf + gs * depth_total) / (gs - gpso)
p_pob = p_so_surf + (gpso * d_pob)

# Deepest Point of Injection (DPOI) - 100psi offset
p_target = p_pob - 100
d_dpoi = depth_total - ((p_wf - p_target) / gs)

# --- DIAGNOSTIC LOGIC (The "Engineer's Assistant") ---
diagnostics = []

# 1. Injection Depth Analysis
if d_dpoi > depth_total:
    diagnostics.append("❌ ERROR: Calculated DPOI exceeds total depth. Check your casing pressure.")
elif d_dpoi < 2000:
    diagnostics.append("⚠️ WARNING: Injection point is too shallow. You may need higher injection pressure.")
else:
    diagnostics.append("✅ OPTIMAL: Injection point is deep enough to provide effective drawdown.")

# 2. Backpressure Analysis
if p_wh > 250:
    diagnostics.append("⚠️ ALERT: High wellhead pressure detected. This restricts production. Consider lowering separator pressure.")

# 3. Pressure Differential
p_diff = p_pob - p_target
if p_diff < 100:
    diagnostics.append("⚠️ STABILITY: Valve differential pressure is low. Risk of gas lift instability.")

# 4. Reservoir Health
drawdown = p_s - p_wf
if drawdown < 100:
    diagnostics.append("📉 DIAGNOSIS: Potential formation damage or low Productivity Index (PI) detected.")

# --- VISUALIZATION ---
fig = go.Figure()
fig.add_trace(go.Scatter(x=[0, p_wf], y=[wfl_depth, depth_total], name="WFL-Pwf Line", line=dict(color='blue', width=3)))
fig.add_trace(go.Scatter(x=[0, p_s], y=[sfl_depth, depth_total], name="SFL-Ps Line", line=dict(color='orange', dash='dash')))
fig.add_trace(go.Scatter(x=[p_so_surf, p_so_td], y=[0, depth_total], name="Pso Casing Line", line=dict(color='green', width=3)))
fig.add_trace(go.Scatter(x=[p_wh, p_target], y=[0, d_dpoi], name="Gradient Above Injection", line=dict(color='red', width=2)))
fig.add_trace(go.Scatter(x=[p_pob], y=[d_pob], name="POB (Balance)", mode="markers", marker=dict(size=12, color='black')))
fig.add_trace(go.Scatter(x=[p_target], y=[d_dpoi], name="DPOI (Injection)", mode="markers", marker=dict(size=15, color='red', symbol='star')))

fig.update_layout(yaxis=dict(autorange="reversed"), template="plotly_white", height=700, 
                  xaxis_title="Pressure (psig)", yaxis_title="Depth (ft)")

# --- DISPLAY ---
col1, col2 = st.columns([2, 1])

with col1:
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📋 Assistant's Interpretation")
    for msg in diagnostics:
        if "❌" in msg: st.error(msg)
        elif "⚠️" in msg: st.warning(msg)
        elif "✅" in msg: st.success(msg)
        else: st.info(msg)
    
    st.divider()
    st.metric("Injection Depth", f"{d_dpoi:.0f} ft")
    st.metric("Valve Pressure (Pvd)", f"{p_target:.1f} psi")
    st.info(f"The assistant analyzed your data based on Slide 18 graphical construction rules.")
