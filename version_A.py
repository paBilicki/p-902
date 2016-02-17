import matplotlib
import sys
matplotlib.use('AGG')
import matplotlib.pyplot as plt
import sqlite3 as lite
import matplotlib.lines as mlines


__author__ = 'Bilicki & Chojnacka'

# S5 PROJET GROUPE 902
# TELECOM Bretagne, Rennes annee scolaire 2014-2015
# Authors: P. BILICKI, O. CHOJNACKA
# email: piotr.bilicki@telecom-bretagne.eu
# email: olga.chojnacka@telecom-bretagne.eu

# TODO: create the input data base containing download tests.
trace_name = 'TraceLog_351869054584951_1417375204591'
conn = None


def get_source(n):
    print 'Get source'
    try:
        db = lite.connect('./inputs/%s.db' % n)
        return db
    except lite.Error, e:
        print 'Error %s:' % e.args[0]
        sys.exit(1)


def get_data(db):
    print 'Get data'
    output = []
    cur = db.cursor()

    # duration = [MIN, MAX] = [START, STOP]
    duration = [cur.execute('SELECT min(timestamp) from  Trace').fetchone()[0],
                cur.execute('SELECT max(timestamp) from  Trace').fetchone()[0]]
    # selectedRows = [timestamp, bytesTransferred] where id = TraceId
    selectedRows = cur.execute(
        "SELECT t.timestamp, c.bytesTransferred FROM Trace t, CellularConnectionData c WHERE t.id = c.TraceId AND c.type = 'IN'").fetchall()
    receivedSignal = cur.execute(
        "SELECT cl.leveldBm FROM Cell cl, CellularConnectionData c, Trace t WHERE cl.id = c.CellId AND t.id = c.TraceId AND c.type = 'IN'").fetchall()
    handovers = cur.execute(
        "SELECT t.timestamp FROM Trace t, CellularConnectionEvent c WHERE c.event = 'CONNECTED' AND c.TraceId == t.id").fetchall()
    pingBegins = cur.execute(
        "SELECT t.timestamp FROM Trace t, CellularConnectionData c WHERE c.type LIKE 'IN-START%' AND t.id = c.TraceId").fetchall()
    pingEnds = cur.execute(
        "SELECT t.timestamp FROM Trace t, CellularConnectionData c WHERE c.type LIKE 'IN-TRANSFERRING%' AND t.id = c.TraceId").fetchall()

    bytesTransferred = []
    for row in selectedRows:
        # row = [val_t, val_b] where val_t = timestamp, val_b = bytesTransferred
        val_t, val_b = row

        # set val_b (bytesTransferred) to 0 when the file is downloaded
        if val_b <= 0:
            output.append([val_t + 1, 0])

        output.append([val_t, val_b])
        bytesTransferred.append(val_b)

    calculated_tputs = calc_tput(bytesTransferred)
    calculated_pings, timeOfPings = calc_ping(pingBegins, pingEnds)
    return output, duration, receivedSignal, handovers, calculated_tputs, calculated_pings, timeOfPings


def calc_tput(bytes_transferred):
    # TODO: add condition to substruct consecutive values only within one download/upload test.
    print 'cal_tput'
    tputs = []

    for i in range(0, len(bytes_transferred)):
        if i != 0 and i % 1 == 0:
            tputs.append(bytes_transferred[i] - bytes_transferred[i - 1000])
        else:
            tputs.append(0)
    return tputs


def calc_ping(pingBegin, pingEnd):
    print'calc_ping'
    pingStart = []
    pingStop = []
    pings = []
    timeOfPings = []
    for i in pingBegin:
        pingStart.append(i[0])
    for i in pingEnd:
        pingStop.append(i[0])
    for i in range(0, len(pingBegin)):
        pings.append(pingStop[i] - pingStart[i])
        timeOfPings.append(pingStart[i])
    return pings, timeOfPings


def plot_bt(n, input_data, input_duration, input_dbm, input_handovers):
    print 'Plot bt'
    x = []
    y = []
    y2 = []

    # bytesTransfered in timestamp function
    for i in input_data:
        x.append(i[0])
        y.append(i[1])

    # values of receivedSignal in dbm
    for i in input_dbm:
        y2.append(i[0])

    ax1 = plt.subplot()
    ax1.plot(x, y, 'b.', markersize=1, label='Transferred Data [Bytes]')
    ax1.set_title(n)
    ax1.set_ylabel('Transferred Data [Bytes]', color='b')
    ax1.set_xlabel('Time (ms)')
    for tl in ax1.get_yticklabels():
        tl.set_color('b')

    ax2 = ax1.twinx()
    ax2.plot(x, y2, 'r--', label='Received Signal [dBm]')
    ax2.set_ylabel('Received Signal [dBm]', color='r')
    for tl in ax2.get_yticklabels():
        tl.set_color('r')

    plt.plot(input_handovers, input_handovers, 'rs', markersize=7)

    ho_marker = mlines.Line2D([], [], color='red', marker='s', markersize=10, label='Handovers')
    plt.legend(handles=[ho_marker])
    plt.xlim(input_duration[0], input_duration[1])
    plt.plot(x, input_dbm)
    plt.tight_layout()

    plt.show()
    plt.savefig('./results/A/bt_' + n + '.png')
    plt.close()


def plot_tput(n, input_data, input_dbm, input_handovers, calc_tput):
    print 'Plot tput'
    x = []
    y = []
    t = []
    for i in input_data:
        x.append(i[0])
        y.append(i[1])

    for j in input_handovers:
        t.append(85)

    ax1 = plt.subplot()
    ax1.plot(x, calc_tput, 'b-', label='Throughput [Bytes]')
    ax1.set_title(n)
    ax1.set_ylabel('Throughput [Bytes]', color='b')
    ax1.set_xlabel('Time (ms)')
    for tl in ax1.get_yticklabels():
        tl.set_color('b')

    ax2 = ax1.twinx()
    ax2.plot(x, input_dbm, 'r--', label='Received Signal [dBm]')
    ax2.set_ylabel('Received Signal [dBm]', color='r')
    for tl in ax2.get_yticklabels():
        tl.set_color('r')

    plt.plot(input_handovers, t, 'rs', markersize=7)
    ho_marker = mlines.Line2D([], [], color='red', marker='s',
                                markersize=10, label='Handovers')

    plt.legend(handles=[ho_marker])
    plt.tight_layout()
    plt.show()
    plt.savefig('./results/A/t_put_' + n + '.png')
    plt.close()


def plot_pings(n, input_data, calc_pings, timeofpings):
    print 'Plot pings'
    x = []
    for i in input_data:
        j = 0
        temp = i[0]
        if temp == timeofpings[j]:
            x.append(temp)
            j += 1
        else:
            x.append(0)

    ax1 = plt.subplot()
    ax1.plot(timeofpings, calc_pings, 'bo', label='Pings [Bytes]')
    ax1.set_title(n)
    ax1.set_ylabel('Pigs [ms]', color='b')
    ax1.set_xlabel('Time of measurement (ms)')
    for tl in ax1.get_yticklabels():
        tl.set_color('b')
    plt.show()
    plt.savefig('./results/A/pings' + n + '.png')
    plt.close()
    return


conn = get_source(trace_name)
if conn != None:
    data_values, data_duration, data_dbm, data_handovers, calculated_tputs, calculated_pings, timeOfPings = get_data(
        conn)
    plot_bt(trace_name, data_values, data_duration, data_dbm, data_handovers)
    plot_pings(trace_name, data_values, calculated_pings, timeOfPings)
    # TODO: after adding condition for calc_tput, uncomment plot_tput.
    plot_tput(trace_name, data_values, data_dbm, data_handovers, calculated_tputs)