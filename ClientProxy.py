import asyncio
import struct
import socket


async def getRequest(reader):
    Request=b''
    while True:
        data = await reader.read(100)
        if (data != b''):
            print(data)
            Response=Response+data
            if (data.__len__() < 100):
                break;
        else:
            break
    return Request

async def addHeadSend(Rwriter,message):
    #Get请求不允许附带信息，因此采用Post
    httpHead=b'POST / HTTP/1.1\r\n'+\
             b'Host: www.baidu.com\r\n'+\
             b'Connection: keep-alive\r\n'+\
             b'User-Agent: Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.119 Safari/537.36\r\n'+\
             b'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8\r\n'+\
             b'Accept-Encoding: gzip, deflate, br\r\n'+\
             b'Accept-Language: zh-CN,zh;q=0.9\r\n'+\
             b'\r\n'
    Rwriter.write(httpHead+message)


#获取去报头响应
async def delHeadGet(Rreader):
    Response=b''
    while True:
        data=await Rreader.readline()
        if(data==b'\r\n'):
            break;
    while True:
        data=await Rreader.read(100)
        if(data!=b''):
            Response=Response+data
            if(data.__len__()<100):
                break
        else:
            break
    return Response



async def handler(reader, writer):
    # 第一次请求
    local = writer.get_extra_info("sockname")
    bdhost = socket.inet_aton(local[0])
    bdport = struct.pack(">H", local[1])
    # bdhost，byte型的ip地址，bdport，byte型的端口地址
    # ?????

    data = await reader.read(257)
    print("第一次请求", data)
    data = data[2:]
    try:
        data.index(b'\x00')
    except Exception as err:
        print("只支持\x00访问")
        return
    # 第一次响应
    writer.write(b'\x05\x00')
    # 读取第二次请求
    bdata = await reader.read(4)
    bVer = bdata[0:1]
    bCmd = bdata[1:2]
    bRsv = bdata[2:3]
    bAtype = bdata[3:4]

    # 解析目标得到byte型的目标ip序列、byte型读的那口地址
    sHostIP = ''
    iHostPort = ''

    if (bVer != b'\x05'):
        print("版本不支持")
        return
    if (bCmd != b'\x01'):
        print("请求类型不为connect")
        return

    # 获取ip
    if (bAtype == b'\x01'):  # ipv4型地址
        print("地址类型为ipv4")
        bHostIP = await reader.read(4)
        sHostIP = bHostIP.decode()
    if (bAtype == b'\x03'):
        # 读地址长度
        print("地址类型为域名")
        bLength = await reader.read(1)
        iLength = int.from_bytes(bLength, byteorder='big', signed=False)
        # 读域名
        bHostName = await reader.read(iLength)
        if (bHostName == b'www.google.com.hk' or bHostName==b'accounts.google.com' or bHostName==b'clients1.google.com'):
            writer.close()
            return
        print(bHostName)
        sHostName = bHostName.decode()
        sHostIP = socket.gethostbyname(sHostName)
    if (bAtype == b'\x04'):
        bHostIP = await reader.read(16)
        sHostIP = bHostIP.decode()
    # 获取端口
    bHostPort = await reader.read(2)
    height, low = struct.unpack("BB", bHostPort)
    iHostPort = height * 256 + low


    try:
        # 开启与远端连接
        Rreader, Rwriter = await asyncio.open_connection("127.0.0.1", 3000)
        print("与服务器连接成功")


        # 发送端口信息
        bHostIP=sHostIP.encode(encoding="utf-8")
        print(bHostIP)
        await addHeadSend(Rwriter,bHostIP+b'\r\n'+bHostPort+b'\r\n')
        print("发送连接目标信息")


        #接收确认信息
        Response=await delHeadGet(Rreader)
        #信息为b'True'和b'Flse'
        if(Response!=b'True\r\n'):
            #返回失败数据报
            writer.write(b'\x05\xff\x00\x01123456')
            await writer.drain()
            Rwriter.close()
            writer.close()
            return

        print("目标ip", sHostIP, "目标端口", iHostPort)
        # 消息返回
        writer.write(b"\x05\x00\x00\x01" + bdhost + bdport)
        await writer.drain()


        Request=b''
        data=b''
        while True:
            data=await reader.read(100)
            if(data!=''):
                Request+=data
                if(data.__len__()<100):
                    break;
            else:
                break

        #加报头
        #发送给远端
        await addHeadSend(Rwriter,message=Request)

        #从远端读取数据报
        #删除报头
        Response=await delHeadGet(Rreader)
        print(Response)
        #返回
        writer.write(Response)
        await writer.drain()
        writer.close()
        Rwriter.close()
        return
    except Exception as err:
        print("发生错误", err)
        writer.close()


async def fHandler(reader,writer):
    try:
        await asyncio.wait_for(handler(reader,writer),timeout=4.0)
    except asyncio.TimeoutError:
        print("请求超时")
        return
    return


async def main():
    asyncio.Semaphore(100)#限定并发数

    server = await asyncio.start_server(fHandler, '127.0.0.1', 8888)
    async with server:
        await server.serve_forever()


asyncio.run(main())
