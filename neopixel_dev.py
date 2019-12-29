import time
import colorsys
import math
import socket
import struct
import _thread

'''
TODO:
fade keeping color ratio
adjust color setting to be more accurate
adjust brightness to be more linear
'''

class NeoPixels():
    #init
    def __init__(self, DEVEL=True, count=300, fade=False, brightness=1.0):
        self.size = count
        self.DEVEL = DEVEL
        self.updatePygame = True
        self.lock = _thread.allocate_lock()
        self.brightness = brightness
        
        if fade:
            self.start_fade()
        
        if self.DEVEL:
            self.pixels = [(0,0,0)] * self.size
            self._display_thread = _thread.start_new_thread(self._display,())
        else:
            import board
            import neopixel
            self.pixels = neopixel.NeoPixel(board.D18, 300, auto_write=False)

    def __enter__(self):
        return self
        
    def __exit__(self):
        if not self.DEVEL:
            self.pixels.deinit()
        else:
            self._display_thread.exit()
        self.stop_fade()

    def __getitem__(self, index):
        with self.lock:
            val = self.pixels[index]
        return val

    def __setitem__(self, index, val):
        with self.lock:
            self.pixels[index] = val

    def __len__(self):
        return len(self.pixels)
        
    #updates the leds with the data in pixels
    def show(self):
        if not self.DEVEL:
            pixels.show()
        else:
            self.updatePygame = True

    #fills pixels with a given color
    def fill(self, color):
        with self.lock:
            if self.DEVEL:
                for i in range(self.size):
                    self.pixels[i] = color
            else:
                self.pixels.fill(color)

    def set_brightness(self, ammount=1.0):
        if not self.DEVEL:
            self.pixels.brightness(ammount)            
        self.brightness = ammount

    #starts a thread constantly fading all pixels
    def start_fade(self, fadeDelay=0.05, fadeAmmount=20):
        self.fadeDelay = fadeDelay
        self.fadeAmmount = fadeAmmount
        if self._fade_thread is None:
            self._fade_thread = _thread.start_new_thread(self._fade(), ())

    #stops the fade thread
    def stop_fade(self):
        if self._fade_thread is not None:
            self._fade_thread.exit()
            self._fade_thread = None

    #sets the delay of the fade        
    def fade_setup(self, delay=0.05, fadeAmmount=20):
        self.fadeDelay = delay
        self.fadeAmmount = fadeAmmount

    #listens with a socket and gives sound data to the sound_handler
    def run_visualiser(self, sound_handler, port=12345, dataType=('e',2), dataLength=None, skipMalformed=True):
        if dataLength is None:
            dataLength = self.size
        #create socket server
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', port))
        s.listen(5)

        bytes_to_float = struct.Struct(dataType[0]).unpack
        melspectrum = []

        while True: 
            c, addr = s.accept()      
            print("Got connection from", addr) 

            try:
                while True:
                    data = c.recv(dataType[1])
                    if data:
                        fdata = bytes_to_float(data)[0]
                        if math.isinf(fdata) and (len(melspectrum) >= dataLength or not skipMalformed):#data is all received
                            sound_handler(melspectrum)
                            melspectrum.clear()
                        elif math.isinf(fdata):#malformed
                            melspectrum.clear()
                        else:
                            melspectrum.append(fdata)
                    else:
                        print("no more data from", client_address)
                        break
            except:
                print("Lost connection to", addr)
                melspectrum.clear()
            finally:
                c.close()

    def _fade(self):
        time.sleep(self.fadeDelay)
        with self.lock:
            for i in self.pixels:
                self.pixels[i] = (max(0,self.pixels[i][0]-self.fadeAmmount),max(0,self.pixels[i][1]-self.fadeAmmount),max(0,self.pixels[i][2]-self.fadeAmmount))                


    def _display(self):
        import pygame
        import pygame.gfxdraw

        pygame.init()
        screen = pygame.display.set_mode((900, 50),pygame.RESIZABLE)
        pygame.display.set_caption("Simulated Neopixels")
        clock = pygame.time.Clock()
        
        while True:
            clock.tick(50)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    _thread.interrupt_main()
                    return
                if event.type == pygame.VIDEORESIZE:
                    surface = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

            if self.updatePygame:
                screen.fill((0, 0, 0))
                w, h = screen.get_size()
                for i in range(self.size):
                    pygame.gfxdraw.box(screen,
                                       (w/self.size*i, 0, w/self.size,h),
                                       tuple( map(lambda x: int(x*self.brightness), self.pixels[i]) ))
            self.updatePygame = False
            
            pygame.display.flip()

        
