import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="UTM Gas Lift Designer", layout="wide", page_icon="🚀")

st.title("🚀 Option B: Gas Lift Valve Spacing App")
st.markdown("### Based on Chapter 3: Analytical Method (Dr. Abdul Rahim Risal)")

# --- SIDEBAR: INPUT DATA (Default values from Example 4, Slide 29) ---
st.sidebar.header("📂 Well Data")
well_depth = st.sidebar.number_input("Well Depth (ft)", value=5000)
p_wh = st.sidebar.number_input("Wellhead Pressure (Pwh), psi", value=200)
p_ko = st.sidebar.number_input("Kick-off Pressure (Pko), psi", value=900)
p_so = st.sidebar.number_input("Surface Operating Pressure (Pso), psi", value=850)

st.sidebar.header("📂 Gradients")
gs = st.sidebar.number_input("Kill Fluid Gradient (Gs), psi/ft", value=0.50)
gu = st.sidebar.number_input("Design Unloading Gradient (Gu), psi/ft", value=0.125)

st.sidebar.header("📂 Constraints")
d_inj = st.sidebar.number_input("Injection Depth (ft)", value=3921)
min_space = st.sidebar.number_input("Min. Spacing (ft)", value=250)
delta_p = st.sidebar.number_input("Drop per Valve (psi)", value=25)

# --- CALCULATIONS ---
valves = []
# 1. Top Valve (Slide 26)
# Unloaded to pit means Psurface = 0
dv1 = (p_ko - 50 - 0) / gs
valves.append({"Valve": 1, "Depth (ft)": round(dv1, 0)})

# 2. Subsequent Valves (Slide 27)
current_depth = dv1
p_so_val = p_so
v_count = 2

while current_depth < d_inj and v_count < 15:
    p_so_val -= delta_p # Pressure drop for balanced valve
    increment = (p_so_val - (gu * current_depth)) / gs
    
    if increment < min_space: increment = min_space
    
    new_depth = current_depth + increment
    if new_depth > d_inj: break
    
    valves.append({"Valve": v_count, "Depth (ft)": round(new_depth, 0)})
    current_depth = new_depth
    v_count += 1

df_valves = pd.DataFrame(valves)

# --- PLOTTING ---
depth_plot = np.linspace(0, well_depth, 100)
p_casing = p_so + (0.02 * depth_plot) # Casing pressure line
p_tubing = p_wh + (gu * depth_plot)   # Tubing gradient line

fig = go.Figure()
fig.add_trace(go.Scatter(x=p_casing, y=depth_plot, name="Casing Pressure", line=dict(color='green')))
fig.add_trace(go.Scatter(x=p_tubing, y=depth_plot, name="Tubing Pressure", line=dict(color='blue')))
fig.add_trace(go.Scatter(x=[p_wh + (gu*d) for d in df_valves['Depth (ft)']], 
                         y=df_valves['Depth (ft)'], mode='markers+text', 
                         name="Valves", text=[f"V{int(n)}" for n in df_valves['Valve']],
                         marker=dict(size=12, color='red', symbol='triangle-left')))

fig.update_layout(yaxis=dict(autorange="reversed"), template="plotly_white", 
                  title="Gas Lift Pressure-Depth Diagram", xaxis_title="Pressure (psi)", yaxis_title="Depth (ft)")

# --- DISPLAY ---
t1, t2 = st.tabs(["📈 Design Plot", "🧮 Workings"])
with t1:
    col1, col2 = st.columns([3, 1])
    col1.plotly_chart(fig, use_container_width=True)
    col2.success(f"**Total Valves:** {len(df_valves)}")
    col2.dataframe(df_valves, hide_index=True)

with t2:
    st.subheader("Analytical Formulas Used")
    st.write("Calculations follow **Slide 26 & 27** equations:")
    st.latex(r"DV_1 = \frac{P_{ko}-50}{G_s}")
    st.latex(r"DV_{n+1} = DV_n + \frac{P_{so} - G_u(DV_n)}{G_s}")
    st.info("Note: Calculation assumes unloading to pit (P_surface = 0) as per Example 4.")
