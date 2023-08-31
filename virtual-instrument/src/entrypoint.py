# -*- coding: utf-8 -*-
import socket

from virtual_instrument.virtual_instrument import MantarrayMcSimulator

if __name__ == "__main__":
    HOST = ""
    PORT = 56575  # TODO figure out what to do if port is already in use

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(1)
        s.setblocking(False)
        print("WAITING")  # allow-print

        simulator = MantarrayMcSimulator(s)
        simulator.run()
