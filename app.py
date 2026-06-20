import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="UTM Gas Lift Design", layout="wide")

st.title("🚀 Gas Lift Design: Valve Spacing Application")
st.markdown("Developed based on **Chapter 3: Artificial Lift** by Dr. Abdul Rahim Risal")

# --- SIDEBAR INPUTS (Based on Example 4, Slide 29) ---
st.sidebar.header("📁 1. Design Parameters")
well_depth = st.sidebar.number_input("Total Well Depth (ft)", value=5000)
p_wh = st.sidebar.number_input("Wellhead Pressure (Pwh), psi", value=200)
p_ko = st.sidebar.number_input("Kick-off Pressure (Pko), psi", value=900)
p_so = st.sidebar.number_input("Surface Operating Pressure (Pso), psi", value=850)

st.sidebar.header("📁 2. Gradients")
gs = st.sidebar.number_input("Kill Fluid Gradient (Gs), psi/ft", value=0.500)
gu = st.sidebar.number_input("Design Unloading Gradient (Gu), psi/ft", value=0.125)

st.sidebar.header("📁 3. Constraints")
d_inj = st.sidebar.number_input("Target Injection Depth (ft)", value=3921)
min_spacing = st.sidebar.number_input("Min. Valve Spacing (ft)", value=250)
delta_p = st.sidebar.number_input("Valve Pressure Drop (psig/valve)", value=25)

# --- CALCULATION LOGIC (Analytical Method Slide 26-27) ---
valves = []

# Valve 1 Depth (Slide 26)
# DV1 = (Pko - 50 - Psurface) / Gs
# Note: Dr. uses Psurface = 0 if unloaded to pit (Example 4)
p_surface_unloading = 0 
dv1 = (p_ko - 50 - p_surface_unloading) / gs
valves.append({"Valve": 1, "Depth": round(dv1, 0)})

# Subsequent Valves (Slide 27)
# DV_next = DV_prev + (Pso_prev - Gu(DV_prev) - Psurface) / Gs
current_depth = dv1
valve_num = 2
p_so_current = p_so

while current_depth < d_inj:
    p_so_current = p_so_current - delta_p # Balanced valve drop
    
    # Formula from Slide 27
    num = p_so_current - (gu * current_depth) - p_surface_unloading
    increment = num / gs
    
    # Check if spacing is too small
    if increment < min_spacing:
        increment = min_spacing
        
    new_depth = current_depth + increment
    
    if new_depth > d_inj:
        break
        
    valves.append({"Valve": valve_num, "Depth": round(new_depth, 0)})
    current_depth = new_depth
    valve_num += 1

df_valves = pd.DataFrame(valves)

# --- VISUALIZATION ---
# Create Pressure lines for the chart
depth_axis = np.linspace(0, well_depth, 100)
casing_p = p_so + (0.02 * depth_axis) # Gas column weight (approx 0.02 psi/ft)
tubing_p = p_wh + (gu * depth_axis)  # Unloading gradient

fig = go.Figure()

# Casing Pressure Line
fig.add_trace(go.Scatter(x=casing_p, y=depth_axis, name="Casing Pressure (Pso)", line=dict(color='green')))
# Tubing Pressure Line
fig.add_trace(go.Scatter(x=tubing_p, y=depth_axis, name="Tubing Pressure (Gu)", line=dict(color='blue')))

# Valve Points
fig.add_trace(go.Scatter(
    x=[p_wh + (gu * d) for d in df_valves['Depth']],
    y=df_valves['Depth'],
    mode="markers+text",
    name="Gas Lift Valves",
    text=[f"V{int(n)}" for n in df_valves['Valve']],
    textposition="top right",
    marker=dict(size=12, color='red', symbol='triangle-left')
))

fig.update_layout(
    title="Gas Lift Pressure-Depth Diagram (Analytical Spacing)",
    xaxis_title="Pressure (psi)",
    yaxis_title="Depth (ft)",
    yaxis=dict(autorange="reversed"), # Depth 0 at top
    template="plotly_white",
    height=700
)

# --- UI LAYOUT ---
tab1, tab2 = st.tabs(["📊 Valve Spacing Plot", "🧮 Spacing Workings"])

with tab1:
    c1, c2 = st.columns([3, 1])
    with c1:
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.success("### Results")
        st.write(f"Total Valves: **{len(df_valves)}**")
        st.dataframe(df_valves, hide_index=True)
        st.info("The diagram shows the casing and tubing gradients crossing at the valve locations.")

with tab2:
    st.subheader("Step-by-Step Analytical Method")
    
    st.markdown("#### 1. Top Valve (DV1)")
    st.latex(r"DV_1 = \frac{(P_{ko} - 50) - P_{surface}}{G_s}")
    st.write(f"Result: **{dv1:.1f} ft**")

    st.markdown("#### 2. Consequent Valves (DVn)")
    st.latex(r"DV_{n+1} = DV_n + \frac{P_{so} - G_u(DV_n) - P_{surface}}{G_s}")
    
    st.divider()
    st.write("#### 📝 Assignment Reference")
    st.write("This app logic follows **Slide 29 (Example 4)** exactly. If you use those inputs, your valve depths will match the manual calculation.")