Ping-Pong: Basic Event Loop
===========================

The simplest event-based example.  Alice sends a sequence of messages to Bob,
who replies to each one.  No state machine — just a simple if/else to choose
the reply.  Found in ``examples/event-based/pingPong/``.

This is purely classical (no quantum operations).  It demonstrates the basic
async event loop pattern before adding state machines and quantum in later examples.

Alice (client)
--------------

Alice sends a list of messages and prints Bob's replies::

    async def run_alice(reader: StreamReader, writer: StreamWriter):
        messages = ["ping", "ping", "hello", "ping"]

        for msg in messages:
            print(f"Alice: sending  '{msg}'")
            writer.write(msg.encode("utf-8"))
            await writer.drain()

            reply_data = await reader.read(255)
            reply = reply_data.decode("utf-8")
            print(f"Alice: received '{reply}'")

Bob (server)
------------

Bob replies "pong" to "ping" and "no way!" to anything else::

    async def run_bob(reader: StreamReader, writer: StreamWriter):
        while True:
            data = await reader.read(255)
            if not data:
                break  # Alice disconnected

            message = data.decode("utf-8")
            if message == "ping":
                reply = "pong"
            else:
                reply = "no way!"

            writer.write(reply.encode("utf-8"))
            await writer.drain()

Key concepts
------------

- **reader/writer**: The async streams for classical TCP communication.
  ``writer.write()`` sends bytes, ``await reader.read(N)`` receives up to N bytes.
- **await writer.drain()**: Ensures the write buffer is flushed to the network.
- **Connection lifecycle**: Bob's loop exits when ``reader.read()`` returns empty
  bytes, meaning Alice has disconnected.

Running
-------

::

    cd examples/event-based/pingPong
    bash run.sh

Expected output::

    Alice: sending  'ping'
    Bob: received 'ping'
    Bob: sending  'pong'
    Alice: received 'pong'
    Alice: sending  'ping'
    ...
    Alice: sending  'hello'
    Bob: received 'hello'
    Bob: sending  'no way!'
    Alice: received 'no way!'
