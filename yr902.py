import threading
from textwrap import wrap
import serial

import cmd

class Yr903:
    enabled = False

    def __init__(self,serialObj,dataHandler):
        self.serial = serialObj
        self.dataHandler = dataHandler
        self.readerAddr = 1
        self.channel = 1

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.serial.close()

    def cancel(self):
        self.enabled = False

    def requestRealTimeTags(self):
        #set inventory reading mode
        self.serial.write(cmd.createRealTimeInventoryPacket(self.readerAddr, self.channel))

    def processRealtimeDataPacket(self,pktLen,pkt):
        # if len == 10 (0x0A) and reading data == 0x89: request reading new tags
        if (pktLen == 0x0A and pkt[1] == 0x89):
            self.requestRealTimeTags()
            print('new request!!!')
        else:
            # pass the data to print data function 
            print('print data:')
            self.dataHandler(pkt)


    def startRealtimeMode(self):
        self.enabled = True
        self.requestRealTimeTags()
        while(self.enabled):
            #read two bytes
            msg = self.serial.read(2)
            # \xa0\x13 0x13 --> 19 length
            # \xa0\n no length no data
            # check the head 0xA0
            if (len(msg)>1 and msg[0] == 0xA0):
                pktLen = msg[1]
                #19
                #10
                # read data with pktLen 
                pkt = self.serial.read(pktLen)
                self.processRealtimeDataPacket(pktLen, pkt)


if __name__ == "__main__":
    serial = serial.Serial(port='/dev/ttyUSB1', bytesize=8, stopbits=1, timeout=0.05)
    serial.baudrate = 115200

    tagCount = 0
    def printData(byteData):
        print('EPC data: ' + ' '.join(wrap(byteData.hex()[:-4],2)))
        # \x01\x89h0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00)\x86b\x1a
        global tagCount
        tagCount += 1

    with Yr903(serial, printData) as Y:
        threading.Timer(3,Y.cancel).start()
        Y.startRealtimeMode()

    print("Total Tags Scanned: ",tagCount)