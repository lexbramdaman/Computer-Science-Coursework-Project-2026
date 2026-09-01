import serial
import csv
import streamlit as st 
import pandas as pd
import time
import altair as alt        

if "ser" not in st.session_state:
    st.session_state.ser = serial.Serial("COM22", 115200, timeout=1)
    time.sleep(2)

@st.dialog("Value(s) TOO HIGH!", width="small", dismissible=True, icon=None, on_dismiss="ignore")
def high_risk_warning():
    st.error("One or more of your values are too high. This may cause an environmental hazard. Please evacuate the area immediately!", icon = "💀")
    
    
def print_to_csv():
    ser = st.session_state.ser
    filename = "results.csv"
    ser.reset_input_buffer()    
    line = ser.readline().decode("utf-8", errors="ignore").strip()
    if not line:
        return
    parts = line.split(",")

    if len(parts) != 3:
        st.write("Skipped incomplete line:", line)
        return
        
    Temperature = float(parts[0])
    Light = float(parts[1])
    Motion = float(parts[2])

    st.write("My temperature is", Temperature, "My light is", Light, "My motion is", Motion)
    if Temperature >= 30 or Light >= 30 or Motion >=1800:
        high_risk_warning()
    elif Temperature >= 20 or Light >= 20 or Motion >=1600:
        st.warning("Value(s) getting high... Possible environmental hazard.")
    else:
        st.success("Value(s) are normal.")
        
    with open(filename, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([Temperature, Light, Motion])
    
def get_data() -> pd.DataFrame:
    data = pd.read_csv("results.csv")
    wfrisks = []
    wfrisklabels = []
    lsrisks = []
    lsrisklabels = []
    for index, row in data.iterrows():
        r = wildfire_risk(row["Temperature"], row["Light"], row["Motion"])
        wfrisks.append(r)                
        wfrisklabels.append(riskLabel(r))
        r2 = landslide_risk(row["Motion"])
        lsrisks.append(r2)
        lsrisklabels.append(riskLabel(r2))        
        
    data["Wildfire Risk Percentage (out of 100)"] = wfrisks
    data["Risk of Wildfire"] = wfrisklabels
    data["Landslide Risk Percentage (out of 100)"] = lsrisks
    data["Risk of Landslide"] = lsrisklabels
    
    return data

def riskLabel(risk):
    if risk > 70:
        return "High Risk"
    elif risk >= 40:
        return "Medium Risk"
    elif risk >= 10:
        return "Low Risk"
    else:
        return "No Risk"
    
def draw_graph(data):
    tab1, tab2 = st.tabs(["Chart", "Dataframe"])
    
    with tab1:  
        min_max ={
            "Temperature": (20, 35, 60),
            "Light": (33, 66, 100),
            "Motion": (1000, 1600, 2800),
            "Wildfire Risk Percentage (out of 100)": (40, 70, 100),
            "Landslide Risk Percentage (out of 100)": (40, 70, 100)
        }
        
        for col in min_max:
            st.subheader(col)
            min, medium, max = min_max[col]
            chartdata = data.reset_index()

            safe_zone = alt.Chart(pd.DataFrame({
                "y1":[0],
                "y2":[min]
            })).mark_rect(color="green").encode(
                y='y1:Q',
                y2='y2:Q'
            )

            warn_zone = alt.Chart(pd.DataFrame({
                "y1":[min],
                "y2":[medium]
            })).mark_rect(color="orange").encode(
                y='y1:Q',
                y2='y2:Q'
            )

            danger_zone = alt.Chart(pd.DataFrame({
                "y1":[medium],
                "y2":[max]
            })).mark_rect(color="red").encode(
                y='y1:Q',
                y2='y2:Q'
            )

            line = alt.Chart(chartdata).mark_line(color="blue", strokeWidth = 5).encode(
                x=alt.X("index", title=("Time (seconds)"), axis = alt.Axis(grid=True, zindex = 1)),
                y=alt.Y(col, title = (col), axis = alt.Axis(grid=True, zindex = 1))
            )

            chart = (safe_zone + warn_zone + danger_zone + line).properties(height=500)
            st.altair_chart(chart, use_container_width=True)
            
            
    with tab2:
        st.dataframe(data, height = 250, width = "stretch")
        
def wildfire_risk(Temperature, Light, Motion):
    risk = 0
    
    if Temperature > 30:
        risk += 50
    elif Temperature >= 25:
        risk += 40
    elif Temperature > 20:
        risk += 30  
    if Light > 20:
        risk += 50
    elif Light >= 15:
        risk += 40  
    elif Light >= 13:
        risk += 30
    if Motion > 2000:
        risk += 30
    elif Motion >= 1500:
        risk += 20
    elif Motion >= 1250:
        risk += 10
    return min(risk, 100)

def landslide_risk(Motion):
    risk2 = 0
    
    if Motion > 2000:
        risk2 += 100
    elif Motion >= 1500:
        risk2 += 50
    elif Motion >= 1250:
        risk2 += 10
    return min(risk2, 100)
  
def main():
    mode = st.radio("Select mode:", ["Live Data", "What-if simulations"])
    filename = "results.csv"
    if "running" not in st.session_state:
        st.session_state.running = False
    if "initialised" not in st.session_state:
        st.session_state.initialised = False
    
    if st.button("Start / Stop"):
        st.session_state.running = not st.session_state.running
        
    if st.session_state.running and not st.session_state.initialised:
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Temperature", "Light", "Motion"])
        st.session_state.initialised = True

    if mode == "Live Data":    
        if st.session_state.running:
            st.write("Running...")
            print_to_csv()
            time.sleep(1)
            st.rerun()
    
        else:
            st.write("Stopped")
            if st.session_state.initialised:
                data=get_data()
                draw_graph(data)
    
    elif mode == "What-if simulations":
        st.subheader("Adjust environmental conditions..")
        simulatedTemperature = st.slider("Temperature (°C)", 0, 50, 25)
        simulatedLight = st.slider("Light (Lumens)", 0, 30, 15)
        simulatedMotion = st.slider("Motion (milli g's)", 900, 3000, 1200)
        wildfire = wildfire_risk(simulatedTemperature, simulatedLight, simulatedMotion)
        landslide = landslide_risk(simulatedMotion)
        
        st.subheader("Simulation Results")
        st.write("Wildfire Risk", wildfire, "% -", riskLabel(wildfire))
        st.write("Landslide Risk", landslide, "% -", riskLabel(landslide))
        
if __name__=="__main__":
    main()