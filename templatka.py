# -*- coding: utf-8 -*-

from psychopy import visual, event, core
import multiprocessing as mp
import pygame as pg
import pandas as pd
import filterlib as flt
import blink as blk
#from pyOpenBCI import OpenBCIGanglion
import time
import random


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

if __name__ == "__main__":


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
    pg.init()

    ############
    DEBUG = False
    ############

# Text rendering

    def text_objects(text, font):
        textSurface = font.render(text, True, (255,255,255))
        return textSurface, textSurface.get_rect()

    def message_display(text, pos):
        largeText = pg.font.Font('freesansbold.ttf',60)
        TextSurf, TextRect = text_objects(text, largeText)
        TextRect.center = pos
        screen.blit(TextSurf, TextRect)

    # Gamer stuff

    def sort_key(obj, win=120):
        return abs(obj.x-win)

    def managebeats(container, tetno, fps=60):
        missed = 0
        if container[0].x<-60:
            container.pop(0)
            missed += 1
        if container[-1].age >= 60*fps/tetno:
            container.append(Beat(container))
        return missed

    def nowyrytm(rytm, szansa=0.005, minimum=50, maximum=100):
        if random.random() <= szansa:
            new = random.randint(minimum, maximum)
            print(f"Nowy rytm: {new}")
            return new
        else: 
            return rytm

    def idz_do_rytmu(aktualny, docelowy, counter, step=0.1):

        if int(aktualny) == docelowy:
            return float(docelowy)
        elif aktualny > docelowy:
            #print(f"{aktualny} dąży do {docelowy}", random.random())
            return round(aktualny-(step*(int(aktualny)-docelowy)), 3)
        elif aktualny < docelowy:
            #print(f"{aktualny} dąży do {docelowy}", random.random())
            return round(aktualny+(step*(int(docelowy)-aktualny)), 3)



    class Beat(object):
        
        def __init__(self, parent):
            self.y = 240
            self.x = 800
            self.age = 0
            self.parent = parent

        def move(self, tetno, speed, fps=60):
            self.x -= int(tetno)/fps*speed

        def get_pos(self):
            return (self.x, self.y)

        def get_points(self, wykrycie = 60, mod=0.1):
            return mod*(wykrycie-abs(self.x - 120))

        def destroy(self, wykrycie = 20):
            if len(self.parent)<=2:
                return self.get_points(wykrycie=wykrycie)
            else:
                self.parent.pop(self.parent.index(self))
                return self.get_points(wykrycie=wykrycie)

    screen = pg.display.set_mode((720, 480))
    clock = pg.time.Clock()      
    
# Load textures
    t_bgdef = pg.image.load("img/bg_def.png")
    t_bgbr = pg.image.load("img/bg_bright.png").convert()
    t_bl = pg.image.load("img/block.png")
    t_dt = pg.image.load("img/det.png").convert_alpha()

#Ładowanie dźwięków
    uderzenie = pg.mixer.Sound('sounds/uderzenie.wav')
      

    alpha_measure = 0
    SPEED = 2

    while True:
        done = False    
        beats = []
        beats.append(Beat(beats))
        tetno = 60.0
        tetno_doc = 60
        points = 100
        counter = 0
        cl_time = time.clock()

        while not done:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    done = True
                    quit_program.set()

            # Check death
            if points<0 and not DEBUG:
                break

            #Sprawdza nowy rytm
            tetno_doc = nowyrytm(tetno_doc, szansa=0.003, minimum=50, maximum=120)
            tetno = idz_do_rytmu(tetno, tetno_doc, counter, step=0.01)


            if ((blink.value == 1 and DEBUG == False) or pg.key.get_pressed()[pg.K_SPACE]) and time.clock()-cl_time>20/tetno:
                uderzenie.play()
                cl_time = time.clock()
                print('BLINK!')
                points += int(sorted(beats, key=sort_key)[0].destroy())
                alpha_measure += 1
                blink.value = 0
            
            # background
            screen.blit(t_bgdef, (0, 0))
            if alpha_measure>-129:
                if alpha_measure >= 128:
                    alpha_measure = -129
                else:
                    alpha_measure += 16
                t_bgbr.set_alpha(128-abs(alpha_measure))
                screen.blit(t_bgbr, (0, 0))
                    

            points -= 20*managebeats(beats, tetno)
            for i in beats:
                i.move(tetno, SPEED)
                i.age += 1
                screen.blit(t_bl, i.get_pos())
            message_display(str(points), (60,30))
            message_display(str(round(tetno)), (660,30))
            screen.blit(t_dt, (120-75, 0))

            pg.display.flip()
            if pg.key.get_pressed()[pg.K_UP]:
                tetno_doc += 1
                print(tetno)
            if pg.key.get_pressed()[pg.K_DOWN]:
                tetno_doc -= 1
                print(tetno)


            clock.tick(60)
        message_display("U dead", (720/2,480/2))
        pg.display.flip()
        while True:
            if ((blink.value == 1 and DEBUG == False) or pg.key.get_pressed()[pg.K_SPACE]) and time.clock()-cl_time>0.05:
                blink.value = 0
                break
    
            if event.type == pg.QUIT:
                quit_program.set()
                break


# Zakończenie podprocesów
    proc_blink_det.join()