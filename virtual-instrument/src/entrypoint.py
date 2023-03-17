# -*- coding: utf-8 -*-
import socket

from virtual_instrument.virtual_instrument import MantarrayMcSimulator

if __name__ == "__main__":
    HOST = ""
    PORT = 56575

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

        s.bind((HOST, PORT))
        s.listen(1)
        print("WAITING")  # allow-print
        conn, addr = s.accept()
        print(f"CONNECTION MADE: {addr}")  # allow-print
        with conn:
            conn.setblocking(False)
            simulator = MantarrayMcSimulator(conn)
            simulator.run()
