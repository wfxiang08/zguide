# -*- encoding: utf-8 -*-
import zmq
import sys
import threading
import time
from random import randint, random

__author__ = "Felipe Cruz <felipecruz@loogica.net>"
__license__ = "MIT/X11"

def tprint(msg):
    """like print, but won't get newlines confused with multiple threads"""
    sys.stdout.write(msg + '\n')
    sys.stdout.flush()

#  ROUTER(bind) <--> DEALER(bind)
#  1. client DEALER 直接连接到 ROUTER
#  2. server DEALER 直接连接到 DEALER
#
# 实在不明白, DEALER是什么东西?
#


class ClientTask(threading.Thread):
    """ClientTask"""
    def __init__(self, id):
        self.id = id
        threading.Thread.__init__ (self)

    def run(self):
        context = zmq.Context()
        socket = context.socket(zmq.DEALER)
        identity = u'client-%d' % self.id
        socket.identity = identity.encode('ascii')

        socket.connect('tcp://localhost:5570')
        print('Client %s started' % (identity))
        poll = zmq.Poller()
        poll.register(socket, zmq.POLLIN)
        reqs = 0
        while True:
            reqs = reqs + 1
            print('Req #%d sent..' % (reqs))
            socket.send_string(u'request #%d' % (reqs))
            for i in range(5):
                sockets = dict(poll.poll(1000))
                if socket in sockets:
                    # 最终的socket是看不到identity等东西的
                    msg = socket.recv()
                    tprint('Client %s received: %s' % (identity, msg))

        socket.close()
        context.term()

class ServerTask(threading.Thread):
    """ServerTask"""
    def __init__(self):
        threading.Thread.__init__ (self)

    def run(self):
        context = zmq.Context()

        # 负责异步接受信息
        frontend = context.socket(zmq.ROUTER)
        frontend.bind('tcp://*:5570')

        # 负责异步处理信息
        backend = context.socket(zmq.DEALER)
        backend.bind('inproc://backend')

        workers = []
        for i in range(5):
            worker = ServerWorker(context)
            worker.start()
            workers.append(worker)

        poll = zmq.Poller()
        poll.register(frontend, zmq.POLLIN)
        poll.register(backend,  zmq.POLLIN)

        # --> frontend <----> backend <---> frontend <---> client
        #     ROUTER <--> DEALER <---> zmq.DEALER(连接到DEALER)
        while True:
            sockets = dict(poll.poll())
            if frontend in sockets:
                # Router需要身份信息
                ident, msg = frontend.recv_multipart()
                tprint('Server received %s id %s' % (msg, ident))

                # backend将这些信息交给谁呢?
                backend.send_multipart([ident, msg])

            if backend in sockets:
                ident, msg = backend.recv_multipart()
                tprint('Sending to frontend %s id %s' % (msg, ident))
                frontend.send_multipart([ident, msg])

        frontend.close()
        backend.close()
        context.term()

class ServerWorker(threading.Thread):
    """ServerWorker"""
    def __init__(self, context):
        threading.Thread.__init__ (self)
        self.context = context

    def run(self):
        # 接受信息，准备replies
        worker = self.context.socket(zmq.DEALER)
        worker.connect('inproc://backend')
        tprint('Worker started')

        while True:
            # 每个消息都会有一个id, msg
            ident, msg = worker.recv_multipart()
            tprint('----> Worker received %s from %s' % (msg, ident))

            replies = 3
            for i in range(replies):
                time.sleep(1. / (randint(1,10)))
                worker.send_multipart([ident, "MSG: %s, Index: %s" % (msg, i)])

        worker.close()


def main():
    """main function"""
    server = ServerTask()
    server.start()
    for i in range(3):
        client = ClientTask(i)
        client.start()

    server.join()


if __name__ == "__main__":
    main()
