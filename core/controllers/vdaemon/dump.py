if __name__ == "__main__":
    import sys
    res = "file_dump = '"

    for i in file(sys.argv[1]).read():
        res += '\\x' + hex(ord(i))[2:].zfill(2)

    res += "'"
    print res
