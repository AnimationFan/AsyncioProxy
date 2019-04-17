
#第一次握手
#第二次握手
#第三次握手
#与服务端建立通信
    #发送目标域名、端口
    #接收确认消息
    #第四次握手
    #循环
        #接收，并转发请求
        #接收，并转发响应

import asyncio
import struct
import socket

async def handler(reader,writer):
    #第一次请求
    local=writer.get_extra_info("sockname")
    bdhost = socket.inet_aton(local[0])
    bdport = struct.pack(">H", local[1])
    print(local,bdhost,bdport)
    #bdhost，byte型的ip地址，bdport，byte型的端口地址
    #?????



    data=await reader.read(257)
    print("第一次请求",data)
    data=data[2:]
    try:
        data.index(b'\x00')
    except Exception as err:
        print("只支持\x00访问")
        return
    #第一次响应
    writer.write(b'\x05\x00')
    #读取第二次请求
    bdata=await reader.read(4)
    bVer=bdata[0:1]
    bCmd=bdata[1:2]
    bRsv=bdata[2:3]
    bAtype=bdata[3:4]
    print(bdata,bVer,bCmd,bRsv,bAtype)


    #解析目标得到byte型的目标ip序列、byte型读的那口地址
    sHostIP=''
    iHostPort=''

    if(bVer!=b'\x05'):
        print("版本不支持")
        return
    if(bCmd!=b'\x01'):
        print("请求类型不为connect")
        return

    #获取ip
    if(bAtype==b'\x01'):#ipv4型地址
        print("地址类型为ipv4")
        bHostIP=await reader.read(4)
        sHostIP=bHostIP.decode()
    if(bAtype==b'\x03'):
        #读地址长度
        print("地址类型为域名")
        bLength=await reader.read(1)
        iLength=int.from_bytes(bLength,byteorder='big',signed=False)
        print("bLength",bLength,"iLength",iLength)
        #读域名
        bHostName=await reader.read(iLength)
        print(bHostName)
        sHostName=bHostName.decode()
        sHostIP=socket.gethostbyname(sHostName)
        print("str型Ip",sHostIP)
    if(bAtype==b'\x04'):
        bHostIP=await reader.read(16)
        sHostIP=bHostIP.decode()
    #获取端口
    bHostPort = await reader.read(2)
    height,low=struct.unpack("BB",bHostPort)
    iHostPort=height*256+low



    try:
        #开启与远端连接
        Rreader, Rwriter = await asyncio.open_connection(sHostIP,iHostPort)



        print("目标ip", sHostIP, "目标端口", iHostPort)
        #消息返回
        writer.write(b"\x05\x00\x00\x01"+bdhost+bdport)
        await writer.drain()
        while True:
            data=await reader.read(100)
            if(data!=b''):
                print(data)
                Rwriter.write(data)
                if(data.__len__()<100):
                    break;
            else:
                break
        print("请求结束")
        data=b''
      #  response=b''
        while True:
            data=await Rreader.readline()
            print(data)
            if(data!=b''):
                writer.write(data)
                await writer.drain()
                #response=response+data
            else:
                break;
        writer.close()
        Rwriter.close()
        print("响应结束")

    except Exception as err:
        print("发生错误",err)
        writer.close()





async def main():
    server=await asyncio.start_server(handler,'127.0.0.1',8888)
    async with server:
        await server.serve_forever()

asyncio.run(main())
