# -*- coding: utf-8 -*-

import multiprocessing as mp
import pygame as pg
import numpy as np
import pandas as pd
import filterlib as flt
import blink as blk
#from pyOpenBCI import OpenBCIGanglion

pg.init()

def blinks_detector(quit_program, blink_det, blinks_num, blink,):
    def detect_blinks(sample):
        if SYMULACJA_SYGNALU:
            smp_flted = sample
        else:
            smp = sample.channels_data[0]
            smp_flted = frt.filterIIR(smp, 0)
        #print(smp_flted)

        brt.blink_detect(smp_flted, -38000)
        if brt.new_blink:
            if brt.blinks_num == 1:
                #connected.set()
                print('CONNECTED. Speller starts detecting blinks.')
            else:
                blink_det.put(brt.blinks_num)
                blinks_num.value = brt.blinks_num
                blink.value = 1

        if quit_program.is_set():
            if not SYMULACJA_SYGNALU:
                print('Disconnect signal sent...')
                board.stop_stream()
                
                
####################################################
    SYMULACJA_SYGNALU = True
####################################################
    mac_adress = 'd2:b4:11:81:48:ad'
####################################################

    clock = pg.time.Clock()
    frt = flt.FltRealTime()
    brt = blk.BlinkRealTime()

    if SYMULACJA_SYGNALU:
        df = pd.read_csv('dane_do_symulacji/data.csv')
        for sample in df['signal']:
            if quit_program.is_set():
                break
            detect_blinks(sample)
            clock.tick(200)
        print('KONIEC SYGNAŁU')
        quit_program.set()
    else:
        board = OpenBCIGanglion(mac=mac_adress)
        board.start_stream(detect_blinks)


blink_det = mp.Queue()
blink = mp.Value('i', 0)
blinks_num = mp.Value('i', 0)
#connected = mp.Event()
quit_program = mp.Event()

proc_blink_det = mp.Process(
    name='proc_',
    target=blinks_detector,
    args=(quit_program, blink_det, blinks_num, blink,)
    )

# rozpoczęcie podprocesu
proc_blink_det.start()
print('subprocess started')

############################################
# Poniżej należy dodać rozwinięcie programu
############################################

import random
import time

screen = pg.display.set_mode((720, 480))
done = False
clock = pg.time.Clock()

def managebeats(container, tetno, fps=60):
    if container[0].x<-60:
        container.pop(0)
    if container[-1].x<720-(tetno*fps/180):
        container.append(Beat())

class Beat(object):
    
    def __init__(self):
        self.y = 240
        self.x = 800

    def move(self, tetno, fps=60):
        self.x -= tetno/fps*5

    def get_obj(self):
        return pg.Rect(self.x, self.y, 60, 60)

beats = [Beat()]
tetno = 20

while not done:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            done = True
            quit_program.set()
                

    if blink.value == 1:
        print('BLINK!')
        blink.value = 0
    screen.fill((0, 0, 0))

    managebeats(beats, tetno)
    for i in beats:
        i.move(tetno)
        pg.draw.rect(screen, (0, 128, 255), i.get_obj())

    pg.display.flip()
    if pg.key.get_pressed()[pg.K_UP]:
        tetno += 10
        print(tetno)
    if pg.key.get_pressed()[pg.K_DOWN]:
        tetno -= 10
        print(tetno)

    clock.tick(60)


# Zakończenie podprocesów
    proc_blink_det.join()
