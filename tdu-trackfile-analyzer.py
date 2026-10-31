# Wypisz CHPT sizes i ostatni bajt (checkpoint number) dla obu plików
from pathlib import Path
import re
online_data = Path("D:\Program Files (x86)\Atari\Test Drive Unlimited\Euro\Bnk\online RMFE0049.IGE").read_bytes()
offline_data = Path("D:\Program Files (x86)\Atari\Test Drive Unlimited\Euro\Bnk\offline RMFE0049.IGE").read_bytes()

def chpt_info(data):
    res = []
    for m in re.finditer(b'CHPT', data):
        pos = m.start()
        data_start = pos + 4
        # find next occurrence of CHPT or CARP or ENTI after this pos
        # search for next tag among CHPT, CARP, ENTI
        next_m = None
        for t in [b'CHPT', b'CARP', b'ENTI']:
            # find next occurrence after pos+1
            for n in re.finditer(re.escape(t), data[pos+1:]):
                np = pos+1 + n.start()
                # choose smallest positive np
                if np > pos:
                    if next_m is None or np < next_m:
                        next_m = np
        data_end = next_m if next_m is not None else len(data)
        size = data_end - data_start
        last_byte = data[data_end-1] if data_end>data_start else None
        res.append((pos, size, last_byte))
    return res

on_chpts = chpt_info(online_data)
off_chpts = chpt_info(offline_data)

print("Online CHPTs (pos, size, last_byte):")
for pos,size,last in on_chpts:
    print(hex(pos), size, last, "checkpoint#", last)
print("\nOffline CHPTs:")
for pos,size,last in off_chpts:
    print(hex(pos), size, last, "checkpoint#", last)
