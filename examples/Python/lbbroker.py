# -*- encoding: utf-8 -*-
"""
Load-balancing broker

Clients and workers are shown here in-process.

Author: Brandon Carpenter (hashstat) <brandon(dot)carpenter(at)pnnl(dot)gov>
"""

from __future__ import print_function

import multiprocessing

import zmq


NBR_CLIENTS = 10
NBR_WORKERS = 3


def client_task(ident):
    """Basic request-reply client using REQ socket."""
    socket = zmq.Context().socket(zmq.REQ)

    # 需要和ROUTER交互，因此需要有自己的id
    socket.identity = u"Client-{}".format(ident).encode("ascii")
    socket.connect("ipc://frontend.ipc")

    # Send request, get reply
    # (id, b"", b"HELLO") --> ROUTER
    socket.send(b"HELLO")

    #
    reply = socket.recv()

    print("{}: {}".format(socket.identity.decode("ascii"), reply.decode("ascii")))


def worker_task(ident):
    """Worker task, using a REQ socket to do load-balancing."""
    socket = zmq.Context().socket(zmq.REQ)
    socket.identity = u"Worker-{}".format(ident).encode("ascii")
    socket.connect("ipc://backend.ipc")

    # Tell broker we're ready for work
    # 告诉broker我们的状态OK
    socket.send(b"READY")

    while True:
        #
        address, empty, request = socket.recv_multipart()
        print("{}: {}".format(socket.identity.decode("ascii"), request.decode("ascii")))

        # (client, b"", request) 这个传递给REQ, 让它来选择路由)
        socket.send_multipart([address, b"", b"OK"])

def start(task, *args):
    process = multiprocessing.Process(target=task, args=args)
    process.daemon = True
    process.start()


def main():
    """Load balancer main loop."""
    # Prepare context and sockets
    context = zmq.Context.instance()

    # 1. 创建frongend/backend
    frontend = context.socket(zmq.ROUTER)
    frontend.bind("ipc://frontend.ipc")
    backend = context.socket(zmq.ROUTER)
    backend.bind("ipc://backend.ipc")

    # 2. Start background tasks
    # 分别启动一定数量的client_task和work_task
    for i in range(NBR_CLIENTS):
        start(client_task, i)
    for i in range(NBR_WORKERS):
        start(worker_task, i)

    # 注意: 路由的功能
    #      给定一个ROUTER, 我和它连接时，需要有一个id, 通信的协议为 (id, empty, .....)
    # Initialize main loop state
    count = NBR_CLIENTS
    workers = []
    poller = zmq.Poller()
    # Only poll for requests from backend until workers are available
    poller.register(backend, zmq.POLLIN)

    while True:
        sockets = dict(poller.poll())

        if backend in sockets:
            # Handle worker activity on the backend
            # ROUTER读取的数据
            # (id, empty, client)
            request = backend.recv_multipart()
            worker, empty, client = request[:3]

            # worker空闲了，可以继续接受来自frontend的请求了
            if not workers:
                # Poll for clients now that a worker is available
                poller.register(frontend, zmq.POLLIN)
            workers.append(worker)

            # worker的信息有两种，启动时的信息
            #                   返回给客户端的信息
            #
            if client != b"READY" and len(request) > 3:
                # If client reply, send rest back to frontend
                # 返回给前端的信息
                empty, reply = request[3:]
                frontend.send_multipart([client, b"", reply])
                count -= 1
                if not count:
                    break

        if frontend in sockets:
            # Get next client request, route to last-used worker
            client, empty, request = frontend.recv_multipart()

            # 前端收到消息，然后通过ROUTER将它交给某个后端
            # [worker, empty, .....]实现到后端服务的路由
            # (client, b"", request) 给后端服务器看到的数据, 或者只有request可以看到
            worker = workers.pop(0)
            backend.send_multipart([worker, b"", client, b"", request])
            if not workers:
                # Don't poll clients if no workers are available
                poller.unregister(frontend)

    # Clean up
    backend.close()
    frontend.close()
    context.term()


if __name__ == "__main__":
    main()
