import sys
import sqlite3 as lite

import matplotlib


matplotlib.use('AGG')
import matplotlib.pyplot as plt

__author__ = 'Bilicki & Chojnacka'
# S5 PROJET GROUPE 902
# TELECOM Bretagne, Rennes annee scolaire 2014-2015
# Authors: P. BILICKI, O. CHOJNACKA
# email: piotr.bilicki@telecom-bretagne.eu
# email: olga.chojnacka@telecom-bretagne.eu

# TODO: create the input data base containing download tests.
# traceName = '20 January 19h36'
# traceName = '20 January 19h39'
traceName = '20 January 20h47'
conn = None


def get_source(traceName):
    print 'Get source'
    try:
        db = lite.connect('./inputs/%s.db' % traceName)
        return db
    except lite.Error, e:
        print 'Error %s:' % e.args[0]
        sys.exit(1)


def download(db):
    print 'Download'
    cur = db.cursor()
    # selectedRows = [timestamp, bytesTransferred] where id = TraceId
    selectedRows = cur.execute(
        "SELECT t.timestamp, c.bytesTransferred FROM Trace t, CellularConnectionData c WHERE t.id = c.TraceId AND c.type = 'IN'").fetchall()

    # receivedSignal = [leveldBm,] where id = TraceId
    receivedSignal = cur.execute(
        "SELECT cl.leveldBm FROM Cell cl, CellularConnectionData c, Trace t WHERE cl.id = c.CellId AND t.id = c.TraceId AND c.type = 'IN'").fetchall()

    # handovers = [timestamp,] where event = connected
    handovers = cur.execute(
        "SELECT t.timestamp FROM Trace t, CellularConnectionEvent c WHERE c.event = 'CONNECTED' AND c.TraceId == t.id").fetchall()

    bytesDownloaded = []
    downloadTimestamps = []
    for row in selectedRows:
        # row = [val_t, val_b] where val_t = timestamp, val_b = bytesTransferred
        val_ts, val_bt = row

        # set val_b (bytesTransferred) to 0 when the file is downloaded
        if val_bt <= 0:
            downloadTimestamps.append(val_bt)

        downloadTimestamps.append(val_ts)
        bytesDownloaded.append(val_bt)

    signaldBm = []
    for row in receivedSignal:
        signaldBm.append(row[0])

    timeOfHandovers = []
    for row in handovers:
        timeOfHandovers.append(row[0])

    return downloadTimestamps, bytesDownloaded, signaldBm, timeOfHandovers


def upload(db):
    print 'Upload'
    cur = db.cursor()
    # selectedRows = [timestamp, bytesTransferred] where id = TraceId
    selectedRows = cur.execute(
        "SELECT t.timestamp, c.bytesTransferred FROM Trace t, CellularConnectionData c WHERE t.id = c.TraceId AND c.type = 'OUT'").fetchall()

    # receivedSignal = [leveldBm,] where id = TraceId
    receivedSignal = cur.execute(
        "SELECT cl.leveldBm FROM Cell cl, CellularConnectionData c, Trace t WHERE cl.id = c.CellId AND t.id = c.TraceId AND c.type = 'OUT'").fetchall()

    # handovers = [timestamp,] where event = connected
    handovers = cur.execute(
        "SELECT t.timestamp FROM Trace t, CellularConnectionEvent c WHERE c.event = 'CONNECTED' AND c.TraceId == t.id").fetchall()

    bytesUploaded = []
    uploadTimestamps = []
    for row in selectedRows:
        # row = [val_t, val_b] where val_t = timestamp, val_b = bytesTransferred
        val_ts, val_bt = row

        # set val_b (bytesTransferred) to 0 when the file is downloaded
        if val_bt <= 0:
            uploadTimestamps.append(val_bt)

        uploadTimestamps.append(val_ts)
        bytesUploaded.append(val_bt)

    signaldBm = []
    for row in receivedSignal:
        signaldBm.append(row[0])

    timeOfHandovers = []
    for row in handovers:
        timeOfHandovers.append(row[0])

    return uploadTimestamps, bytesUploaded, signaldBm, timeOfHandovers


def calculating_pings(db, du):
    print'Calculating_pings'
    cur = db.cursor()

    # pingBegins = [timestamp,] where type = in-start*
    # pingBegins = [timestamp,] where type = in-transferring*
    if du == 0:
        pingBegins = cur.execute(
            "SELECT t.timestamp FROM Trace t, CellularConnectionData c WHERE c.type LIKE 'IN-START%' AND t.id = c.TraceId").fetchall()
        pingEnds = cur.execute(
            "SELECT t.timestamp FROM Trace t, CellularConnectionData c WHERE c.type LIKE 'IN-TRANSFERRING%' AND t.id = c.TraceId").fetchall()
    else:
        pingBegins = cur.execute(
            "SELECT t.timestamp FROM Trace t, CellularConnectionData c WHERE c.type LIKE 'OUT-START%' AND t.id = c.TraceId").fetchall()
        pingEnds = cur.execute(
            "SELECT t.timestamp FROM Trace t, CellularConnectionData c WHERE c.type == 'OUT' AND t.id = c.TraceId AND c.bytesTransferred == '13880'").fetchall()
        receivedSignalPing = cur.execute(
            "SELECT cl.leveldBm FROM Trace t, CellularConnectionData c, Cell cl WHERE c.type LIKE 'OUT-START%' AND t.id = c.TraceId AND cl.id = c.CellId").fetchall()
    pingBegin = []
    for row in pingBegins:
        pingBegin.append(row[0])

    pingEnd = []
    for row in pingEnds:
        pingEnd.append(row[0])

    calculatedPings = []
    timeOfPings = []
    for row in range(0, len(pingBegin)):
        calculatedPings.append(pingEnd[row] - pingBegin[row])
        timeOfPings.append(pingBegin[row])

    receivedSignalPings = []
    for row in receivedSignalPing:
        receivedSignalPings.append(row[0])
    return calculatedPings, timeOfPings, receivedSignalPings


def plot_transfer(traceName, timestamps, bytesTransferred, signaldBm, timeOfHandovers):
    print 'Plot Transfer'

    ax1 = plt.subplot()
    ax1.plot(timestamps, bytesTransferred, 'b.', markersize=1)
    ax1.set_title(traceName)
    ax1.set_ylabel('Transferred Data [Bytes]', color='b')
    ax1.set_xlabel('Time (ms)')
    for tl in ax1.get_yticklabels():
        tl.set_color('b')

    ax2 = ax1.twinx()
    ax2.plot(timestamps, signaldBm, 'g-', label='Signal [dBm]')
    ax2.set_ylabel('Signal [dBm]', color='g')
    for tl in ax2.get_yticklabels():
        tl.set_color('g')

    # drawing red -. lines when a handover took place
    for ho in timeOfHandovers:
        plt.axvline(x=ho, linewidth=2, color='r', ls='-.')

    plt.show()
    plt.savefig('./results/B/bt_' + traceName + '.png')
    plt.close()


def plot_pings(traceName, calculatedPings, timeOfPings, receivedSignalPings):
    print 'Plot Pings'
    ax1 = plt.subplot()
    ax1.set_title(traceName)
    ax1.plot(timeOfPings, calculatedPings, 'bo')
    ax1.set_ylabel('Pings [ms]', color='b')
    ax1.set_xlabel('Time of measurement (ms)')
    for tl in ax1.get_yticklabels():
        tl.set_color('b')

    ax2 = ax1.twinx()
    ax2.plot(timeOfPings, receivedSignalPings, 'g-', label='Signal [dBm]')
    ax2.set_ylabel('Signal [dBm]', color='g')
    for tl in ax2.get_yticklabels():
        tl.set_color('g')

    plt.show()
    plt.savefig('./results/B/pings_' + traceName + '.png')
    plt.close()


conn = get_source(traceName)
if conn != None:
    # TODO: Having data base containing download tests, verify the download() and the plot_transfer(download parameters)
    # du - to distinguish plots of download/upload, 0 for download, 1 for upload
    du = 1
    downloadTimestamps, bytesDownloaded, signaldBm, timeOfHandovers = download(conn)
    uploadTimestamps, bytesUploaded, signaldBmU, timeOfHandoversU = upload(conn)
    calculatedPings, timeOfPings, receivedSignalPings = calculating_pings(conn, du)

    # plot_transfer(traceName, downloadTimestamps, bytesDownloaded, signaldBm, timeOfHandovers)
    plot_transfer(traceName, uploadTimestamps, bytesUploaded, signaldBmU, timeOfHandoversU)
    plot_pings(traceName, calculatedPings, timeOfPings, receivedSignalPings)