#!/usr/bin/env python3
import socket
import argparse
import time

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--mode", choices=["vanilla", "buffered", "reliable", "window"], required=True)
    args = parser.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", args.port))
    print(f"[SERVER] Listening on port {args.port} (mode={args.mode})")

    buffer = {}
    received = []

    while True:
        data, addr = sock.recvfrom(4096)
        msg = data.decode()

        if msg.startswith("END"):
            if args.mode == "vanilla":
                print("Arrival order:", received)
            else:
                ordered = [buffer[i] for i in sorted(buffer)]
                print("In-order delivery:", ordered)
            buffer.clear()
            received.clear()
            continue

        seq, payload = msg.split(":", 1)
        seq = int(seq)

        if args.mode == "vanilla":
            print(f"[VANILLA] got SEQ={seq} -> {payload}")
            received.append(seq)

        elif args.mode == "buffered":
            print(f"[BUFFERED] storing SEQ={seq}")
            buffer[seq] = payload

        elif args.mode == "reliable":
            print(f"[RELIABLE] got SEQ={seq}, sending ACK")
            buffer[seq] = payload
            sock.sendto(f"ACK:{seq}".encode(), addr)

        elif args.mode == "window":
            print(f"[WINDOW] got SEQ={seq}, sending cumulative ACK")
            buffer[seq] = payload
           
            expected = 0
            while expected in buffer:
                expected += 1
            sock.sendto(f"ACK:{expected-1}".encode(), addr)

if __name__ == "__main__":
    main()
