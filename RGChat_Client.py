import getpass # 用于隐藏屏幕输入回显
import argparse, socket, sys
import json # 传送非字符串时使用，https://www.runoob.com/python/python-json.html
import threading

# 设置状态码字典，服务器根据客户端发送的状态码进行响应，
# 为了能使得服务器能区分客户端的不同请求，客户端每次发消息前必须发送一个状态码
# 然后服务器根据状态码来决定采用什么功能响应
statusMark = {'greet':'0', 'login':'1', 'register':'2', 'logout':'3', 'userDel':'4'} 
MAX_BYTES = 65535

# def info_tuple2List(infoTuple): # 数据库查询返回的一条记录是元组，为了方便后续编程，设计此函数
#     return {'id':infoTuple(0),'name':infoTuple(1),'pwd':infoTuple(2),'host':infoTuple(3),'status':infoTuple(4)}
# 发生异常: TypeError
# 'tuple' object is not callable
# 傻了。。。下标引用的括号写出了，变成了函数调用的圆括号了()

def info_list2Dict(infoList): # 数据库查询返回的一条记录是元组，为了方便后续编程，设计此函数
     return {'id':infoList[0],'name':infoList[1],'pwd':infoList[2],'host':infoList[3],'status':infoList[4]}

def mainFrame(userinfo):
    print('welcome {} at {} , status: {}'.format(userinfo['name'],userinfo['host'],userinfo['status']))

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
    username = input('Welcome to RGchat!\nPlease enter user name: ')
    return username


def register(sock):

    # 先发送状态码
    sock.send(statusMark['register'].encode())
    print('=========================================')
    print('请进行注册！')

    # dbCursor.execute('SELECT name FROM userdata')
    # userNameTuple = dbCursor.fetchall() # 这样返回的是[('RGroot',),('test',)]
    # userNameTuple = [ t[0] for t in dbCursor.fetchall()] # 数据大了这里效率会非常低
    # 以上服务器处理

    # 从服务器拉取用户名列表，用于判断是否被注册过
    userNameList = sock.recv(MAX_BYTES) # 接收服务器查询数据库的结果，
    userNameList = json.loads(userNameList.decode()) # 由于服务器只能传送str，所有用json把字符串恢复成相应对象

    while(1): # 判断用户名是否被注册过，更好的办法是设计数据库的时候name字段不能重，以后再优化了
        username = input('Username: ')
        if username in userNameList:
            print('用户名已被注册，请尝试更换！')
        else:
            break
    userPwd = getpass.getpass('Password: ')
    pwdCheck = getpass.getpass("Password Check: ")
    while(userPwd != pwdCheck): # 密码验证
        print('Check不通过，两次输入的密码不一致，请重新设置密码！')
        userPwd = getpass.getpass('Password: ')
        pwdCheck = getpass.getpass("Password Check: ")

    # 将注册的信息打包成tuple并dumps之后发给服务器
    userInfo = json.dumps((username,userPwd)) 
    sock.send(userInfo.encode())

    # 新人入库
    # sql = 'INSERT INTO userdata (name,pwd) VALUES (%s,%s)' # id自增，stauts、host设置了默认初始值0、NULL
    # insertData = (username, userPwd)
    # dbCursor.execute(sql,insertData) # 执行sql语句
    # mydb.commit() # 数据表内容有更新，必须使用到该语句
    regFlag = sock.recv(MAX_BYTES)
    if regFlag.decode() == '0':
        print('出现错误，注册失败，请稍后尝试，即将断开连接...')
    else:
        print('注册成功！')
        print('=========================================')
    
    return username

def userDel(username,sock): # 一般这个模块是用户登录之后才出现，所以删除用户的时候不用查用户是否存在
    # 先发送状态码
    sock.send(statusMark['userDel'].encode())
    print('=========================================')
    print('敏感操作：正在删除账户 {} ...'.format(username))
    sock.send(username.encode()) # 将要删的username发送给服务器
    # sql = 'SELECT pwd FROM userdata WHERE name="{}" '.format(username)
    # dbCursor.execute(sql)
    # # pwd = dbCursor.fetchall()[0][0] # fetchall 结果应该是[(pwd,)]
    # pwd = dbCursor.fetchone()[0] # fetchone 结果应该是 (pwd,)
    pwd = sock.recv(MAX_BYTES).decode() # 接收密码，用于检验
    errPwdCount=0
    while(1):
        pwdCheck = getpass.getpass('Password: ')
        if pwd != pwdCheck:
            errPwdCount+=1
            print('密码输入错误，还有{}次机会！'.format(3-errPwdCount))
            if errPwdCount>2:
                print('您已经输错3次密码，系统将自动退出！')
                pwdFlag = '0'
                sock.send(pwdFlag.encode()) # 发送密码检验标志符
                return
        else:
            pwdFlag = '1'
            sock.send(pwdFlag.encode()) # 发送密码检验标志符
            # sql = 'DELETE FROM userdata WHERE name="{}" '.format(username)
            # dbCursor.execute(sql)
            # mydb.commit() # 只要数据表有变动就要commit
            print('账户已被成功删除！')
            print('=========================================')
            return
    
def login(username,sock): # host没写
    # 先发送状态码
    sock.send(statusMark['login'].encode())
    print('=========================================')
    print('尊敬的{}, 欢迎使用RGchat！，请登录：'.format(username))
    sock.send(username.encode()) # 将要登录d的username发送给服务器

    # dbCursor.execute('SELECT name FROM userdata')
    # userNameTuple = [ t[0] for t in dbCursor.fetchall()] # 数据大了这里效率会非常低
    userNameList = sock.recv(MAX_BYTES) # 拉取用户列表
    userNameList = json.loads(userNameList.decode())

    if username not in userNameList:
        print('账号{}不存在！请注册：'.format(username))
        userExistFlag = '0'
        sock.send(userExistFlag.encode()) # 发送用户不存在标识
        login(register(sock),sock) # 注册完了重新login
        # mainFrame(userinfo) 
    else:
        # sql = 'SELECT pwd FROM userdata WHERE name= "{}" '.format(username)
        # dbCursor.execute(sql)
        # pwd = dbCursor.fetchone()[0]
        userExistFlag = '1'
        sock.send(userExistFlag.encode()) # 发送用户存在标识
        pwd = sock.recv(MAX_BYTES).decode() # 获取密码，之后优化要加密
        errPwdCount=0
        userPwd = getpass.getpass('Password: ')
        while(userPwd != pwd):
            errPwdCount+=1
            userpwd=getpass.getpass('错误的密码，还可以尝试{}次：'.format(5-errPwdCount))
            if errPwdCount>3:
                print('您已经输错5次密码，系统将自动退出！')
                pwdFlag = '0'
                sock.send(pwdFlag.encode()) # 发送密码检验标志符
                return 
        pwdFlag = '1'
        sock.send(pwdFlag.encode()) # 发送密码检验标志符
        # # 登录后将该用户状态设置为1表示在线
        # sql = 'UPDATE userdata SET status={} WHERE name="{}" '.format(1,username) 
        # dbCursor.execute(sql)
        # mydb.commit()
        # # 抽取用户信息，因为mainFrame需要获得用户所有信息
        # sql = 'SELECT * FROM userdata WHERE name="{}" '.format(username)
        # dbCursor.execute(sql)
        # infoTuple = dbCursor.fetchone()
        # userinfo = info_tuple2List(infoTuple) 
        userinfo = sock.recv(MAX_BYTES).decode()
        userinfo = json.loads(userinfo) # 得到的userinfo是list
        userinfo = info_list2Dict(userinfo) # 转成字典，mainframe要用字典
        print('=========================================')
        mainFrame(userinfo)

# 一般这个模块是用户登录之后才出现，所以删除用户的时候不用查用户是否存在
def logout(username,sock): # 没写完，要等进入mainframe写完之后调用break
    # 先发送状态码
    sock.send(statusMark['logout'].encode())
    sock.send(username.encode()) # 发送要退出的账户名
    print('=========================================')
    print('正在退出账户...')
    # # 注销后将该用户状态设置为0表示离线，同时清空host
    # sql = 'UPDATE userdata SET status={},host=Null WHERE name="{}" '.format(0,username)
    # dbCursor.execute(sql)
    # mydb.commit()
    print('Goodbye~ {} '.format(username))
    print('=========================================')
    pass

def privChat(pair):
    pass
def groupChat(grp):
    pass
def pubChar():
    pass

def clientBoot(host,port):
    
    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    # host = sys.argv[1] # 这里是读取用户输入的host，可以搜一下这个https://www.cnblogs.com/aland-1415/p/6613449.html
    # sock.connect((host,port))
    sock.connect((host,port))
    # 问候服务器
    username = greeting(sock)
    # register(sock)
    # userDel('jack',sock)
    # login('Lucy',sock)
    # logout('test',sock)
    login(username,sock)
    



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='UDP based RGchat') # 创建ArgumentParser 对象
    parser.add_argument('host',help='interface the server listens at')
    parser.add_argument('-p',metavar='PORT',type=int,default=1060,help='UDP server port(default 1060)')
    args = parser.parse_args()
    clientBoot(args.host,args.p)