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
depth_total = st.sidebar.number_input("Total well depth (ft)", value=10000)
p_s = st.sidebar.number_input("Static Reservoir Pressure (Ps), psi", value=3000)
p_wf = st.sidebar.number_input("Flowing BHP (Pwf), psi", value=2867)
p_wh = st.sidebar.number_input("Wellhead Pressure (Pwh), psi", value=100)

st.sidebar.header("📁 Injection Setup")
p_ko_surf = st.sidebar.number_input("Surface Kick-off Pressure (Pko), psi", value=1000)
p_so_surf = st.sidebar.number_input("Surface Operating Pressure (Pso), psi", value=950)

st.sidebar.header("📁 Design Constraints")
gs = st.sidebar.number_input("Kill Fluid Gradient (Gs), psi/ft", value=0.455, format="%.3f")
gpso = st.sidebar.number_input("Gas Operating Gradient, psi/ft", value=0.022, format="%.3f")
min_space = st.sidebar.number_input("Min. Spacing Constraint (ft)", value=300)
min_spread = st.sidebar.number_input("Min. Valve Spread (psi)", value=100)

# --- CALCULATIONS ---

# 1. Graphical Construction Points
wfl_depth = depth_total - (p_wf / gs)
sfl_depth = depth_total - (p_s / gs)
p_so_td = p_so_surf + (gpso * depth_total)

# 2. Key Intersections
d_pob = (p_so_surf - p_wf + gs * depth_total) / (gs - gpso)
p_pob = p_so_surf + (gpso * d_pob)
p_target = p_pob - 100 # Differential logic at DPOI
d_dpoi = depth_total - ((p_wf - p_target) / gs)
g_fa = (p_target - p_wh) / d_dpoi # Lifted gradient slope

# 3. Smart Valve Selection Logic (Iterative with Validation)
final_valves = []
skipped_valves = []
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
        fail_reason = f"Spacing {spacing:.0f}ft < {min_space}ft"
    elif spread < min_spread:
        fail_reason = f"Spread {spread:.0f}psi < {min_spread}psi"

    if fail_reason == "":
        final_valves.append({"Valve": f"Valve {v_idx}", "Depth": round(candidate_d, 0), "Pressure": round(p_tubing_cand, 1), "Status": "✅ Accepted"})
        last_valid_d = candidate_d
    else:
        skipped_valves.append({"Valve": f"Valve {v_idx}", "Reason": fail_reason})
    
    curr_candidate_d = candidate_d
    v_idx += 1

# Add Operating Valve
final_valves.append({"Valve": "Operating Valve", "Depth": round(d_dpoi, 0), "Pressure": round(p_target, 1), "Status": "🎯 Target"})
v_df = pd.DataFrame(final_valves)

# --- UI LAYOUT WITH TABS ---
tab1, tab2, tab3 = st.tabs(["📈 Design Construction", "🤖 Engineer's Assistant", "📚 Gas Lift Academy"])

with tab1:
    fig = go.Figure()
    # Gradient Lines
    fig.add_trace(go.Scatter(x=[0, p_wf], y=[wfl_depth, depth_total], name="Working Fluid Gradient", line=dict(color='#1f77b4', width=3)))
    fig.add_trace(go.Scatter(x=[0, p_s], y=[sfl_depth, depth_total], name="Static Fluid Gradient", line=dict(color='#ff7f0e', dash='dash')))
    fig.add_trace(go.Scatter(x=[p_so_surf, p_so_td], y=[0, depth_total], name="Casing Pressure (Pso)", line=dict(color='#2ca02c', width=3)))
    fig.add_trace(go.Scatter(x=[p_wh, p_target], y=[0, d_dpoi], name="Lifted Flowing Gradient", line=dict(color='#d62728', width=3)))
    
    # Construction Points
    fig.add_trace(go.Scatter(x=[p_pob], y=[d_pob], name="POB (Balance Point)", mode="markers", marker=dict(size=14, color='cyan', line=dict(width=2, color='black'))))
    fig.add_trace(go.Scatter(x=[p_target], y=[d_dpoi], name="DPOI (Injection Point)", mode="markers", marker=dict(size=18, color='yellow', symbol='star', line=dict(width=1, color='red'))))
    
    # Selected Valves (on the red line)
    fig.add_trace(go.Scatter(x=v_df['Pressure'], y=v_df['Depth'], mode='markers+text', name="Selected Valves", text=v_df['Valve'], textposition="middle right", marker=dict(size=10, color='red', symbol='triangle-left')))

    fig.update_layout(yaxis=dict(autorange="reversed"), template="plotly_white", height=700, xaxis_title="Pressure (psig)", yaxis_title="Depth (ft)", legend=dict(yanchor="top", y=0.99, xanchor="left", x=1.02))
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("📋 Final Valve Schedule")
    st.dataframe(v_df[['Valve', 'Depth', 'Status']], hide_index=True, use_container_width=True)
    
    if skipped_valves:
        st.warning("⚠️ Validation Exceptions (Skips)")
        for sv in skipped_valves:
            st.write(f"**{sv['Valve']}** was excluded: *{sv['Reason']}*")
    
    st.divider()
    st.subheader("🤖 Smart Interpretations")
    if d_dpoi > depth_total: st.error("❌ Invalid Design: Injection depth exceeds well depth.")
    elif d_dpoi < 3000: st.warning("⚠️ Warning: Shallow injection point. Efficiency may be low.")
    else: st.success("✅ Success: Deep injection achieved for maximum drawdown.")
    
    st.info(f"**Selection Logic:** Validated using minimum {min_space}ft spacing and {min_spread}psi casing-to-tubing spread.")

with tab3:
    st.header("📖 Gas Lift Academy: Tailored Theory")
    with st.expander("1. Graphical Construction Key"):
        st.write("""
        - **POB (Point of Balance):** The depth where casing and tubing pressures are equal. 
        - **DPOI (Deepest Point of Injection):** The location of the operating valve, set 100 psi (differential) left of the POB.
        """)

    with st.expander("2. Automated Selection Logic"):
        st.write("""
        To ensure mechanical integrity, **GLIS** validates each valve depth candidate:
        - **Valve Spacing:** If valves are closer than 300ft, the system skips the candidate to prevent pressure interference.
        - **Valve Spread:** A minimum differential (100 psi) is required to ensure the valve can actually open/close reliably.
        """)

    with st.expander("3. Analytical Derivations"):
        st.latex(r"DV_{n+1} = DV_n + \frac{P_{so} - G_u(DV_n) - P_{surface}}{G_{kill}}")
