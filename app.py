import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="Gas Lift Design & Diagnostic Tool", layout="wide", page_icon="🛢️")

st.title("🛢️ Gas Lift Design & Diagnostic Tool")
st.markdown("### Integrated Graphical Construction & Valve Spacing")

# --- SIDEBAR INPUTS ---
st.sidebar.header("📁 1. Well & Reservoir Data")
depth_total = st.sidebar.number_input("Total Well Depth (ft)", value=10000)
p_s = st.sidebar.number_input("Static Pressure (Ps), psig", value=3000)
p_wf = st.sidebar.number_input("Flowing Pressure (Pwf), psig", value=2867)
p_wh = st.sidebar.number_input("Wellhead Pressure (Pwh), psig", value=100)

st.sidebar.header("📁 2. Injection Settings")
p_ko_surf = st.sidebar.number_input("Kick-off Pressure (Pko), psig", value=1000)
p_so_surf = st.sidebar.number_input("Operating Pressure (Pso), psig", value=950)
gu = st.sidebar.number_input("Design Unloading Gradient (Gu), psi/ft", value=0.120, format="%.3f")

st.sidebar.header("📁 3. Fluid Gradients")
gs = st.sidebar.number_input("Kill Fluid Gradient (Gs), psi/ft", value=0.455, format="%.3f")
gpko = st.sidebar.number_input("Gas Kick-off Gradient, psi/ft", value=0.025, format="%.3f")
gpso = st.sidebar.number_input("Gas Operating Gradient, psi/ft", value=0.022, format="%.3f")

# --- CALCULATIONS ---

# 1. Construction Points
wfl_depth = depth_total - (p_wf / gs)
sfl_depth = depth_total - (p_s / gs)
p_ko_td = p_ko_surf + (gpko * depth_total)
p_so_td = p_so_surf + (gpso * depth_total)

# 2. Points of Intersection
# Point of Balance (POB)
d_pob = (p_so_surf - p_wf + gs * depth_total) / (gs - gpso)
p_pob = p_so_surf + (gpso * d_pob)

# Injection Point (DPOI) - 100 psi offset logic
p_target = p_pob - 100
d_dpoi = depth_total - ((p_wf - p_target) / gs)

# 3. Valve Spacing Calculation (Analytical Method)
valves = []
# Valve 1 (Assumes unloading to Wellhead Pwh)
dv1 = (p_ko_surf - 50 - p_wh) / gs
if dv1 > 0: valves.append({"Valve": 1, "Depth (ft)": round(dv1, 0)})

# Subsequent Valves up to DPOI
curr_d = dv1
v_idx = 2
while curr_d < d_dpoi and v_idx < 10:
    # Formula: DV_next = DV_prev + (Pso_at_depth - Gu*DV_prev - Pwh) / Gs
    p_so_at_d = p_so_surf + (gpso * curr_d)
    increment = (p_so_at_d - (gu * curr_d) - p_wh) / gs
    if increment < 200: increment = 250 # Min spacing safety
    curr_d += increment
    if curr_d > d_dpoi: break
    valves.append({"Valve": v_idx, "Depth (ft)": round(curr_d, 0)})
    v_idx += 1

# Add DPOI as the final Operating Valve
valves.append({"Valve": "OP", "Depth (ft)": round(d_dpoi, 0)})
df_valves = pd.DataFrame(valves)

# --- VISUALIZATION ---
fig = go.Figure()

# Line: Casing Pko (Reaches axes)
fig.add_trace(go.Scatter(x=[p_ko_surf, p_ko_td], y=[0, depth_total], name="Kick-off Pressure (Casing)", line=dict(color='#2ca02c', dash='dot', width=1)))

# Line: Casing Pso (Reaches axes)
fig.add_trace(go.Scatter(x=[p_so_surf, p_so_td], y=[0, depth_total], name="Operating Pressure (Casing)", line=dict(color='#2ca02c', width=3)))

# Line: Static Gradient (SFL to Ps)
fig.add_trace(go.Scatter(x=[0, p_s], y=[sfl_depth, depth_total], name="Static Fluid Gradient", line=dict(color='#ff7f0e', dash='dash')))

# Line: Working Gradient (WFL to Pwf)
fig.add_trace(go.Scatter(x=[0, p_wf], y=[wfl_depth, depth_total], name="Working Fluid Gradient", line=dict(color='#1f77b4', width=3)))

# Line: Flowing Gradient Above Injection (Pwh to DPOI)
fig.add_trace(go.Scatter(x=[p_wh, p_target], y=[0, d_dpoi], name="Gradient Above Valve", line=dict(color='#d62728', width=2)))

# INTERCEPT MARKERS
fig.add_trace(go.Scatter(x=[p_pob], y=[d_pob], name="POB (Balance Point)", mode="markers", 
                         marker=dict(size=14, color='cyan', symbol='circle', line=dict(width=2, color='black'))))

# VALVES MARKERS
fig.add_trace(go.Scatter(x=[p_wh + (gu * d) for d in df_valves['Depth (ft)']], 
                         y=df_valves['Depth (ft)'], mode='markers+text', name="Valves",
                         text=[str(v) for v in df_valves['Valve']], textposition="top left",
                         marker=dict(size=10, color='red', symbol='triangle-left')))

fig.update_layout(
    title="Pressure-Depth Design Construction",
    xaxis_title="Pressure (psig)", yaxis_title="Depth (ft)",
    yaxis=dict(autorange="reversed", range=[depth_total, 0], gridcolor='LightGray'),
    xaxis=dict(range=[0, max(p_s, p_ko_td) + 200], gridcolor='LightGray'),
    template="plotly_white", height=800,
    legend=dict(yanchor="bottom", y=0.01, xanchor="right", x=0.99)
)

# --- DISPLAY ---
col_graph, col_data = st.columns([2.5, 1])

with col_graph:
    st.plotly_chart(fig, use_container_width=True)

with col_data:
    st.subheader("🤖 Engineer's Assistant")
    # Quick interpretations
    if d_dpoi > depth_total: st.error("❌ DPOI exceeds well depth!")
    elif d_dpoi < 3000: st.warning("⚠️ Injection point is too shallow.")
    else: st.success("✅ Design parameters are within optimal range.")
    
    st.divider()
    st.write("#### 📍 Calculated Valve Depths")
    st.dataframe(df_valves, hide_index=True)
    
    st.write("#### Design Key")
    st.write(f"- **DPOI:** {d_dpoi:.0f} ft")
    st.write(f"- **POB:** {d_pob:.0f} ft")
    st.write(f"- **SFL:** {sfl_depth:.0f} ft")
    
    st.info("The Red Triangles show the unloading valve sequence calculated via the Analytical Method.")
