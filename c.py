#!/usr/bin/env python3
import socket
import argparse
import random
import time
import sys

def typewriter(msg, delay=0.05):

    for ch in msg:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--mode", choices=["vanilla", "reliable", "window"], required=True)
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
        unacked = {seq: payload for seq, payload in packets}
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
                print("[CLIENT] Timeout waiting for ACKs...")
        sock.sendto("END".encode(), addr)
        print("[CLIENT] All packets delivered")

 
    elif args.mode == "window":
        WINDOW_SIZE = 5
        TIMEOUT = 3.0
        base = 0
        nextseq = 0
        total = len(packets)
        sock.settimeout(0.2)
        timer_start = None

        print(f"[CLIENT] Starting sliding window transfer (W={WINDOW_SIZE})")

        while base < total:
    
            while nextseq < base + WINDOW_SIZE and nextseq < total:
                if random.random() < args.drop:
                    print(f"[CLIENT] Simulated drop SEQ={nextseq}")
                else:
                    msg = f"{nextseq}:{packets[nextseq][1]}"
                    sock.sendto(msg.encode(), addr)
                    print(f"[CLIENT] Sent SEQ={nextseq}")
                if base == nextseq:
                    timer_start = time.time()
                nextseq += 1

     
            try:
                data, _ = sock.recvfrom(1024)
                ack = data.decode()
                if ack.startswith("ACK:"):
                    ack_seq = int(ack.split(":")[1])
                    print(f"[CLIENT] Got cumulative ACK={ack_seq}")
                    base = ack_seq + 1
                    if base == nextseq:
                        timer_start = None
                    else:
                        timer_start = time.time()
            except socket.timeout:
                pass

         
            if timer_start:
                remaining = TIMEOUT - (time.time() - timer_start)
                if remaining > 0:
                    sys.stdout.write(f"\r[TIMER] {remaining:0.1f}s remaining ")
                    sys.stdout.flush()
                else:
                    sys.stdout.write("\r")
                    typewriter("[CLIENT] Timeout! Retransmitting window...")
                    for seq in range(base, nextseq):
                        msg = f"{seq}:{packets[seq][1]}"
                        sock.sendto(msg.encode(), addr)
                        print(f"[CLIENT] Retransmit SEQ={seq}")
                    timer_start = time.time()
                    print()

        sock.sendto("END".encode(), addr)
        print("[CLIENT] Sliding window transfer complete")

if __name__ == "__main__":
    main()
