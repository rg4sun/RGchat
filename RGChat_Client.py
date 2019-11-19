import getpass # 用于隐藏屏幕输入回显
import argparse, socket, sys, os
import json # 传送非字符串时使用，https://www.runoob.com/python/python-json.html
import threading

# 设置状态码字典，服务器根据客户端发送的状态码进行响应，
# 为了能使得服务器能区分客户端的不同请求，客户端每次发消息前必须发送一个状态码
# 然后服务器根据状态码来决定采用什么功能响应
statusMark = {'greet':'grt', 'login':'lgi', 'register':'reg', 'quit':'q','logout':'lgo', 'userDel':'del', 'privChat':'pri', 'pubChat':'pub'}
MAX_BYTES = 65535

def msgRecv(sock):
    while True:
        msg = sock.recv(MAX_BYTES)
        print(msg.decode())
            

def msgSend(sock):
    while True:
        # print('=====================================================')
        # print('请选择如何输入，若需要输密码请选择(2)，(2)会关闭屏幕回显')
        # flag = input('> (1):msg ; (2):Password <\n Option:')
        # if flag == '1':
        #     msg = input('>Enter msg< : ')
        # else:
        #     msg = getpass.getpass('Password:')
        msg = input()
        sock.send(msg.encode())
        if msg == statusMark['quit']:
            # print('now quit')
            os._exit(0)

def greeting(sock):
    # 先发送状态码
    sock.send(statusMark['greet'].encode())
    print('Client at {} Boots Successfully'.format(sock.getsockname()))
    # Client发送问候消息
    greetTxt = 'This is a user at {}'.format(sock.getsockname())
    sock.send(greetTxt.encode())  # 不指定encode编码参数默认使用utf-8
    # 接受Server问候消息
    serverGreet = sock.recv(MAX_BYTES)
    print(serverGreet.decode())
    print('===================================================')
    print('Welcome to RGchat!\n(1)登录 (2)注册 (q)退出 ')
    print('Please choose a function:')


def clientBoot(srvHost,port):
    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    # host = sys.argv[1] # 这里是读取用户输入的host，可以搜一下这个https://www.cnblogs.com/aland-1415/p/6613449.html
    sock.connect((srvHost,port))
    # 问候服务器
    greeting(sock)
    rcv = threading.Thread(target=msgRecv,args=(sock,), daemon=True)
    snd = threading.Thread(target=msgSend,args=(sock,), daemon=True)
    rcv.start()
    snd.start()
    rcv.join()
    snd.join()


if __name__ == "__main__":
    # parser = argparse.ArgumentParser(description='UDP based RGchat') # 创建ArgumentParser 对象
    # parser.add_argument('host',help='interface the server listens at')
    # parser.add_argument('-p',metavar='PORT',type=int,default=1060,help='UDP server port(default 1060)')
    # args = parser.parse_args()
    # clientBoot(args.host,args.p)
    clientBoot('127.0.0.1',1060)