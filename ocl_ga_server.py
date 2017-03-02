#!/usr/bin/python3
import sys
import time
import utils
import socket
import select
import threading
import traceback
from server_client import Server, OP_MSG_BEGIN, OP_MSG_END

class OpenCLGAServer():
    def __init__(self, options, port=12345):
        self.__paused = False
        self.__forceStop = False
        self.__options = options
        self.__callbacks = {
            "connected": [], # for notifying users that a client is connected
            "disconnected": [], # for notifying users that a client is disconnected
            "message": [] # for notifying users that a message is received from client
        }
        self.server = None
        self.__listen_at(port)

    def __listen_at(self, port):
        '''
        we should create a server socket and bind at all IP address with specified port.
        all commands are passed to client and wait for client's feedback.
        '''
        try:
            self.server = Server(ip = "0.0.0.0", port = port)
            self.server.setup_callbacks_info({ 0 : { "pre" : OP_MSG_BEGIN,
                                                     "post": OP_MSG_END,
                                                     "callback"  : self.__process_data}})
            self.server.run_server()
        except:
            traceback.print_exc()
            self.server = None
        pass

    def __send(self, command, data):
        '''
        Send method should send a dict with type property for command type and data property for
        command data. The whole payload should be translated into pickle structure.
        '''
        pass

    def __process_data(self, data):
        '''
        Once we receive a payload dict which has a type property for command type and data property
        for command data.
        '''
        try:
            # Conver bytearray "data" to string-like object
            msg = str(data, 'ASCII')
            dict_msg = eval(msg)
            result_type = dict_msg["type"]
            print("[Server] __process_data from client, type = %s "%(result_type))

            if dict_msg["type"] == "statistics":
                st = dict_msg["result"]
                self.__notify("message", {"statistics" : st})
            elif dict_msg["type"] == "best":
                best_chromosome = eval(dict_msg["result"])
                self.__notify("message", {"best" : best_chromosome})
            elif dict_msg["type"] == "save":
                saved_filename = dict_msg["result"]

        except:
            traceback.print_exc()

    def __notify(self, name, data):
        if name not in self.__callbacks:
            return

        for func in self.__callbacks[name]:
            try:
                func(data)
            except Exception as e:
                print("exception while execution %s callback"%(name))
                print(traceback.format_exc())

    # public APIs
    @property
    def paused(self):
        return self.__paused

    @property
    def elapsed_time(self):
        return self.__elapsed_time

    def on(self, name, func):
        if name in self.__callbacks:
            self.__callbacks[name].append(func)

    def off(self, name, func):
        if (name in self.__callbacks):
            self.__callbacks[name].remove(func)

    def prepare(self, info):
        data = {"command" : "prepare", "data" : info}
        self.server.send(repr(data))
        pass

    def run(self, prob_mutate, prob_crossover):
        assert self.server != None
        data = {"command" : "run", "data" : None}
        self.server.send(repr(data))
        pass

    def stop(self):
        assert self.server != None
        self.__forceStop = True
        data = {"command" : "stop", "data" : None}
        self.server.send(repr(data))

    def pause(self):
        assert self.server != None
        self.__paused = True
        data = {"command" : "pause", "data" : None}
        self.server.send(repr(data))

    def save(self, filename = None):
        assert self.server != None
        data = {"command" : "save", "data" : filename}
        self.server.send(repr(data))

    def restore(self, filename = None):
        assert self.server != None
        data = {"command" : "restore", "data" : filename}
        self.server.send(repr(data))

    def get_statistics(self):
        assert self.server != None
        data = {"command" : "statistics", "data" : None}
        self.server.send(repr(data))
        pass

    def get_the_best(self):
        assert self.server != None
        data = {"command" : "best", "data" : None}
        self.server.send(repr(data))
        pass

    def shutdown(self):
        assert self.server != None
        data = {"command" : "exit", "data" : None}
        self.server.send(repr(data))
        while self.server.get_connected_lists() != []:
            time.sleep(0.2)
        self.server.shutdown()
        self.server = None

def start_ocl_ga_server(info_getter, callbacks = {}):
    lines = ""
    def get_input():
        nonlocal lines
        data = None
        try:
            if sys.platform in ["linux", "darwin"]:
                import select
                time.sleep(0.01)
                if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
                    data = sys.stdin.readline().rstrip()
            elif sys.platform == "win32":
                import msvcrt
                time.sleep(0.01)
                if msvcrt.kbhit():
                    data = msvcrt.getch().decode("utf-8")
                    if data == "\r":
                        # Enter is pressed
                        data = lines
                        lines = ""
                    else:
                        lines += data
                        print(data)
                        data = None
            else:
                pass
        except KeyboardInterrupt:
            data = "exit"
        return data

    try:
        oclGAServer = OpenCLGAServer("")
        for name, callback in list(callbacks.items()):
            oclGAServer.on(name, callback)
        print("Press prepare    + <Enter> to prepare")
        print("Press run        + <Enter> to run");
        print("Press restore    + <Enter> to restore");
        print("Press pause      + <Enter> to pause")
        print("Press save       + <Enter> to save (filename:saved.pickle)")
        print("Press stop       + <Enter> to stop")
        print("Press plot_st    + <Enter> to plot statistics")
        print("Press plot_best  + <Enter> to plot best")
        print("Press ctrl       + c       to exit")

        while True:
            user_input = get_input()
            if "prepare" == user_input:
                info = info_getter()
                oclGAServer.prepare(info)
            elif "pause" == user_input:
                oclGAServer.pause()
            elif "run" == user_input:
                # TODO : deliver cross/mutate probability correctly
                oclGAServer.run(0.1, 0.3)
            elif "stop" == user_input:
                oclGAServer.stop()
            elif "save" == user_input:
                oclGAServer.save()
            elif "plot_st" == user_input:
                oclGAServer.get_statistics()
            elif "plot_best" == user_input:
                oclGAServer.get_the_best()
            elif "restore" == user_input:
                oclGAServer.restore()
            elif "exit" == user_input:
                oclGAServer.shutdown()
                print("[OpenCLGAServer] Bye Bye !!")
                break
    except:
        traceback.print_exc()

if __name__ == "__main__":
    # NOTE : NOT support executing ocl_ga_server.py directly.
    #        Please call start_ocl_ga_server from each example.
    assert False, "NOT support executing ocl_ga_client.py directly. "\
                  "Please call start_ocl_ga_server in each example."
