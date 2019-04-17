import asyncio
import struct
#获取域名
#获取端口
    #建立连接
    #返回确认消息
    #接收反馈转发
    #

#删除报头读取请求
async def delHeadInfo(reader):
    Request=b''
    while True:
        data=await reader.readline()
        if(data==b'\r\n'):
            break
    data=b''
    while True:
        data=await reader.read(100)
        if(data!=b''):
            Request+=data
            if(data.__len__()<100):
                break;
        else:
            break;
    return Request

#加报头响应
async def addHead(writer,message):
    Response = b'HTTP/1.1 200 OK\r\n' + \
               b'Connection: Keep-Alive\r\n' + \
               b'Content-Encoding: gzip\r\n' + \
               b'Content-Type: text/html; charset=utf-8\r\n' + \
               b'Date: Fri, 06 Apr 2018 11:42:46 GMT\r\n' + \
               b'\r\n' + message
    writer.write(Response)
    await writer.drain()


async def handler(reader,writer):
    # 从代理读取目标ip和端口
    PortandIP=await delHeadInfo(reader)
    bHostIP=PortandIP[0:-6]
    bHostPort=PortandIP[-4:-2]
    sHostIP=bHostIP.decode()
    height, low = struct.unpack("BB", bHostPort)
    iHostPort = height * 256 + low

    print("格式化的地址和端口",sHostIP,iHostPort)
    #建立连接
    try:
        Rreader,Rwriter=await asyncio.open_connection(sHostIP,iHostPort)
        #返回连接结果
        await addHead(writer,b'True\r\n')
    except Exception as err:
        await addHead(writer,b'False\r\n')
        writer.close()


    #接收请求
    #取表请求头
    Request=await delHeadInfo(reader)
    #发送给远程
    Rwriter.write(Request)

    #接收响应
    #加报头
    Response=b''
    while True:
        data=await Rreader.read(100)
        if(data!=b''):
            Response+=data;
            if(data.__len__()<100):
                break;
        else:
            break;
    if(Response!=b''):
        await addHead(writer,Response)

    writer.close()
    Rwriter.close()
    return
    #发送给代理
    #结束

async def main():
    # 启动异步io服务端
    server = await asyncio.start_server(
        handler, '127.0.0.1', 3000)


    async with server:
        await server.serve_forever()

asyncio.run(main())
