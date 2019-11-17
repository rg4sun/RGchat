import getpass # 用于隐藏屏幕输入回显
import argparse, socket, sys
import threading

def clientBoot(host,port):
    MAX_BYTES = 65535
    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    host = sys.argv[1] # 这里是读取用户输入的host，可以搜一下这个https://www.cnblogs.com/aland-1415/p/6613449.html
    sock.connect((host,port))
    print('Client at {}'.format(sock.getsockname()))
    greetTxt = 'This is a user at {}'.format(sock.getsockname())
    greetBytes = greetTxt.encode() # 不指定encode编码参数默认使用utf-8
    sock.send(greetBytes)
    serverGreet = sock.recv(MAX_BYTES)
    print(serverGreet.decode())
    print('===================================================')
    username = input('请输入用户名称：')
    sock.send(username.encode())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='UDP based RGchat') # 创建ArgumentParser 对象
    parser.add_argument('host',help='interface the server listens at')
    parser.add_argument('-p',metavar='PORT',type=int,default=1060,help='UDP server port(default 1060)')
    args = parser.parse_args()
    clientBoot(args.host,args.p)