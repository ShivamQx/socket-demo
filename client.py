#!/usr/bin/env python3
import socket
import argparse
import random
import time

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--mode", choices=["vanilla","reliable"], required=True)
    parser.add_argument("--n", type=int, default=10, help="number of packets")
    parser.add_argument("--drop", type=float, default=0.2, help="drop probability")
    parser.add_argument("--shuffle", action="store_true", help="shuffle order (vanilla only)")
    args = parser.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    addr = (args.host, args.port)

    packets = [(i, f"DATA_{i}") for i in range(args.n)]

    if args.mode == "vanilla":
        send_list = packets[:]
        if args.shuffle:
            random.shuffle(send_list)
        for seq, payload in send_list:
            if random.random() < args.drop:
                print(f"[CLIENT] DROPPED SEQ={seq}")
                continue
            msg = f"{seq}:{payload}"
            sock.sendto(msg.encode(), addr)
            print(f"[CLIENT] Sent SEQ={seq}")
            time.sleep(0.05)
        sock.sendto("END".encode(), addr)

    elif args.mode == "reliable":
        sock.settimeout(0.5)
        unacked = {seq:payload for seq,payload in packets}
        while unacked:
            for seq in list(unacked.keys()):
                if random.random() < args.drop:
                    print(f"[CLIENT] Simulated drop SEQ={seq}")
                else:
                    msg = f"{seq}:{unacked[seq]}"
                    sock.sendto(msg.encode(), addr)
                    print(f"[CLIENT] Sent SEQ={seq}")
            try:
                data, _ = sock.recvfrom(1024)
                ack = data.decode()
                if ack.startswith("ACK:"):
                    ack_seq = int(ack.split(":")[1])
                    if ack_seq in unacked:
                        print(f"[CLIENT] Got ACK for {ack_seq}")
                        del unacked[ack_seq]
            except socket.timeout:
                pass
        sock.sendto("END".encode(), addr)
        print("[CLIENT] All packets delivered")

if __name__ == "__main__":
    main()
