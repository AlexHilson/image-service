import png
import numpy as np
import itertools

def loadPngTo8BitBinaryArray(fname):
    with open(fname, 'r') as f:
        r = png.Reader(f)
        d = r.read()
        image_array = np.vstack(d[2])

    normed = (image_array/255.0*15.0).astype(np.uint8)
    unormed = np.unpackbits(normed[:, :, None], 2)
        
    return unormed

def mungeArrays(data, shadows):
    combined = np.zeros(data.shape, dtype=np.uint8)
    combined[:, :, :4] = data[:, :, 4:] # numbers have been converted to 8 bit
    combined[:, :, 4:] = shadows[:, :, 4:] # so we only need to minor 4 bits
    
    return np.packbits(combined, 2)[:,:,0]

def write_array(array, savep):
    png_writer = png.Writer(height=4096, width=4096, bitdepth=8)
    with open(savep, 'wb') as f:
        png_writer.write(f, array)