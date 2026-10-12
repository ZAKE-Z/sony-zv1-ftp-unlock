"""Read-only Senser receive adapter for the observed Sony 054c:0336 device.

Uses Sony-PMCA-RE's packet structures and sequence state, without discarding
nonempty USB data at 32 KiB boundaries. Applies only during a FileControl READ.
Upstream: https://github.com/ma1co/Sony-PMCA-RE/blob/master/pmca/usb/sony.py
"""
import contextlib
import io


def read_exact(driver, count, record):
    parts = []
    remaining = count
    empty_reads = 0
    while remaining:
        data = driver.read(min(remaining, 0x8000))
        if not data:
            # Genuine zero-length USB packets contain no file bytes.
            empty_reads += 1
            record['zero_length_packets'] = record.get('zero_length_packets', 0) + 1
            if empty_reads > 16:
                raise RuntimeError('Too many empty USB reads; stopping the transfer.')
            continue
        empty_reads = 0
        if len(data) > remaining:
            raise RuntimeError('USB backend returned more bytes than requested.')
        parts.append(data)
        remaining -= len(data)
    return b''.join(parts)


@contextlib.contextmanager
def file_read_receiver(cam, record, limit):
    senser = cam.dev
    if senser.driver.getId() != (0x054c, 0x0336):
        raise RuntimeError('This receive adapter is restricted to Sony 054c:0336.')
    original = senser.sendSenserPacket

    def receive(pfunc, data, oData=None):
        hsize = cam.FileControlHeader.size
        if pfunc != cam.SONY_PFUNC_FileControl or len(data) < hsize:
            raise RuntimeError('Only FileControl READ is allowed in this context.')
        request = cam.FileControlHeader.unpack(data[:hsize])
        if request.cmd != cam.SONY_FILE_CONTROL_READ or len(data) > senser.SenserMaxSize:
            raise RuntimeError('Non-read or oversized request refused.')
        wire_header = senser.SenserPacketHeader.pack(
            size=len(data), pFunc=pfunc, sequence=senser._sequence,
            version=0, miconType=0, offsetType=0, response=0)
        senser.driver.write(wire_header + data)
        output = io.BytesIO() if oData is None else oData
        captured = 0
        record['senser_headers'] = []
        while True:
            raw = read_exact(senser.driver, senser.SenserPacketHeader.size, record)
            header = senser.SenserPacketHeader.unpack(raw)
            record['senser_headers'].append({
                'size': header.size, 'sequence': header.sequence,
                'pfunc': header.pFunc, 'response': header.response})
            if header.sequence != senser._sequence:
                raise RuntimeError('Wrong Senser response sequence.')
            if header.size > limit - captured:
                raise RuntimeError('Senser response exceeds the file capture limit.')
            remaining = min(header.size, senser.SenserMaxSize)
            while remaining:
                count = min(remaining, senser.SenserChunkSize)
                payload = read_exact(senser.driver, count, record)
                output.write(payload)
                captured += len(payload)
                remaining -= len(payload)
                # No extra 512-byte read: every nonempty payload byte is retained.
            if header.size <= senser.SenserMaxSize:
                break
        senser._sequence += 1
        record['protocol_payload_bytes'] = captured
        return header.response, output.getvalue() if oData is None else None

    senser.sendSenserPacket = receive
    try:
        yield
    finally:
        senser.sendSenserPacket = original
