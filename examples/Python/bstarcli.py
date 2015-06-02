# -*- coding: utf-8 -*-
from time import sleep
import zmq


REQUEST_TIMEOUT = 1000  # msecs
SETTLE_DELAY = 2000  # before failing over


def main():
    server = ['tcp://localhost:5001', 'tcp://localhost:5002']
    server_nbr = 0

    ctx = zmq.Context()
    client = ctx.socket(zmq.REQ)
    client.connect(server[server_nbr])


    poller = zmq.Poller()
    poller.register(client, zmq.POLLIN)

    sequence = 0
    while True:
        client.send_string("%s" % sequence)

        expect_reply = True
        while expect_reply:
            socks = dict(poller.poll(REQUEST_TIMEOUT))
            if socks.get(client) == zmq.POLLIN:
                reply = client.recv_string()

                # 获取到反馈
                if int(reply) == sequence:
                    print("I: server replied OK (%s)" % reply)
                    expect_reply = False # 结束请求
                    sequence += 1
                    sleep(1)
                else:
                    print("E: malformed reply from server: %s" % reply)
            else:
                print("W: no response from server, failing over")
                sleep(SETTLE_DELAY / 1000)
                poller.unregister(client)
                client.close()

                # 长时间没有数据返回，则认为服务器挂了?
                # 如何处理Fail Over呢?
                server_nbr = (server_nbr + 1) % 2
                print("I: connecting to server at %s.." % server[server_nbr])
                client = ctx.socket(zmq.REQ)
                poller.register(client, zmq.POLLIN)
                # reconnect and resend request
                client.connect(server[server_nbr])
                client.send_string("%s" % sequence)

if __name__ == '__main__':
    main()
