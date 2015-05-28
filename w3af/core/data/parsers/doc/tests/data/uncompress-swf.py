import sys
import zlib

if __name__ == '__main__':
    filename = sys.argv[1]
    
    compressed_data = file(filename).read()[8:]
    uncompressed_data = zlib.decompress(compressed_data)
    
    output_file = '%s.bytecode' % filename
    file(output_file, 'w').write(uncompressed_data)
