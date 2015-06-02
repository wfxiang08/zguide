# -*- encoding: utf-8 -*-
#
#   Demonstrate identities as used by the request-reply pattern.  Run this
#   program by itself.
#
#   Author: Jeremy Avnet (brainsik) <spork(dash)zmq(at)theory(dot)org>
#

import zmq
import zhelpers

context = zmq.Context()

# bin/connect的区别?
sink = context.socket(zmq.ROUTER)
sink.bind("inproc://example")

# #
# # 以DEALER的身份连接ROUTER
# #
# # First allow 0MQ to set the identity
# anonymous = context.socket(zmq.DEALER)
# anonymous.connect("inproc://example")
#
# # 1. 匿名的id, 使用 uuid
# anonymous.send(b"ROUTER uses a generated UUID")
# zhelpers.dump(sink)

# Then set the identity ourselves
identified = context.socket(zmq.DEALER)

# 2. 设置了id
identified.setsockopt(zmq.IDENTITY, b"PEER2")
identified.connect("inproc://example")

# identified.send_multipart([b"", b"ROUTER socket uses REQ's socket identity"])
identified.send(b"ROUTER socket uses REQ's socket identity")
zhelpers.dump(sink)


#
# 以普通的REQ连接
#


identified1 = context.socket(zmq.REQ)

# 2. 设置了id
identified1.setsockopt(zmq.IDENTITY, b"REQ1")
identified1.connect("inproc://example")

identified1.send(b"ROUTER socket uses REQ's socket identity")
zhelpers.dump(sink)