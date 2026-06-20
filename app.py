import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="GLIS: Gas Lift Intelligent System", layout="wide", page_icon="🚀")

# --- APP TITLE ---
st.title("🚀 GLIS: Gas Lift Intelligent System")
st.markdown("##### Gas Lift Design & Diagnostic Suite | Option B Specialist")
st.divider()

# --- SIDEBAR INPUTS ---
st.sidebar.header("📁 Field Data Input")
depth_total = st.sidebar.number_input("Total well depth (ft)", value=10000)
p_s = st.sidebar.number_input("Static Reservoir Pressure (Ps), psi", value=3000)
p_wf = st.sidebar.number_input("Flowing Bottomhole Pressure (Pwf), psi", value=2867)
p_wh = st.sidebar.number_input("Wellhead Pressure (Pwh), psi", value=100)

st.sidebar.header("📁 Injection Setup")
p_ko_surf = st.sidebar.number_input("Surface Kick-off Pressure (Pko), psi", value=1000)
p_so_surf = st.sidebar.number_input("Surface Operating Pressure (Pso), psi", value=950)

st.sidebar.header("📁 Gradients & Constraints")
gs = st.sidebar.number_input("Kill Fluid Gradient (Gs), psi/ft", value=0.455, format="%.3f")
gpso = st.sidebar.number_input("Gas Operating Gradient, psi/ft", value=0.022, format="%.3f")
min_space = st.sidebar.number_input("Min. Spacing Constraint (ft)", value=300)
min_spread = st.sidebar.number_input("Min. Valve Spread (psi)", value=100)

# --- CALCULATIONS ---
wfl_depth = depth_total - (p_wf / gs)
sfl_depth = depth_total - (p_s / gs)
p_so_td = p_so_surf + (gpso * depth_total)

# Point of Balance (POB)
d_pob = (p_so_surf - p_wf + gs * depth_total) / (gs - gpso)
p_pob = p_so_surf + (gpso * d_pob)

# DPOI (100psi offset)
p_target = p_pob - 100
d_dpoi = depth_total - ((p_wf - p_target) / gs)
g_fa = (p_target - p_wh) / d_dpoi # Red line gradient

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
    
    fig.update_layout(yaxis=dict(autorange="reversed"), template="plotly_white", height=700, xaxis_title="Pressure (psig)", yaxis_title="Depth (ft)", legend=dict(yanchor="top", y=0.99, xanchor="left", x=1.02))
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("📋 Design Diagnostics")
    c1, c2, c3 = st.columns(3)
    c1.metric("Target Depth (DPOI)", f"{d_dpoi:.0f} ft")
    c2.metric("Point of Balance", f"{d_pob:.0f} ft")
    c3.metric("Valve Pressure (Pvd)", f"{p_target:.1f} psi")
    
    st.divider()
    st.subheader("🤖 Smart Interpretations")
    # Analysis Logic
    if d_dpoi > depth_total: st.error("❌ Invalid Design: Injection depth exceeds well depth.")
    elif d_dpoi < 3000: st.warning("⚠️ Warning: Shallow injection point. System efficiency may be compromised.")
    else: st.success("✅ Success: Deep injection point achieved, maximizing reservoir drawdown.")
    
    if (p_s - p_wf) < 100: st.warning("📉 Alert: Low drawdown detected. Formation damage or low PI may be present.")
    if p_wh > 200: st.info("ℹ️ Optimization Tip: High wellhead pressure is acting as a restriction. Lowering THP will increase production.")

with tab3:
    st.header("📖 Gas Lift Academy: Tailored Theory")
    st.write("Understand the engineering logic behind the **GLIS** algorithms.")
    
    with st.expander("1. The Principle of Gas Injection"):
        st.write("""
        Artificial lift is required when reservoir pressure ($P_s$) is too low to lift the fluid column to the surface naturally. 
        Gas lift achieves this by injecting high-pressure gas into the tubing to:
        - **Reduce Density:** Lowering the average fluid gradient.
        - **Increase Drawdown:** Decreasing the $P_{wf}$ to allow more fluid to flow from the reservoir.
        """)
        st.info("On the graph: The RED line shows the new, lighter gradient after gas is injected.")

    with st.expander("2. Graphical Construction Key"):
        st.write("""
        Our design uses the industry-standard Graphical Method:
        - **Static Fluid Level (SFL):** The depth where the static fluid column sits when the well is dead.
        - **Working Fluid Level (WFL):** The level to which the fluid rises during production.
        - **Point of Balance (POB):** The depth where the pressure in the casing equals the pressure in the tubing. 
        - **Deepest Point of Injection (DPOI):** Located 100 psi (safety margin) above the POB on the flowing gradient line.
        """)

    with st.expander("3. Nodal Analysis in Gas Lift"):
        st.write("""
        Nodal analysis for Option B focuses on the **Solution Node at the Injection Valve**. 
        The system reaches equilibrium when:
        """)
        st.latex(r"P_{casing} - \Delta P_{valve} = P_{tubing}")
        st.write("Where $\Delta P_{valve}$ is typically assumed to be 100 psi for design purposes.")

    with st.expander("4. Analytical Valve Spacing Formulas"):
        st.write("To reach the DPOI, we must unload the well in stages using 'Unloading Valves'.")
        st.write("**Depth of First Valve ($DV_1$):**")
        st.latex(r"DV_1 = \frac{P_{ko} - 50 - P_{surface}}{G_{kill}}")
        st.write("**Subsequent Valve Spacing ($DV_{n+1}$):**")
        st.latex(r"DV_{n+1} = DV_n + \frac{P_{so} - G_{u}(DV_n) - P_{surface}}{G_{kill}}")
        st.caption("GLIS enforces a minimum 300ft spacing and 100psi spread to ensure mechanical stability.")
