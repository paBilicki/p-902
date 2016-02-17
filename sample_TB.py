#!/usr/bin/python

import sqlite3

import matplotlib
matplotlib.use('AGG')
import matplotlib.pyplot as plt


# Global Vars
OUT_NAME = "output.png"


#Connect to the sqlite database
conn = sqlite3.connect('./inputs/TraceLog_359290050338171_1414508488061.db')
# conn =sqlite3.connect(sys.argv[1])
c = conn.cursor()

#Get the first time limits of the mesure
startTime = c.execute('SELECT min(timestamp) from  Trace').fetchone()[0]
stopTime = c.execute('SELECT max(timestamp) from  Trace').fetchone()[0]


#Extract the connection data fot the CellConnectionData table and the timestamp from the Trace table
DataRows = c.execute(
    'SELECT timestamp, bytesTransferred from CellularConnectionData, Trace where Trace.id = CellularConnectionData.TraceId').fetchall()
DataPoints = []

print DataRows

LastBytes = [0, 0]  #Put back graphing to zero after a download stopped progressing...

#Store the data in a [Timestamp, ByteTransferred] list
for row in DataRows:
    Timestamp, Bytes = row

    #Reset to 0 if stopped downloading
    if Bytes <= LastBytes[1]:
        DataPoints.append([LastBytes[0] + 1, 0])

    LastBytes = [Timestamp, Bytes]
    DataPoints.append(LastBytes)


#Create a matplotlib plot
fig = plt.figure()

titleStr = "Transfered Data Timeline"
xLabel = "Time"
yLabel = "Transferred Data (Bytes)"

#Set Axes
plt.title(titleStr)
plt.ylabel(yLabel)
plt.xlabel(xLabel)

#Strat the x axis at the minimal data value
plt.xlim([startTime, stopTime])
# print DataPoints
#Plot the data
plt.plot(*zip(*DataPoints))
plt.show()
#export to png
plt.savefig('./results/sample_TB/' + OUT_NAME + '.png')
plt.close()
