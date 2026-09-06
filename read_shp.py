import struct
import json
import sys

def read_dbf(path):
    with open(path, 'rb') as f:
        data = f.read()
    numrec = struct.unpack('<I', data[4:8])[0]
    lenheader = struct.unpack('<H', data[8:10])[0]
    numfields = (lenheader - 33) // 32
    fields = []
    for i in range(numfields):
        base = 32 + i*32
        name = data[base:base+11].split(b'\x00')[0].decode('latin1')
        ftype = chr(data[base+11])
        flen = data[base+16]
        fields.append((name, ftype, flen))
    records = []
    recsize = sum(f[2] for f in fields) + 1
    offset = lenheader
    for r in range(numrec):
        rec_data = data[offset:offset+recsize]
        offset += recsize
        if not rec_data or rec_data[0:1] == b'*':
            continue
        pos = 1
        rec = {}
        for name, ftype, flen in fields:
            raw = rec_data[pos:pos+flen].decode('latin1', errors='replace').strip()
            pos += flen
            rec[name] = raw
        records.append(rec)
    return fields, records

def read_shp(path):
    with open(path, 'rb') as f:
        data = f.read()
    # header is 100 bytes
    shape_type = struct.unpack('<i', data[32:36])[0]
    shapes = []
    offset = 100
    n = len(data)
    while offset < n:
        rec_num, content_len = struct.unpack('>ii', data[offset:offset+8])
        offset += 8
        content = data[offset:offset+content_len*2]
        stype = struct.unpack('<i', content[0:4])[0]
        if stype == 0:
            shapes.append({'type': 'null'})
        elif stype in (5, 15, 25):  # Polygon variants
            xmin, ymin, xmax, ymax = struct.unpack('<4d', content[4:36])
            numparts, numpoints = struct.unpack('<2i', content[36:44])
            parts = struct.unpack('<%di' % numparts, content[44:44+4*numparts])
            pt_start = 44 + 4*numparts
            points = []
            for i in range(numpoints):
                x, y = struct.unpack('<2d', content[pt_start+16*i:pt_start+16*i+16])
                points.append((x, y))
            # split into rings by parts
            rings = []
            for i in range(numparts):
                start = parts[i]
                end = parts[i+1] if i+1 < numparts else numpoints
                rings.append(points[start:end])
            shapes.append({'type': 'polygon', 'bbox': (xmin, ymin, xmax, ymax), 'rings': rings})
        elif stype in (3, 13, 23):  # Polyline
            xmin, ymin, xmax, ymax = struct.unpack('<4d', content[4:36])
            numparts, numpoints = struct.unpack('<2i', content[36:44])
            parts = struct.unpack('<%di' % numparts, content[44:44+4*numparts])
            pt_start = 44 + 4*numparts
            points = []
            for i in range(numpoints):
                x, y = struct.unpack('<2d', content[pt_start+16*i:pt_start+16*i+16])
                points.append((x, y))
            lines = []
            for i in range(numparts):
                start = parts[i]
                end = parts[i+1] if i+1 < numparts else numpoints
                lines.append(points[start:end])
            shapes.append({'type': 'polyline', 'bbox': (xmin, ymin, xmax, ymax), 'lines': lines})
        elif stype in (1, 11, 21):  # Point
            x, y = struct.unpack('<2d', content[4:20])
            shapes.append({'type': 'point', 'x': x, 'y': y})
        else:
            shapes.append({'type': 'unknown', 'stype': stype})
        offset += content_len*2
    return shape_type, shapes

if __name__ == '__main__':
    base = sys.argv[1]
    fields, records = read_dbf(base + '.dbf')
    stype, shapes = read_shp(base + '.shp')
    print('shape_type', stype, 'n_shapes', len(shapes), 'n_records', len(records))
    print('fields', fields)
    for i in range(min(5, len(records))):
        print('---', i)
        print(records[i])
        print(shapes[i]['type'], shapes[i].get('bbox'))
