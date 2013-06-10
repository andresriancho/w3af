if __name__ == '__main__':
    import socket
    import sys

    ip = sys.argv[1]
    port = sys.argv[2]
    f = file(sys.argv[3], 'w')

    cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cs.connect((ip, port))

    while 1:
        data = cs.recv(1024)
        if not data:
            break
        f.write(data)

    cs.close()
    f.close()
