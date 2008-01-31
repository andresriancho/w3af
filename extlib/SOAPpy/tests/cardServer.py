#!/usr/bin/env python

# Copyright (c) 2001 actzero, inc. All rights reserved.

import string
import sys

sys.path.insert (1, '..')

from SOAPpy import *

ident = '$Id: cardServer.py,v 1.4 2004/02/18 21:22:13 warnes Exp $'

# create the list of all cards, and keep strings for each suit
__cs = "Clubs"
__ds = "Diamonds"
__hs = "Hearts"
__ss = "Spades"
__cards = []
for suit in [__cs, __ds, __hs, __ss]:
    for num in range(9):
        num += 1
        __cards.append(str(num+1)+" of "+suit)
    for face in ["ace","King","Queen","Jack"]:
        __cards.append(face+" of "+suit)


def deal(num):
    if num not in range(1,53):
        return -1
    else:
        alreadydealt = []
        ignore = 0
        handdealt = []
        import whrandom
        while num > 0:
            idx = int(str(whrandom.random())[2:4])
            if idx in range(52) and idx not in alreadydealt:
                handdealt.append(__cards[idx])
                alreadydealt.append(idx)
                num -= 1
            else:
                ignore += 1
                continue
        return handdealt

def arrangeHand(hand):
    c = []
    d = []
    h = []
    s = []
    import string
    for card in hand:
        if string.find(card, __cs) != -1:
            c.append(card)
        elif string.find(card, __ds) != -1:
            d.append(card)
        elif string.find(card, __hs) != -1:
            h.append(card)
        elif string.find(card, __ss) != -1:
            s.append(card)
    for cards, str in ((c, __cs),(d, __ds),(h,__hs), (s,__ss)):
        cards.sort()
        idx = 0
        if "10 of "+str in cards:
            cards.remove("10 of "+str)
            if "Jack of "+str in cards: idx += 1
            if "Queen of "+str in cards: idx += 1
            if "King of "+str in cards: idx += 1
            if "ace of "+str in cards: idx +=1
            cards.insert(len(cards)-idx,"10 of "+str)
        if "King of "+str in cards:
            cards.remove("King of "+str)
            if "ace of "+str in cards: cards.insert(len(cards)-1,"King of "+str)
            else: cards.append("King of "+str)
    return c+d+h+s

def dealHand (NumberOfCards, StringSeparator):
    hand = deal(NumberOfCards)
    return string.join(hand,StringSeparator)


def dealArrangedHand (NumberOfCards, StringSeparator):
    if NumberOfCards < 1 or NumberOfCards > 52:
        raise ValueError, "NumberOfCards must be between 1 and 52"
    unarranged = deal(NumberOfCards)
    hand = arrangeHand(unarranged)
    return string.join(hand, StringSeparator)

def dealCard ():
    return deal(1)[0]

run = 1

def quit():
    global run
    run=0;

namespace = 'http://soapinterop.org/'

server = SOAPServer (("localhost", 12027))

server.registerKWFunction (dealHand, namespace)
server.registerKWFunction (dealArrangedHand, namespace)
server.registerKWFunction (dealCard, namespace)
server.registerKWFunction (quit, namespace)

try:
    while run:
        server.handle_request()
except KeyboardInterrupt:
    pass
