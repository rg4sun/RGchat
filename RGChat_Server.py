import mysql.connector as dbConnector
import getpass # 用于隐藏屏幕输入回显
import argparse, socket, sys
import threading
import json


# 设置状态码字典，服务器根据客户端发送的状态码进行响应，
# 为了能使得服务器能区分客户端的不同请求，客户端每次发消息前必须发送一个状态码
# 然后服务器根据状态码来决定采用什么功能响应
statusMark = {'greet':'0', 'login':'1', 'register':'2', 'logout':'3', 'userDel':'4'} 
MAX_BYTES = 65535

# userinfo ={'id':None,'name':None,'pwd':None,'host':None,'status':None} # id字段用于记录用户序号，用于检索userDate
# userData = [{'id':0,'name':'RGroot','pwd':'Rg123','host':None}] # 预先存入一个root用户，事实上是为了普通用户id从1计数
# 保存用户数据，之后把这个改成数据库或者导出txt

# 链接数据库
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

def handleGreeting(sock,addr):
    data, addr = sock.recvfrom(MAX_BYTES)
    print('Client:{} => {}'.format(addr,data.decode()))
    sock.sendto('> Conected to RGchat Server <'.encode(),addr)

def info_tuple2List(infoTuple): # 数据库查询返回的一条记录是元组，为了方便后续编程，设计此函数
     return {'id':infoTuple[0],'name':infoTuple[1],'pwd':infoTuple[2],'host':infoTuple[3],'status':infoTuple[4]}

def mainFrame(userinfo):
    print('welcome {} at {} , status: {}'.format(userinfo['name'],userinfo['host'],userinfo['status']))

def handleRegister(sock,addr):
    # print('=========================================')
    # print('请进行注册！')

    dbCursor.execute('SELECT name FROM userdata')
    # userNameTuple = dbCursor.fetchall() # 这样返回的是[('RGroot',),('test',)]
    userNameTuple = [ t[0] for t in dbCursor.fetchall()] # 数据大了这里效率会非常低
    userNameTuple = json.dumps(userNameTuple) # 由于服务器只能传送str, 将查询得到的tuple用json转成字符串
    # dumps会把list、tuple类型转成json的array，array用loads会恢复成list
    sock.sendto(userNameTuple.encode(),addr)

    # while(1): # 判断用户名是否被注册过，更好的办法是设计数据库的时候name字段不能重，以后再优化了
    #     username = input('Username: ')
    #     if username in userNameTuple:
    #         print('用户名已被注册，请尝试更换！')
    #     else:
    #         break
    # userPwd = getpass.getpass('Password: ')
    # pwdCheck = getpass.getpass("Password Check: ")
    # while(userPwd != pwdCheck): # 密码验证
    #     print('Check不通过，两次输入的密码不一致，请重新设置密码！')
    #     userPwd = getpass.getpass('Password: ')
    #     pwdCheck = getpass.getpass("Password Check: ")


    # 新人入库
    insertData, addr = sock.recvfrom(MAX_BYTES)
    print(insertData)
    sql = 'INSERT INTO userdata (name,pwd) VALUES (%s,%s)' # id自增，stauts、host设置了默认初始值0、NULL
    insertData = tuple(json.loads(insertData.decode())) # 要转成tuple
    dbCursor.execute(sql,insertData) # 执行sql语句
    mydb.commit() # 数据表内容有更新，必须使用到该语句
    # 不知道commit有没有更新成功的返回值，有的话可以写一个regFlag
    sock.sendto('1'.encode(),addr)

    # print('注册成功！')
    # print('=========================================')
    # return username

def handleUserDel(sock,addr): # 一般这个模块是用户登录之后才出现，所以删除用户的时候不用查用户是否存在
    # print('=========================================')
    # print('敏感操作：正在删除账户 {} ...'.format(username))
    # username = sock.recvfrom(MAX_BYTES)# 从客户端接收要删除的username, 要时刻注意recvform返回的是 data-str，addr-tuple
    # username = username.decode
    username = sock.recv(MAX_BYTES).decode()
    # 拉取对应于该user的pwd
    sql = 'SELECT pwd FROM userdata WHERE name="{}" '.format(username)
    dbCursor.execute(sql)
    # pwd = dbCursor.fetchall()[0][0] # fetchall 结果应该是[(pwd,)]
    pwd = dbCursor.fetchone()[0] # fetchone 结果应该是 (pwd,)
    sock.sendto(pwd.encode(),addr) # 将密码发送给客户端用于验证，后续优化这里要加密
    # pwdFlag = sock.recvfrom(MAX_BYTES) #  要时刻注意recvform返回的是 data-str，addr-tuple
    # pwdFlag = pwdFlag.decode()
    pwdFlag = sock.recv(MAX_BYTES).decode()
    if pwdFlag == '0':
        return
    elif pwdFlag == '1':
        sql = 'DELETE FROM userdata WHERE name="{}" '.format(username)
        dbCursor.execute(sql)
        mydb.commit() # 只要数据表有变动就要commit
        return

    
def login(username,sock): # host没写

    print('=========================================')
    print('尊敬的{}, 欢迎使用RGchat！，请登录：'.format(username))
    

    dbCursor.execute('SELECT name FROM userdata')
    userNameTuple = [ t[0] for t in dbCursor.fetchall()] # 数据大了这里效率会非常低

    if username not in userNameTuple:
        print('账号{}不存在！请注册：'.format(username))
        login(register()) # 注册完了重新login
        # mainFrame(userinfo) 
    else:
        sql = 'SELECT pwd FROM userdata WHERE name= "{}" '.format(username)
        dbCursor.execute(sql)
        pwd = dbCursor.fetchone()[0]
        errPwdCount=0
        userPwd = getpass.getpass('Password: ')
        while(userPwd != pwd):
            errPwdCount+=1
            userinfo['pwd']=getpass.getpass('错误的密码，还可以尝试{}次：'.format(5-errPwdCount))
            if errPwdCount>4:
                print('您已经输错5次密码，系统将自动退出！')
                return 
        # 登录后将该用户状态设置为1表示在线
        sql = 'UPDATE userdata SET status={} WHERE name="{}" '.format(1,username) 
        dbCursor.execute(sql)
        mydb.commit()
        # 抽取用户信息，因为mainFrame需要获得用户所有信息
        sql = 'SELECT * FROM userdata WHERE name="{}" '.format(username)
        dbCursor.execute(sql)
        infoTuple = dbCursor.fetchone()
        userinfo = info_tuple2List(infoTuple) 
        print('=========================================')
        mainFrame(userinfo)

def logout(username,sock): # 没写完，要等进入mainframe写完之后调用break
    # 注销后将该用户状态设置为0表示离线，同时清空host
    sql = 'UPDATE userdata SET status={},host=Null WHERE name="{}" '.format(0,username)
    dbCursor.execute(sql)
    mydb.commit()
    print('Goodbye~ {} '.format(username))
    pass

def privChat(pair):
    pass
def groupChat(grp):
    pass
def pubChar():
    pass

def serverBoot(interface,port):
    
    # host = '127.0.0.1'
    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sock.bind((interface,port))
    print('Sever listen at {}'.format(sock.getsockname()))

    while True:
        status, addr = sock.recvfrom(MAX_BYTES)
        if status.decode() == statusMark['greet']:
            handleGreeting(sock,addr)
            # break # 测试用
            continue
        elif status.decode() == statusMark['login']:
            pass
            # handleLogin(sock,addr)
        elif status.decode() == statusMark['register']:
            handleRegister(sock,addr)
            # break # 测试用
            continue
        elif status.decode() == statusMark['userDel']:
            handleUserDel(sock,addr)
            break # 测试用
            # continue
        
    

        

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='UDP based RGchat') # 创建ArgumentParser 对象
    parser.add_argument('host', metavar='HOST', type=str, default='127.0.0.1', help='interface the server listens at(default 127.0.0.1)')
    parser.add_argument('-p',metavar='PORT',type=int,default=1060,help='UDP server port(default 1060)')
    args = parser.parse_args()
    serverBoot(args.host,args.p)
    # serverBoot('127.0.0.1',1060)
    # print(sys.argv[2])
    
