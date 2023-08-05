from time import sleep
import lib_db as ldb
import sqlite3
import output_config
from threading import Thread
import socket
import llm_group

def parent():

    parsed_groups = llm_group.parse_llm()
    groups = []
    for g in parsed_groups:
        groups.append(llm_group.llm_group(g[0], g[1]))

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('192.168.1.1', 25566))
        s.listen(16)
        while True:
            try:
                print("waiting for connection")
                connec, addr = s.accept()
                print("got a connection")

                # get msg from child
                msg = connec.recv(36)
                print("received request")

                for g in groups:
                    l = msg.decode().split(",")
                    if g.contains(l[0]):
                        if(int(l[1]) == 3):
                            print("Child is active with state: ", l[1])
                            g.update_activity(l[0], 1)
                        else:
                            print("Child is not active with state: ", l[1])
                            g.update_activity(l[0], 0)
                        g.calculate_current()
                        if len(g.decreases) == 0:
                            connec.send(bytes(str(g.members[l[0]].next_current), encoding='utf-8'))
                        elif l[0] in g.decreases.keys():
                            connec.send(bytes(str(g.members[l[0]].next_current), encoding='utf-8'))
                        else:
                            connec.send(bytes(str(g.members[l[0]].current_current), encoding='utf-8'))
                        print("Sending " + str(g.members[l[0]].next_current) + " amps to " + l[0])
                        ack = connec.recv(4)
                        if ack.decode() == "ack":
                            g.update_current(l[0])

            except Exception as e:
                print("Had error:", e)


def child():
    conn = sqlite3.connect("/root/data/data.db")

    serial_num = ldb.read_db('system_status', 'serial_num', conn)

    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #activity = str(ldb.read_db("status", "charge_authorized", conn))
            state = str(ldb.read_db("status", "pilot_state", conn))
            c = s.connect_ex(("192.168.1.1", 25566))
            if c == 0:
                print("CHILD: sending " + serial_num + "," + state)
                s.send(bytes(serial_num + "," + state, encoding='utf-8'))
                amps = s.recv(4).decode()
                print("CHILD: received " + amps)

                if(int(amps) >= 0):
                    output_config.update_output_current(int(float(amps)))
                    s.send(bytes("ack", encoding='utf-8'))
                    print("acknowledgement sent")
            else:
                output_config.update_output_current(6)
                print("could not connect to parent")   

            s.close()

        except Exception as e:
            output_config.update_output_current(6)
            print(e)   

        sleep(30)

if __name__ == "__main__":
    conn = sqlite3.connect("/root/data/data.db")
    wifi_mode = ldb.read_db('config', 'network_mode', conn)

    match(wifi_mode):
        case "Direct":
            print("not supported")
        
        case "Gateway":
            print("LLM Brokering started")
            broker = Thread(target=parent)
            broker.start()
            sleep(1)
            this = Thread(target=child)
            this.start()


        case "Client":
            print("LLM Child started")
            this = Thread(target=child)
            this.start()
            