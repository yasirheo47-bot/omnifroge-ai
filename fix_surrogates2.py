# Binary fix: surrogate pairs encoded as CESU-8/WTF-8 in the file
# \ud83d\uddbc (🖼) in Python surrogatepass = bytes ED A0 BD ED B6 BC -> should be F0 9F 96 BC
# \ud83c\udfa8 (🎨) in Python surrogatepass = bytes ED A0 BC ED BF A8 -> should be F0 9F 8E A8

with open('scenx_bot.py', 'rb') as f:
    data = f.read()

print(f"File size: {len(data)} bytes")

# Check for ED A0 xx ED Bx xx patterns (surrogate pairs)
import re
surrogates = [(m.start(), m.group().hex()) for m in re.finditer(b'\xed[\xa0-\xaf].', data)]
print(f"Surrogate high bytes found: {len(surrogates)}")
for pos, h in surrogates[:10]:
    print(f"  pos {pos}: {data[pos:pos+6].hex()}")

# Replace known surrogate pairs
replacements = {
    b'\xed\xa0\xbd\xed\xb6\xbc': b'\xf0\x9f\x96\xbc',  # 🖼 U+1F5BC
    b'\xed\xa0\xbc\xed\xbf\xa8': b'\xf0\x9f\x8e\xa8',  # 🎨 U+1F3A8
    b'\xed\xa0\xbc\xed\xbf\xa0': b'\xf0\x9f\x8f\xa0',  # 🏠 fallback
}

for bad, good in replacements.items():
    count = data.count(bad)
    if count:
        print(f"Replacing {bad.hex()} -> {good.hex()} ({count}x)")
        data = data.replace(bad, good)

# Also scan for any remaining surrogate-encoded bytes (ED A0..AF followed by ED B0..BF)
remaining = re.findall(b'\xed[\xa0-\xaf].\xed[\xb0-\xbf].', data)
if remaining:
    print(f"WARNING: {len(remaining)} unhandled surrogate pairs remain: {[r.hex() for r in set(remaining)]}")
else:
    print("No surrogate pairs remain")

with open('scenx_bot.py', 'wb') as f:
    f.write(data)

print("Done")
