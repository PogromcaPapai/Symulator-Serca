# -*- coding: utf-8 -*-

import multiprocessing as mp
import pygame as pg
import numpy as np
import pandas as pd
import filterlib as flt
import blink as blk
import random
import time
#from pyOpenBCI import OpenBCIGanglion

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

# Text rendering

def text_objects(text, font):
    textSurface = font.render(text, True, (255,255,255))
    return textSurface, textSurface.get_rect()

def message_display(text):
    largeText = pg.font.Font('freesansbold.ttf',60)
    TextSurf, TextRect = text_objects(text, largeText)
    TextRect.center = (45,30)
    screen.blit(TextSurf, TextRect)

# Gamer stuff

def sort_key(obj, win=120):
    return abs(obj.x-win)

def managebeats(container, tetno, fps=60):
    if container[0].x<-60:
        container.pop(0)
    if container[-1].x<720-(tetno*fps/180):
        container.append(Beat(container))

class Beat(object):
    
    def __init__(self, parent):
        self.y = 240
        self.x = 800
        self.parent = parent

    def move(self, tetno, fps=60):
        self.x -= tetno/fps*5

    def get_obj(self):
        return pg.Rect(self.x, self.y, 20, 60)

    def get_points(self, wykrycie = 60, mod=0.1):
        return mod*(wykrycie-abs(self.x - 120))

    def destroy(self, wykrycie = 20):
        if len(self.parent)<=2:
            return self.get_points(wykrycie=wykrycie)
        else:
            self.parent.pop(self.parent.index(self))
            return self.get_points(wykrycie=wykrycie)


if __name__ == "__main__":
    pg.init()
    blink_det = mp.Queue()
    blink = mp.Value('i', 0)
    blinks_num = mp.Value('i', 0)
    connected = mp.Event()
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

    screen = pg.display.set_mode((720, 480))
    done = False
    clock = pg.time.Clock()            

    beats = []
    beats.append(Beat(beats))
    tetno = 20
    points = 100
    cl_time = time.clock()


    while not done:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                done = True
                quit_program.set()
                    

        if (blink.value == 1 or pg.key.get_pressed()[pg.K_SPACE]) and time.clock()-cl_time>0.15:
            cl_time = time.clock()
            print('BLINK!')
            points += int(sorted(beats, key=sort_key)[0].destroy())
            print(points)
            blink.value = 0
        screen.fill((0, 0, 0))

        managebeats(beats, tetno)
        for i in beats:
            i.move(tetno)
            pg.draw.rect(screen, (0, 128, 255), i.get_obj())
        message_display(str(points))
        pg.draw.rect(screen, (255,150,150), pg.Rect(120, 240, 5, 480))

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
