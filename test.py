import serial
import csv

ser = serial.Serial("COM22", 115200)
line = ser.readline().decode("utf-8", errors = "ignore").strip()

filename = "alri.csv"

for x in range(10):
    parts = line.split(",")
    
    temp = parts[0]
    light = parts[1]
    motion = parts[2]
    
    print("My temp is", temp, "My light is", light, "My motion is", motion)
    
    with open(filename, "a", newline = "") as f:
        writer = csv.writer(f)
        writer.writerow([temp, light, motion])
        
print("I saved my csv file as", filename)