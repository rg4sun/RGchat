import mysql.connector as dbConnector
import getpass # 用于隐藏屏幕输入回显
import argparse, socket, sys
import threading 
import json


# 设置状态码字典，服务器根据客户端发送的状态码进行响应，
# 为了能使得服务器能区分客户端的不同请求，客户端每次发消息前必须发送一个状态码
# 然后服务器根据状态码来决定采用什么功能响应
statusMark = {'greet':'grt', 'login':'lgi', 'register':'reg', 'quit':'q','logout':'lgo', 'userDel':'del', 'privChat':'pri', 'pubChat':'pub'}
MAX_BYTES = 65535

# userinfo ={'id':None,'name':None,'pwd':None,'host':None,'status':None} # id字段用于记录用户序号，用于检索userDate
# userData = [{'id':0,'name':'RGroot','pwd':'Rg123','host':None}] # 预先存入一个root用户，事实上是为了普通用户id从1计数
# 保存用户数据，之后把这个改成数据库或者导出txt

# 链接数据库---这里要改成登录
print('=========================================')
print('Connecting Database...')
mydb = dbConnector.connect(
    host='localhost',
    user='root', # input('Username: '),
    password='SHh001MIT', # getpass.getpass('Password: '),
    database='rgchat'
)
dbCursor = mydb.cursor() 
print('Database Successfully Connected !')
print('=========================================')

def info_list2Dict(infoList): # 数据库查询返回的一条记录是元组，为了方便后续编程，设计此函数
     return {'id':infoList[0],'name':infoList[1],'pwd':infoList[2],'host':infoList[3],'status':infoList[4]}

def handleGreeting(sock,addr):
    data, addr = sock.recvfrom(MAX_BYTES)
    print('Client:{} => {}'.format(addr,data.decode()))
    sock.sendto('> Conected to RGchat Server <'.encode(),addr)

def handlePrivChat(sock,cltAddr):
    bar = '========================================='
    notice = bar + '\n请输入私聊账户名：'
    sock.sendto(notice.encode(),cltAddr)
    contactName = sock.recv(MAX_BYTES).decode()
    # 拉取用户列表
    dbCursor.execute('SELECT name FROM userdata')
    userNameList = [ t[0] for t in dbCursor.fetchall()] # 数据大了这里效率会非常低
    contactExsitFlag = ''
    if contactName not in userNameList:
        notice = '聊天对象不存在，系统自动退出！'
        sock.sendto(notice.encode(),cltAddr)
    else:
        sql = 'SELECT host FROM userdata WHERE name="{}" '.format(contactName)
        print(contactName)
        print(sql)
        dbCursor.execute(sql)
        host = dbCursor.fetchone()[0].split(':')
        host[1] = int(host[1])
        contactAddr = tuple(host)
        # while True:
        notice = '已连接上 {} 请输入消息:'.format(contactName)
        sock.sendto(notice.encode(),cltAddr)
        recvMsg, addr= sock.recvfrom(MAX_BYTES)
        host = addr[0] + ':' + str(addr[1])
        sql = 'SELECT name FROM userdata WHERE host="{}" '.format(host)
        dbCursor.execute(sql)
        username = dbCursor.fetchone()[0]
        recvMsg = '{} => '.format(username) + recvMsg.decode()
        sock.sendto(recvMsg.encode(),contactAddr)
            # if addr == contactAddr:
            #     sock.sendto(recvMsg,cltAddr)
            # elif addr == cltAddr:
            #     sock.sendto(recvMsg,contactAddr)
        
def pubChat(userinfo):
    pass

def handleRegister(sock,addr):
    bar = '========================================='
    notice = bar + '\n请进行注册! '
    sock.sendto(notice.encode(),addr) # 发送提示
    
    dbCursor.execute('SELECT name FROM userdata')
    # userNameTuple = dbCursor.fetchall() # 这样返回的是[('RGroot',),('test',)]
    userNameList = [ t[0] for t in dbCursor.fetchall()] # 数据大了这里效率会非常低
    
    while True:
        notice = '需要输入Username: '
        sock.sendto(notice.encode(),addr)
        username = sock.recv(MAX_BYTES).decode()
        if username in userNameList:
            notice = '用户名已被注册，请尝试更换！'
            sock.sendto(notice.encode(),addr)
        else:
            break
    userPwd = ''
    pwdCheck = ''
    while True:
        notice = '需要输入Password: '
        sock.sendto(notice.encode(),addr)
        userPwd = sock.recv(MAX_BYTES).decode()
        notice = "需要输入Password Check: "
        sock.sendto(notice.encode(),addr)
        pwdCheck = sock.recv(MAX_BYTES).decode()
        if pwdCheck == userPwd:
            break
        notice = 'Check不通过，两次输入的密码不一致，请重新设置密码！'
        sock.sendto(notice.encode(),addr)
    # 新人入库
    insertData = (username,userPwd)
    sql = 'INSERT INTO userdata (name,pwd) VALUES (%s,%s)' # id自增，stauts、host设置了默认初始值0、NULL
    dbCursor.execute(sql,insertData) # 执行sql语句
    mydb.commit() # 数据表内容有更新，必须使用到该语句
    # 不知道commit有没有更新成功的返回值，有的话可以写一个regFlag
    notice = '注册成功! \n' + bar
    sock.sendto(notice.encode(),addr)

def handleUserDel(username,sock,addr): # 一般这个模块是用户登录之后才出现，所以删除用户的时候不用查用户是否存在

    bar = '========================================='
    # notice = bar + '\n请输入要删除的账户名:'
    # sock.sendto(notice.encode(),addr) # 发送提示
    # username = sock.recv(MAX_BYTES).decode() # 获取要删的username
    notice = bar + '\n敏感操作：正在删除账户 {} ...'.format(username)
    sock.sendto(notice.encode(),addr) # 发送提示
    # 拉取对应于该user的pwd
    sql = 'SELECT pwd FROM userdata WHERE name="{}" '.format(username)
    dbCursor.execute(sql)
    # pwd = dbCursor.fetchall()[0][0] # fetchall 结果应该是[(pwd,)]
    pwd = dbCursor.fetchone()[0] # fetchone 结果应该是 (pwd,)
    errPwdCount=0
    while True:
        notice = '需要输入Password: '
        sock.sendto(notice.encode(),addr)
        userPwd = sock.recv(MAX_BYTES).decode()
        if pwd != userPwd:
            errPwdCount+=1
            notice = '密码输入错误，还有{}次机会！'.format(3-errPwdCount)
            sock.sendto(notice.encode(),addr)
            if errPwdCount>2:
                notice = '您已经输错3次密码，系统将自动退出！'
                sock.sendto(notice.encode(),addr)
                return
        else:
            sql = 'DELETE FROM userdata WHERE name="{}" '.format(username)
            dbCursor.execute(sql)
            mydb.commit() # 只要数据表有变动就要commit
            notice = '账户{}已被成功删除!\n'.format(username) + bar
            sock.sendto(notice.encode(),addr) # 发送提示
            return

def handleLogout(sock, addr): # 没写完，要等进入mainframe写完之后调用break
    username = sock.recv(MAX_BYTES).decode() # 接收要退出的账户名
    # 注销后将该用户状态设置为0表示离线，同时清空host
    sql = 'UPDATE userdata SET status={},host=Null WHERE name="{}" '.format(0,username)
    dbCursor.execute(sql)
    mydb.commit()
    pass

def mainFrame(userinfo,sock,addr):
    bar = '========================================='
    notice = bar + '\nwelcome {} at {} , status: {}'.format(userinfo['name'],userinfo['host'],userinfo['status'])
    notice += '\n请选择功能：(pri)私聊; (pub)群聊 (del)删除账户 (q)退出'
    sock.sendto(notice.encode(),addr)
    # option = sock.recv(MAX_BYTES).decode()
    # if option == '1':
    #     handlePrivChat(sock,addr)
    # elif option == '2':
    #     pubChat(userinfo)
    # elif option == '3':
    #     handleUserDel(userinfo['name'],sock,addr)
    # elif option == '4':
    #     handleLogout(userinfo['name'],sock,addr)

def handleLogin(sock,addr): # host没写
    bar = '========================================='
    notice = bar + '\n欢迎使用RGchat！，请输入用户名：'
    sock.sendto(notice.encode(),addr)

    username, addr = sock.recvfrom(MAX_BYTES)
    username = username.decode()

    # 拉取用户列表
    dbCursor.execute('SELECT name FROM userdata')
    userNameList = [ t[0] for t in dbCursor.fetchall()] # 数据大了这里效率会非常低

    if username not in userNameList:
        notice = '账号{}不存在！请注册：'.format(username)
        sock.sendto(notice.encode(),addr)
        handleLogin(handleRegister(sock,addr),addr)
    else:
        # 拉取对应密码
        sql = 'SELECT pwd FROM userdata WHERE name= "{}" '.format(username)
        dbCursor.execute(sql)
        pwd = dbCursor.fetchone()[0]
        errPwdCount=0
        notice = 'Password: '
        sock.sendto(notice.encode(),addr)
        userPwd = sock.recv(MAX_BYTES).decode()
        while(userPwd != pwd):
            errPwdCount+=1
            notice = '错误的密码，还可以尝试{}次：'.format(5-errPwdCount)
            sock.sendto(notice.encode(),addr)
            notice = 'Password: '
            sock.sendto(notice.encode(),addr)
            userPwd = sock.recv(MAX_BYTES).decode()
            if errPwdCount>3:
                notice = '您已经输错5次密码，系统将自动退出！'
                sock.sendto(notice.encode(),addr)
                return
        # 登录后将该用户状态设置为1表示在线,同时记录用户地址
        addrStr = addr[0]+':'+str(addr[1]) # 把tuple类型的addr变成字符串,host:port
        sql = 'UPDATE userdata SET status={}, host="{}" WHERE name="{}" '.format(1,addrStr,username) 
        dbCursor.execute(sql)
        mydb.commit()
        # 抽取用户信息，因为mainFrame需要获得用户所有信息
        sql = 'SELECT * FROM userdata WHERE name="{}" '.format(username)
        dbCursor.execute(sql)
        userinfo = dbCursor.fetchone()
        # userinfo = info_tuple2List(infoTuple) # 弃用这个了，因为传送的时候用json格式不用考虑list和tuple的区别了
        userinfo = json.dumps(userinfo)
        userinfo = json.loads(userinfo) # 得到的userinfo是list
        userinfo = info_list2Dict(userinfo) # 转成字典，mainframe要用字典
        mainFrame(userinfo,sock,addr)



def serverResponse4ever(sock):
    print('in serverResponse4ever')
    while True:
        status, addr = sock.recvfrom(MAX_BYTES)
        if status.decode() == statusMark['greet']:
            handleGreeting(sock, addr)
            # Thread(target=handleGreeting,args=(sock, addr))
            # break # 测试用
            continue
        elif status.decode() == statusMark['login']:
            handleLogin(sock, addr)
            # break # 测试用
            continue
        elif status.decode() == statusMark['register']:
            handleRegister(sock, addr)
            # break # 测试用
            continue
        elif status.decode() == statusMark['logout']:
            handleLogout(sock, addr)
            # break # 测试用
            continue
        elif status.decode() == statusMark['userDel']:
            handleUserDel(sock, addr)
            # break # 测试用
            continue
        elif status.decode() == statusMark['privChat']:
            handlePrivChat(sock,addr)
            # break # 测试用
            continue
        elif status.decode() == statusMark['quit']:
            print('Client at {} exit!'.format(addr))
            sock.sendto('Goodby~'.encode(),addr)

def threadsCreate(sock, workers=5):
    arg = (sock,) # 参数必须是tuple
    for i in range(workers):
        threading.Thread(target=serverResponse4ever, args=arg).start()
        print(threading.enumerate())        

def serverBoot(interface, port):
    # host = '127.0.0.1'
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((interface, port))
    print('Sever listen at {}'.format(sock.getsockname()))
    serverResponse4ever(sock)
        

if __name__ == '__main__':
    # parser = argparse.ArgumentParser(description='UDP based RGchat') # 创建ArgumentParser 对象
    # parser.add_argument('host', metavar='HOST', type=str, default='127.0.0.1', help='interface the server listens at(default 127.0.0.1)')
    # parser.add_argument('-p',metavar='PORT',type=int,default=1060,help='UDP server port(default 1060)')
    # args = parser.parse_args()
    # serverBoot(args.host,args.p)
    serverBoot('127.0.0.1',1060)
    # print(sys.argv[2])
    
