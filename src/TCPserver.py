import socket, time

if __name__ == "__main__":

    try:
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.bind(('', 50000))
        print('listening')
        serversocket.listen(5)

        while 1:
            (clientsocket, address) = serversocket.accept()
            clientsocket.close()
    except KeyboardInterrupt:
        pass
