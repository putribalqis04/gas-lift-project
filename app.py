import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="Gas Lift Design & Diagnostic Tool", layout="wide", page_icon="🛢️")

st.title("🛢️ Gas Lift Design & Diagnostic Tool")
st.markdown("### Integrated Graphical Design with Automated Interpretation")

# --- SIDEBAR INPUTS ---
st.sidebar.header("📁 Reservoir & Well Geometry")
depth_total = st.sidebar.number_input("Total well depth (ft)", value=10000)
p_s = st.sidebar.number_input("Static Reservoir Pressure (Ps), psig", value=3000)
p_wf = st.sidebar.number_input("Flowing BHP (Pwf), psig", value=2867)
p_wh = st.sidebar.number_input("Wellhead Pressure (Pwh), psig", value=100)

st.sidebar.header("📁 Injection Pressures")
p_ko_surf = st.sidebar.number_input("Surface Kick-off Pressure (Pko), psig", value=1000)
p_so_surf = st.sidebar.number_input("Surface Operating Pressure (Pso), psig", value=950)

st.sidebar.header("📁 Gradients")
gs = st.sidebar.number_input("Fluid Gradient (Gs), psi/ft", value=0.455, format="%.3f")
gpko = st.sidebar.number_input("Gas Kick-off Gradient, psi/ft", value=0.025, format="%.3f")
gpso = st.sidebar.number_input("Gas Operating Gradient, psi/ft", value=0.022, format="%.3f")

# --- CALCULATIONS ---
# Fluid Levels
wfl_depth = depth_total - (p_wf / gs)
sfl_depth = depth_total - (p_s / gs)

# Casing Pressures at Depth
p_ko_td = p_ko_surf + (gpko * depth_total)
p_so_td = p_so_surf + (gpso * depth_total)

# Intersection: Point of Balance (POB)
# Intersection of Tubing Gradient (WFL-Pwf) and Casing Gradient (Pso)
d_pob = (p_so_surf - p_wf + gs * depth_total) / (gs - gpso)
p_pob = p_so_surf + (gpso * d_pob)

# Injection Point (DPOI) - 100 psi offset logic
p_target = p_pob - 100
d_dpoi = depth_total - ((p_wf - p_target) / gs)

# --- SMART ASSISTANT INTERPRETATIONS ---
diagnostics = []

# 1. Lift Potential
if d_dpoi > depth_total:
    diagnostics.append("❌ ERROR: Required injection depth exceeds well depth. Increase casing pressure.")
elif d_dpoi < (depth_total * 0.3):
    diagnostics.append("⚠️ WARNING: Injection is very shallow. Artificial lift efficiency will be low.")
else:
    diagnostics.append("✅ SUCCESS: Deep injection point achieved for maximum drawdown.")

# 2. Backpressure Analysis
if p_wh > 200:
    diagnostics.append("⚠️ RESTRICTION: Operating point indicates high wellhead pressure/tubing restriction.")
else:
    diagnostics.append("✅ OPTIMAL: Low wellhead backpressure detected.")

# 3. Reservoir Analysis
if (p_s - p_wf) < 150:
    diagnostics.append("📉 DIAGNOSIS: Potential formation damage detected (Low Drawdown).")
else:
    diagnostics.append("📈 STATUS: Productivity index appears healthy.")

# --- VISUALIZATION ---
fig = go.Figure()

# Tubing Lines
fig.add_trace(go.Scatter(x=[0, p_wf], y=[wfl_depth, depth_total], name="Working Fluid Gradient", line=dict(color='#1f77b4', width=3)))
fig.add_trace(go.Scatter(x=[0, p_s], y=[sfl_depth, depth_total], name="Static Fluid Gradient", line=dict(color='#ff7f0e', dash='dash')))

# Casing Lines
fig.add_trace(go.Scatter(x=[p_ko_surf, p_ko_td], y=[0, depth_total], name="Kick-off Pressure (Casing)", line=dict(color='#2ca02c', dash='dot', width=1.5)))
fig.add_trace(go.Scatter(x=[p_so_surf, p_so_td], y=[0, depth_total], name="Operating Pressure (Casing)", line=dict(color='#2ca02c', width=3)))

# Lifted Gradient Line
fig.add_trace(go.Scatter(x=[p_wh, p_target], y=[0, d_dpoi], name="Lifted Gradient (Flowing)", line=dict(color='#d62728', width=2)))

# Intercept Points
fig.add_trace(go.Scatter(x=[p_pob], y=[d_pob], name="POB (Balance Point)", mode="markers", 
                         marker=dict(size=14, color='cyan', symbol='circle', line=dict(width=2, color='black'))))

fig.add_trace(go.Scatter(x=[p_target], y=[d_dpoi], name="Injection Valve (DPOI)", mode="markers", 
                         marker=dict(size=18, color='yellow', symbol='star', line=dict(width=1, color='red'))))

fig.update_layout(
    title="Gas Lift Pressure-Depth Construction",
    xaxis_title="Pressure (psig)",
    yaxis_title="Depth (ft)",
    yaxis=dict(autorange="reversed", gridcolor='LightGray'),
    xaxis=dict(gridcolor='LightGray'),
    template="plotly_white",
    height=800,
    legend=dict(yanchor="bottom", y=0.01, xanchor="right", x=0.99)
)

# --- DISPLAY ---
col_graph, col_assist = st.columns([2.5, 1])

with col_graph:
    st.plotly_chart(fig, use_container_width=True)

with col_assist:
    st.subheader("🤖 Engineer's Assistant")
    for msg in diagnostics:
        if "❌" in msg: st.error(msg)
        elif "⚠️" in msg: st.warning(msg)
        elif "✅" in msg: st.success(msg)
        else: st.info(msg)
    
    st.divider()
    st.write("#### Design Summary")
    st.metric("Injection Depth", f"{d_dpoi:.0f} ft")
    st.metric("Balance Depth", f"{d_pob:.0f} ft")
    st.metric("Drawdown", f"{p_s - p_wf:.0f} psi")
    
    st.info("💡 Adjust values in the sidebar to see real-time graphical updates and diagnostic warnings.")
