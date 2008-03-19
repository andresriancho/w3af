#!/usr/bin/env python
######################################################################
#
#   Module:  pyRijnadel
#   Version: $Id: pyRijndael.py,v 1.3 2003/09/03 16:33:04 jsc Exp $
#   Author:  Jeffrey Clement <jclement@bluesine.com>
#   Targets: Win32, Unix
#   Web:     http://jclement.ca/software/pyrijndael/
#
# A pure-python implementation of the AES Rijndael Block Cipher.
# Basic on Phil Fresle's VB implementation.  Notice: this has not
# been verified to correctly implement the Rijndael cipher.  You
# may want to test it yourself before using in a hostile environment.
#
# -------------------------------------------------------------------
#
# $Log: pyRijndael.py,v $
# Revision 1.3  2003/09/03 16:33:04  jsc
# Fixed up licensing
#
# Revision 1.2  2003/09/03 16:16:49  jsc
# Fixed bug for 2.4+ versions of Python where 0x80000000 used to return
# -21..... but will return 21....
#
#
# -------------------------------------------------------------------
#
# Copyright (c) 2003, Jeffrey Clement All rights reserved. 
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions 
# are met: 
#
# * Redistributions of source code must retain the above copyright notice, 
#   this list of conditions and the following disclaimer. 
# * Redistributions in binary form must reproduce the above copyright 
#   notice, this list of conditions and the following disclaimer in the 
#   documentation and/or other materials provided with the distribution. 
# * Neither the name of the Bluesine nor the names of its contributors 
#   may be used to endorse or promote products derived from this software 
#   without specific prior written permission. 
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS 
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED 
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR 
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, 
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, 
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR 
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING 
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS 
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##########################################################################

import math
import string
from operator import *

# 2003/09/03 - Fix for Python2.4+
minInt = -2147483648

# LUTs for Performance
lutLOnBits=[]
lutL2Power=[]
lutBOnBits=[]
lutB2Power=[]

lutInCo=[]
lutRCO=[0] * 30

lutPTab=[0] * 256
lutLTab=[0] * 256
lutFBSub=[0] * 256
lutRBSub=[0] * 256
lutFTable=[0] * 256
lutRTable=[0] * 256

def buildLUTs():
    """
    Populate lookup tables with some frequently used values
    """

    def sumArray(arr):
        """
        return sum of array
        """
        sum=0
        for e in arr:
            sum=sum+e
        return sum
    
    lutInCo.append(0xB)
    lutInCo.append(0xD)
    lutInCo.append(0x9)
    lutInCo.append(0xE)
    
    for i in range(8):
        lutB2Power.append(int(math.pow(2,i)))
        lutBOnBits.append(sumArray(lutB2Power))
        
    for i in range(31):
        lutL2Power.append(int(math.pow(2,i)))
        lutLOnBits.append(sumArray(lutL2Power))

def LShiftL(lValue, iShiftBits):
    """
    LShift does a n-bit left shift on a long(lValue)
    """
    if iShiftBits == 0:
        return lValue
    elif iShiftBits == 31:
        if lValue & 1:
            return minInt
        else:
            return 0
    elif iShiftBits < 0 or iShiftBits > 31:
        raise "iShiftBits not in specified range!"

    if (lValue & lutL2Power[31-iShiftBits]):
        return ((lValue & lutLOnBits[31 - (iShiftBits+1)]) * lutL2Power[iShiftBits]) | minInt
    else:
        return ((lValue & lutLOnBits[31 - (iShiftBits)]) * lutL2Power[iShiftBits]) 

def RShiftL(lValue, iShiftBits):
    """
    RShift does a n-bit right shift on a long(lValue)
    """
    if iShiftBits == 0:
        return lValue
    elif iShiftBits == 31:
        if lValue & minInt:
            return 1
        else:
            return 0
    elif iShiftBits < 0 or iShiftBits > 31:
        raise "iShiftBits not in specified range!"

    tmp = (lValue & 0x7FFFFFFE) / lutL2Power[iShiftBits]

    if (lValue & minInt):
        return (tmp | (0x40000000 / lutL2Power[iShiftBits-1]))
    else:
        return tmp

def LShiftB(bValue, iShiftBits):
    """
    LShift does a n-bit left shift on a byte(bValue)
    """
    if iShiftBits == 0:
        return bValue
    elif iShiftBits == 7:
        if bValue & 1:
            return 0x80
        else:
            return 0
    elif iShiftBits < 0 or iShiftBits > 7:
        raise "iShiftBits not in specified range!"
    return ((bValue & lutBOnBits[7-iShiftBits]) * lutB2Power[iShiftBits])

def RShiftB(bValue, iShiftBits):
    """
    RShift does a n-bit right shift on a byte(bValue)
    """
    if iShiftBits == 0:
        return bValue
    elif iShiftBits == 7:
        if bValue & 0x80:
            return 1
        else:
            return 0
    elif iShiftBits < 0 or iShiftBits > 7:
        raise "iShiftBits not in specified range!"
    return bValue / lutB2Power[iShiftBits]

def RotateLeftL(lValue, iShiftBits):
    return LShiftL(lValue, iShiftBits) | RShiftL(lValue, (32-iShiftBits))

def RotateLeftB(bValue, iShiftBits):
    return LShiftB(bValue, iShiftBits) | RShiftB(bValue, (8-iShiftBits))

def Pack(b, k=0):
    tmp=0
    for i in range(4):
        tmp = tmp | LShiftL(b[i+k], i*8)
    return tmp

def Unpack(a, b, k=0):
    b[0+k] = a & lutLOnBits[7]
    b[1+k] = RShiftL(a,8) & lutLOnBits[7]
    b[2+k] = RShiftL(a,16) & lutLOnBits[7]
    b[3+k] = RShiftL(a,24) & lutLOnBits[7]

def xtime(a):
    b=0
    if (a & 0x80):
        b=0x1B
    else:
        b=0
    return xor(LShiftB(a,1), b)

def bmul(x, y):
    if x!=0 and y!=0:
        return lutPTab[mod(long(lutLTab[x]) + long(lutLTab[y]), 255)]
    else:
        return 0

def SubByte(a):
    b=[0] * 4
    Unpack (a,b)
    for i in range(4):
        b[i] = lutFBSub[b[i]]
    return Pack(b)

def product(x,y):
    xb=[0]*4
    yb=[0]*4
    Unpack (x, xb)
    Unpack (y, yb)
    return xor(bmul(xb[0], yb[0]),xor(bmul(xb[1], yb[1]),xor(bmul(xb[2], yb[2]),bmul(xb[3], yb[3]))))

def InvMixCol(x):
    y=0
    m=0
    b=[0]*4
    m=Pack(lutInCo)
    b[3]=product(m,x)
    m = RotateLeftL(m, 24)
    b[2]=product(m,x)
    m = RotateLeftL(m, 24)
    b[1]=product(m,x)
    m = RotateLeftL(m, 24)
    b[0]=product(m,x)
    m = RotateLeftL(m, 24)
    y = Pack(b)
    return y

def ByteSub(x):
    y = lutPTab[255 - lutLTab[x]]
    x=y
    x = RotateLeftB(x,1)
    y=xor(y,x)
    x = RotateLeftB(x,1)
    y=xor(y,x)
    x = RotateLeftB(x,1)
    y=xor(y,x)
    x = RotateLeftB(x,1)
    y=xor(y,x)
    return xor(y,0x63)

def genTables():
    """
    Generate a bunch of lookup tables needed
    """

    lutLTab[0]=0
    lutPTab[0]=1
    lutLTab[1]=0
    lutPTab[1]=3
    lutLTab[3]=1

    for i in range(2,256):
        lutPTab[i] = xor(lutPTab[i-1], xtime(lutPTab[i-1]))
        lutLTab[lutPTab[i]]=i

    lutFBSub[0]=0x63
    lutRBSub[0x63]=0

    for i in range(1,256):
        y = ByteSub(i)
        lutFBSub[i]=y
        lutRBSub[y]=i

    y=1
    for i in range(0,30):
        lutRCO[i]=y
        y=xtime(y)

    b=[0]*4
    y=0
    for i in range(0,256):
        y=lutFBSub[i]
        b[3] = xor(y, xtime(y))
        b[2] = y
        b[1] = y
        b[0] = xtime(y)
        lutFTable[i] = Pack(b)

        y=lutRBSub[i]
        b[3]=bmul(lutInCo[0],y)
        b[2]=bmul(lutInCo[1],y)
        b[1]=bmul(lutInCo[2],y)
        b[0]=bmul(lutInCo[3],y)
        lutRTable[i] = Pack(b)

class pyRijndael:

    def __init__(self):
        self.Nb=0
        self.Nk=0
        self.Nr=0
        self.fi=[0]*24
        self.ri=[0]*24
        self.fkey=[0]*120
        self.rkey=[0]*120

    def gkey(self, nb, nk, key):
        i=0
        j=0
        k=0
        m=0
        N=0
        C1=0
        C2=0
        C3=0
        CipherKey=[0] * 8
        
        self.Nb=nb
        self.Nk=nk

        if self.Nb >= self.Nk:
            self.Nr = 6 + self.Nb
        else:
            self.Nr = 6 + self.Nk

        C1=1
        if self.Nb < 8:
            C2=2
            C3=3
        else:
            C2=3
            C3=4

        for j in range(0,nb):
            m = j * 3
            self.fi[m+0] = mod(j+C1,nb)
            self.fi[m+1] = mod(j+C2,nb)
            self.fi[m+2] = mod(j+C3,nb)
            self.ri[m+0] = mod(nb+j-C1, nb)
            self.ri[m+1] = mod(nb+j-C2, nb)
            self.ri[m+2] = mod(nb+j-C3, nb)

        N = self.Nb * (self.Nr+1)

        for i in range(self.Nk):
            CipherKey[i]=Pack(key,i*4)

        for i in range(self.Nk):
            self.fkey[i]=CipherKey[i]

        j = self.Nk
        k = 0
       
        while j < N:
            self.fkey[j] = xor(xor(self.fkey[j-self.Nk],SubByte(RotateLeftL(self.fkey[j-1],24))),lutRCO[k])
            if self.Nk <= 6:
                i=1
                while i < self.Nk and (i+j) < N:
                    self.fkey[i+j] = xor(self.fkey[i+j-self.Nk], self.fkey[i+j-1])
                    i = i + 1
            else:
                i=1
                while i < 4 and (i+j) < N:
                    self.fkey[i+j] = xor(self.fkey[i+j-self.Nk], self.fkey[i+j-1])
                    i = i + 1
                if j + 4 < N:
                    self.fkey[j+4]= xor(self.fkey[j+4-self.Nk], SubByte(self.fkey[j+3]))
                i=5
                while i < self.Nk and (i+j) < N:
                    self.fkey[i+j] = xor(self.fkey[i+j-self.Nk], self.fkey[i+j-1])
                    i=i+1
            j=j+self.Nk
            k=k+1

        for j in range(self.Nb):
            self.rkey[j+N-nb]=self.fkey[j]

        i=self.Nb

        while i < N - self.Nb:
            k=N-self.Nb-i   
            for j in range(self.Nb):
                self.rkey[k+j]=InvMixCol(self.fkey[i+j])
            i=i+self.Nb

        j=N-self.Nb
        while j < N:
            self.rkey[j-N+self.Nb] = self.fkey[j]
            j=j+1

    def Encrypt(self,buff):
        a=[0]*8
        b=[0]*8
        tmp=[]
        for element in buff:
            tmp.append(element)
        for i in range(self.Nb):
            j=i*4
            a[i]=Pack(tmp,j)
            a[i]=xor(a[i], self.fkey[i])
        k=self.Nb
        x=a
        y=b
       
        for i in range(1,self.Nr):
            for j in range(self.Nb):
                m=j*3
                y[j] = xor(self.fkey[k],
                            xor(lutFTable[x[j] & lutLOnBits[7]],
                                xor(RotateLeftL(lutFTable[RShiftL(x[self.fi[m]], 8)& lutLOnBits[7]], 8),
                                    xor(RotateLeftL(lutFTable[RShiftL(x[self.fi[m + 1]], 16) & lutLOnBits[7]], 16),
                                        RotateLeftL(lutFTable[RShiftL(x[self.fi[m + 2]], 24) & lutLOnBits[7]], 24)))))
                k = k + 1
            t = x
            x = y
            y = t
        
        for j in range(self.Nb):
            m=j*3
            y[j] = xor(self.fkey[k],
                       xor(lutFBSub[x[j] & lutLOnBits[7]],
                           xor(RotateLeftL(lutFBSub[RShiftL(x[self.fi[m]], 8) & lutLOnBits[7]], 8),
                               xor(RotateLeftL(lutFBSub[RShiftL(x[self.fi[m + 1]], 16) & lutLOnBits[7]], 16),
                                   RotateLeftL(lutFBSub[RShiftL(x[self.fi[m + 2]], 24) & lutLOnBits[7]], 24)))))
            k=k+1

        for i in range(self.Nb):
            j=i*4
            Unpack (y[i], tmp, j)
            x[i]=0
            y[i]=0

        return tmp
    
    def Decrypt(self,buff):
        a=[0]*8
        b=[0]*8
        tmp=[]
        for element in buff:
            tmp.append(element)

        for i in range(self.Nb):
            a[i] = Pack(tmp, i*4)
            a[i]=xor(a[i], self.rkey[i])

        k=self.Nb
        x=a
        y=b

        for i in range(1,self.Nr):
            for j in range(self.Nb):
                m=j*3
                y[j]=xor(xor(xor(xor(self.rkey[k],lutRTable[x[j] & lutLOnBits[7]]),
                         RotateLeftL(lutRTable[RShiftL(x[self.ri[m]],8) & lutLOnBits[7]], 8)),
                         RotateLeftL(lutRTable[RShiftL(x[self.ri[m+1]],16) & lutLOnBits[7]], 16)),
                         RotateLeftL(lutRTable[RShiftL(x[self.ri[m+2]],24) & lutLOnBits[7]], 24))
                
                k = k + 1
            t=x
            x=y
            y=t

        for j in range(self.Nb):
            m=j*3
            y[j]=xor(xor(xor(xor(self.rkey[k],lutRBSub[x[j] & lutLOnBits[7]]),
                     RotateLeftL(lutRBSub[RShiftL(x[self.ri[m]],8) & lutLOnBits[7]], 8)),
                     RotateLeftL(lutRBSub[RShiftL(x[self.ri[m+1]],16) & lutLOnBits[7]], 16)),
                     RotateLeftL(lutRBSub[RShiftL(x[self.ri[m+2]],24) & lutLOnBits[7]], 24))
            k = k + 1
    
        for i in range(self.Nb):
            j=i*4
            Unpack(y[i],tmp,j)
            x[i]=0
            y[i]=0        
        
        return tmp

    def strToByteArray(self, str):
        b=[]
        for ch in str:
            b.append(ord(ch))
        return b

    def byteArrayToStr(self,b):
        s=""
        for nm in b:
            s=s+chr(nm)
        return s

    def padArray(self,arr, sz):
        na=[0]*sz
        for i in range(len(arr)):
            if i>sz: break
            na[i]=arr[i]
        return na

    def padModulus(self, arr):
        tmp=arr
        if ((len(arr) % 32) != 0):
            for i in range(32-len(arr) % 32):
                tmp.append(0)
        return tmp

def EncryptData(key, data):
    """
    Usage: EncryptData(key, data)
        key(string): password for encryption
        data(string): data for encryption

    Encrypts data using key and returns encrypted string.  Uses 256 bit Rijndael
    cipher.  Key is built from first 32 characters of password.  A 32-bit message
    length is attached to beginning of ciphertext.
    """
    # add 32 bit number for length
    r=pyRijndael()
    r.gkey(8,8,r.padArray(r.strToByteArray(key),32))
    sz=[0]*4
    Unpack(len(data),sz)
    din=r.padModulus(sz+r.strToByteArray(data))
    dout=[]
    while len(din)>0: # operate on 32bit blocks
        dout=dout+r.Encrypt(din[0:32])
        din=din[32:]
    return r.byteArrayToStr(dout)

def DecryptData(key, data):
    """
    Usage: DecryptData(key, data)
        key(string): password for decryption
        data(string): data for decryption
    """
    r=pyRijndael()
    r.gkey(8,8,r.padArray(r.strToByteArray(key),32))
    din=r.strToByteArray(data)
    dout=[]
    while len(din)>0:  # operate on 32-bit blocks
        dout=dout+r.Decrypt(din[:32])
        din=din[32:]
    sz=Pack(dout)      # extract size information
    dout=dout[4:4+sz]   # remove size data
    return r.byteArrayToStr(dout)
        
buildLUTs()
genTables()

if __name__=='__main__':
    print "Copyright (C) 2003 Jeffrey Clement"
    print "This is free software; see the source for copying conditions.  There is NO"
    print "warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE."
    print "\n\n== TEST RUN =="
    PlainText="Hello World" *50
    Key="Secret"
    CipherText=EncryptData(Key,PlainText)
    PlainText2=DecryptData(Key,CipherText)
    print "PT :",PlainText
    print "KY :",Key
    print "PT2:",PlainText2
