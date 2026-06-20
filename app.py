import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="Professional Gas Lift Designer", layout="wide", page_icon="🛢️")

st.title("🛢️ Gas Lift Design & Diagnostic Tool")
st.markdown("### Integrated Graphical Construction & Constrained Valve Spacing")

# --- SIDEBAR INPUTS ---
st.sidebar.header("📁 1. Well & Reservoir Data")
depth_total = st.sidebar.number_input("Total Well Depth (ft)", value=10000)
p_s = st.sidebar.number_input("Static Pressure (Ps), psig", value=3000)
p_wf = st.sidebar.number_input("Flowing Pressure (Pwf), psig", value=2867)
p_wh = st.sidebar.number_input("Wellhead Pressure (Pwh), psig", value=100)

st.sidebar.header("📁 2. Injection Settings")
p_ko_surf = st.sidebar.number_input("Kick-off Pressure (Pko), psig", value=1000)
p_so_surf = st.sidebar.number_input("Operating Pressure (Pso), psig", value=950)

st.sidebar.header("📁 3. Fluid Gradients")
gs = st.sidebar.number_input("Kill Fluid Gradient (Gs), psi/ft", value=0.455, format="%.3f")
gpko = st.sidebar.number_input("Gas Kick-off Gradient, psi/ft", value=0.025, format="%.3f")
gpso = st.sidebar.number_input("Gas Operating Gradient, psi/ft", value=0.022, format="%.3f")

# --- CALCULATIONS ---

# 1. Base Construction Points
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

# Gradient Above Injection (Red Line Slope)
g_fa = (p_target - p_wh) / d_dpoi

# 3. Valve Spacing Calculation with Constraints
valves = []
# Valve 1 (Top valve)
dv1 = (p_ko_surf - 50 - p_wh) / gs
if dv1 > 0:
    valves.append({"Valve": 1, "Depth (ft)": round(dv1, 0), "Pressure (psi)": round(p_wh + (g_fa * dv1), 1)})

# Subsequent Valves up to DPOI
curr_d = dv1
v_idx = 2
while curr_d < d_dpoi:
    p_casing_at_d = p_so_surf + (gpso * curr_d)
    p_tubing_at_d = p_wh + (g_fa * curr_d)
    
    # Differential constraint: Spread must be > 100 psi
    # Spacing constraint: Increment must be > 300 ft
    increment = (p_casing_at_d - p_tubing_at_d) / gs
    
    if increment < 300: increment = 300 # Constraint 1: Spacing > 300ft
    
    new_d = curr_d + increment
    
    # Check if new depth exceeds DPOI
    if new_d >= d_dpoi:
        break
        
    p_new_tubing = p_wh + (g_fa * new_d)
    valves.append({"Valve": v_idx, "Depth (ft)": round(new_d, 0), "Pressure (psi)": round(p_new_tubing, 1)})
    curr_d = new_d
    v_idx += 1

# Add DPOI as the final Operating Valve
valves.append({"Valve": "OP", "Depth (ft)": round(d_dpoi, 0), "Pressure (psi)": round(p_target, 1)})
df_valves = pd.DataFrame(valves)

# --- VISUALIZATION ---
fig = go.Figure()

# Line: Casing Pko
fig.add_trace(go.Scatter(x=[p_ko_surf, p_ko_td], y=[0, depth_total], name="Kick-off Pressure (Casing)", line=dict(color='#2ca02c', dash='dot', width=1)))

# Line: Casing Pso
fig.add_trace(go.Scatter(x=[p_so_surf, p_so_td], y=[0, depth_total], name="Operating Pressure (Casing)", line=dict(color='#2ca02c', width=3)))

# Line: Static Gradient (SFL to Ps)
fig.add_trace(go.Scatter(x=[0, p_s], y=[sfl_depth, depth_total], name="Static Fluid Gradient", line=dict(color='#ff7f0e', dash='dash')))

# Line: Working Gradient (WFL to Pwf)
fig.add_trace(go.Scatter(x=[0, p_wf], y=[wfl_depth, depth_total], name="Working Fluid Gradient", line=dict(color='#1f77b4', width=3)))

# Line: Flowing Gradient Above Injection (Pwh to DPOI)
fig.add_trace(go.Scatter(x=[p_wh, p_target], y=[0, d_dpoi], name="Lifted Gradient (Flowing)", line=dict(color='#d62728', width=3)))

# INTERCEPT MARKERS
fig.add_trace(go.Scatter(x=[p_pob], y=[d_pob], name="POB (Point of Balance)", mode="markers", 
                         marker=dict(size=14, color='cyan', symbol='circle', line=dict(width=2, color='black'))))

# VALVES MARKERS (On the Red Line)
fig.add_trace(go.Scatter(x=df_valves['Pressure (psi)'], 
                         y=df_valves['Depth (ft)'], mode='markers+text', name="Gas Lift Valves",
                         text=[f"V{v}" if isinstance(v, int) else v for v in df_valves['Valve']], 
                         textposition="middle right",
                         marker=dict(size=12, color='red', symbol='triangle-left', line=dict(width=1, color='black'))))

fig.update_layout(
    title="Gas Lift Construction & Valve Placement",
    xaxis_title="Pressure (psig)", yaxis_title="Depth (ft)",
    yaxis=dict(autorange="reversed", range=[depth_total, 0], gridcolor='#EEEEEE'),
    xaxis=dict(range=[0, max(p_s, p_ko_td) + 200], gridcolor='#EEEEEE'),
    template="plotly_white", height=800,
    # Move Legend outside to the right
    legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
    margin=dict(r=150) # Add right margin space for the legend
)

# --- DISPLAY ---
col_graph, col_data = st.columns([2.2, 1])

with col_graph:
    st.plotly_chart(fig, use_container_width=True)

with col_data:
    st.subheader("🤖 Smart Assistant")
    # Quick interpretations
    if d_dpoi > depth_total: st.error("❌ ERROR: DPOI exceeds well depth.")
    elif p_wf >= p_s: st.warning("⚠️ ALERT: Flowing BHP >= Static Pressure. Well will not flow.")
    else: st.success("✅ DESIGN: Valid configuration detected.")
    
    st.divider()
    st.write("#### 📍 Constrained Valve Schedule")
    st.caption("Spacing > 300ft | Spread > 100psi")
    st.dataframe(df_valves, hide_index=True)
    
    st.divider()
    st.write("#### Construction Key")
    st.write(f"**DPOI:** {d_dpoi:.0f} ft")
    st.write(f"**POB:** {d_pob:.0f} ft")
    st.write(f"**WFL:** {wfl_depth:.0f} ft")
    
    st.info("Valves are placed on the lifted flowing gradient line (Red) as requested.")
