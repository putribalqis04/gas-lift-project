import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="Pro Gas Lift Design & Validator", layout="wide", page_icon="🤖")

st.title("🤖 Gas Lift Design & Smart Validator")
st.markdown("### Graphical Construction with Constraint-Based Valve Selection")

# --- SIDEBAR INPUTS ---
st.sidebar.header("📁 Well & Reservoir Data")
depth_total = st.sidebar.number_input("Total Well Depth (ft)", value=10000)
p_s = st.sidebar.number_input("Static Pressure (Ps), psig", value=3000)
p_wf = st.sidebar.number_input("Flowing Pressure (Pwf), psig", value=2867)
p_wh = st.sidebar.number_input("Wellhead Pressure (Pwh), psig", value=100)

st.sidebar.header("📁 Injection Pressures")
p_ko_surf = st.sidebar.number_input("Kick-off Pressure (Pko), psig", value=1000)
p_so_surf = st.sidebar.number_input("Operating Pressure (Pso), psig", value=950)

st.sidebar.header("📁 Gradients & Constraints")
gs = st.sidebar.number_input("Kill Fluid Gradient (Gs), psi/ft", value=0.455, format="%.3f")
gpko = st.sidebar.number_input("Gas Kick-off Gradient, psi/ft", value=0.025, format="%.3f")
gpso = st.sidebar.number_input("Gas Operating Gradient, psi/ft", value=0.022, format="%.3f")
min_space = st.sidebar.number_input("Min Spacing (ft)", value=300)
min_spread = st.sidebar.number_input("Min Spread (psi)", value=100)

# --- CALCULATIONS ---

# 1. Geometry Construction
wfl_depth = depth_total - (p_wf / gs)
sfl_depth = depth_total - (p_s / gs)
p_ko_td = p_ko_surf + (gpko * depth_total)
p_so_td = p_so_surf + (gpso * depth_total)

# 2. Key Intersections
d_pob = (p_so_surf - p_wf + gs * depth_total) / (gs - gpso)
p_pob = p_so_surf + (gpso * d_pob)
p_target = p_pob - 100 # Differential at DPOI
d_dpoi = depth_total - ((p_wf - p_target) / gs)

# Lifted Gradient slope (Red Line)
g_fa = (p_target - p_wh) / d_dpoi

# 3. Smart Valve Selection Logic
final_valves = []
skipped_valves = []
curr_d = 0
last_valid_d = 0
v_num = 1

# Iterate to find valves
while curr_d < d_dpoi and v_num < 15:
    # 1st Valve calculation vs Subsequent
    if v_num == 1:
        candidate_d = (p_ko_surf - 50 - p_wh) / gs
    else:
        p_so_at_d = p_so_surf + (gpso * last_valid_d)
        p_tub_at_d = p_wh + (g_fa * last_valid_d)
        increment = (p_so_at_d - p_tub_at_d) / gs
        candidate_d = last_valid_d + increment

    # STOP if we pass DPOI
    if candidate_d >= d_dpoi:
        break

    # VALIDATION RULES
    p_casing = p_so_surf + (gpso * candidate_d)
    p_tubing = p_wh + (g_fa * candidate_d)
    spread = p_casing - p_tubing
    spacing = candidate_d - last_valid_d

    # Rule Checking
    fail_reason = ""
    if v_num > 1 and spacing < min_space:
        fail_reason = f"Spacing {spacing:.0f}ft < {min_space}ft"
    elif spread < min_spread:
        fail_reason = f"Spread {spread:.0f}psi < {min_spread}psi"

    if fail_reason == "":
        # ACCEPT
        final_valves.append({
            "ID": f"Valve {v_num}",
            "Depth": round(candidate_d, 0),
            "Pressure": round(p_tubing, 1),
            "Status": "✅ Accepted"
        })
        last_valid_d = candidate_d
    else:
        # SKIP
        skipped_valves.append({
            "ID": f"Valve {v_num}",
            "Reason": fail_reason
        })
    
    curr_d = candidate_d
    v_num += 1

# Add Operating Point as final
final_valves.append({"ID": "Operating Valve", "Depth": round(d_dpoi, 0), "Pressure": round(p_target, 1), "Status": "🎯 Target"})

# --- VISUALIZATION ---
fig = go.Figure()

# Construction Lines (Extended to axes)
fig.add_trace(go.Scatter(x=[p_ko_surf, p_ko_td], y=[0, depth_total], name="Kick-off Pressure", line=dict(color='green', dash='dot', width=1)))
fig.add_trace(go.Scatter(x=[p_so_surf, p_so_td], y=[0, depth_total], name="Operating Pressure", line=dict(color='green', width=3)))
fig.add_trace(go.Scatter(x=[0, p_s], y=[sfl_depth, depth_total], name="Static Gradient", line=dict(color='orange', dash='dash')))
fig.add_trace(go.Scatter(x=[0, p_wf], y=[wfl_depth, depth_total], name="Working Gradient", line=dict(color='blue', width=3)))
fig.add_trace(go.Scatter(x=[p_wh, p_target], y=[0, d_dpoi], name="Lifted Gradient (Flowing)", line=dict(color='red', width=3)))

# Intercepts
fig.add_trace(go.Scatter(x=[p_pob], y=[d_pob], name="POB (Balance Point)", mode="markers", marker=dict(size=14, color='cyan', symbol='circle', line=dict(width=2, color='black'))))
fig.add_trace(go.Scatter(x=[p_target], y=[d_dpoi], name="DPOI (Target)", mode="markers", marker=dict(size=16, color='yellow', symbol='star', line=dict(width=1, color='red'))))

# Accepted Valves (On Red Line)
v_df = pd.DataFrame(final_valves)
fig.add_trace(go.Scatter(x=v_df['Pressure'], y=v_df['Depth'], mode='markers+text', name="Selected Valves",
                         text=v_df['ID'], textposition="middle right",
                         marker=dict(size=10, color='red', symbol='triangle-left', line=dict(width=1, color='black'))))

fig.update_layout(
    title="Professional Gas Lift Construction & Valve Analysis",
    xaxis_title="Pressure (psig)", yaxis_title="Depth (ft)",
    yaxis=dict(autorange="reversed", range=[depth_total, 0]),
    xaxis=dict(range=[0, max(p_s, p_ko_td) + 200]),
    template="plotly_white", height=800,
    legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
    margin=dict(r=150)
)

# --- DISPLAY ---
col_graph, col_info = st.columns([2.2, 1])

with col_graph:
    st.plotly_chart(fig, use_container_width=True)

with col_info:
    st.subheader("📋 Selection Results")
    st.dataframe(v_df[['ID', 'Depth', 'Status']], hide_index=True)
    
    if skipped_valves:
        st.warning("⚠️ Engineering Exceptions")
        for sv in skipped_valves:
            st.write(f"**{sv['ID']}** was skipped: *{sv['Reason']}*")
    
    st.divider()
    st.subheader("🤖 Smart Interpretation")
    if len(skipped_valves) > 0:
        st.info("The system skipped redundant valves to maintain design stability and cost efficiency.")
    
    st.metric("Final Injection Depth", f"{d_dpoi:.0f} ft")
    st.metric("Point of Balance", f"{d_pob:.0f} ft")
