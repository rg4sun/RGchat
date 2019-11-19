import threading
from functools import partial
from socket import socket, AF_INET, SOCK_DGRAM

class LazyConnection:
    def __init__(self, address, family=AF_INET, type=SOCK_DGRAM):
        self.address = address
        self.family = AF_INET
        self.type = SOCK_DGRAM
        self.local = threading.local()

    def __enter__(self):
        if hasattr(self.local, 'sock'):
            raise RuntimeError('Already connected')
        # 把socket连接存入local中
        self.local.sock = socket(self.family, self.type)
        self.local.sock.connect(self.address)
        return self.local.sock

    def __exit__(self, exc_ty, exc_val, tb):
        self.local.sock.close()
        del self.local.sock

def spider(conn, website):
    with conn as s:
        header = 'GET / HTTP/1.1\r\nHost: {}\r\nConnection: close\r\n\r\n'.format(website)
        s.send(header.encode("utf-8"))
        resp = b''.join(iter(partial(s.recv, 100000), b''))
    print('Got {} bytes'.format(len(resp)))

if __name__ == '__main__':
    # 建立一个TCP连接
    conn = LazyConnection(('www.sina.com.cn', 80))

    # 爬取两个页面
    t1 = threading.Thread(target=spider, args=(conn,"news.sina.com.cn"))
    t2 = threading.Thread(target=spider, args=(conn,"blog.sina.com.cn"))
    t1.start()
    t2.start()
    t1.join()
    t2.join()