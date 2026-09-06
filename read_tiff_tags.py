import struct

def read_ifd(path):
    with open(path, 'rb') as f:
        data = f.read(65536)  # header + first IFD should be near the start; grow if needed
    byteorder = data[0:2]
    if byteorder == b'II':
        endian = '<'
    elif byteorder == b'MM':
        endian = '>'
    else:
        raise ValueError('not a tiff')
    magic = struct.unpack(endian+'H', data[2:4])[0]
    bigtiff = magic == 43
    if bigtiff:
        raise ValueError('bigtiff not handled here')
    ifd_offset = struct.unpack(endian+'I', data[4:8])[0]

    # may need more data if ifd_offset is beyond what we read
    with open(path, 'rb') as f:
        f.seek(0, 2)
        filesize = f.tell()
        f.seek(0)
        data = f.read(min(filesize, ifd_offset + 200000))

    num_entries = struct.unpack(endian+'H', data[ifd_offset:ifd_offset+2])[0]
    tags = {}
    TYPE_SIZES = {1:1,2:1,3:2,4:4,5:8,6:1,7:1,8:2,9:4,10:8,11:4,12:8}
    for i in range(num_entries):
        entry_offset = ifd_offset + 2 + i*12
        tag, ftype, count = struct.unpack(endian+'HHI', data[entry_offset:entry_offset+8])
        value_offset_bytes = data[entry_offset+8:entry_offset+12]
        tsize = TYPE_SIZES.get(ftype, 1)
        total_size = tsize * count
        if total_size <= 4:
            raw = value_offset_bytes[:total_size]
        else:
            voff = struct.unpack(endian+'I', value_offset_bytes)[0]
            raw = data[voff:voff+total_size]
        if ftype == 3:  # SHORT
            vals = struct.unpack(endian+('H'*count), raw[:2*count])
        elif ftype == 4:  # LONG
            vals = struct.unpack(endian+('I'*count), raw[:4*count])
        elif ftype == 12:  # DOUBLE
            vals = struct.unpack(endian+('d'*count), raw[:8*count])
        elif ftype == 2:  # ASCII
            vals = raw.split(b'\x00')[0].decode('latin1', errors='replace')
        else:
            vals = raw
        tags[tag] = vals
    return tags

if __name__ == '__main__':
    import sys
    tags = read_ifd(sys.argv[1])
    NAMES = {
        256: 'ImageWidth', 257: 'ImageHeight', 258: 'BitsPerSample', 259: 'Compression',
        262: 'PhotometricInterpretation', 277: 'SamplesPerPixel',
        33550: 'ModelPixelScaleTag', 33922: 'ModelTiepointTag', 34264: 'ModelTransformationTag',
        34735: 'GeoKeyDirectoryTag', 34736: 'GeoDoubleParamsTag', 34737: 'GeoAsciiParamsTag',
        42112: 'GDAL_METADATA', 42113: 'GDAL_NODATA',
    }
    for tag, val in sorted(tags.items()):
        name = NAMES.get(tag, str(tag))
        v = val if not isinstance(val, tuple) or len(val) < 20 else (val[:20], '...')
        print(name, tag, v)
