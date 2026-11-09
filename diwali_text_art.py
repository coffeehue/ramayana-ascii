"""Live Diwali text-particle art. Every visible spark and shape is a character.

python diwali_text_art.py
python diwali_text_art.py --speed 1.2 --width 624
python diwali_text_art.py --words "HAPPY DIWALI,RAMAYANA,RAM,SITA,LAXMAN,AYODHYA"

Space pauses; R restarts; arrows seek; +/- changes speed; Esc exits.
No video is loaded or prepared: each frame is calculated while the window runs.
"""
from __future__ import annotations

import argparse
import colorsys
import math
from pathlib import Path
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageTk

COLS, ROWS = 78, 80
CW, CH = 8, 12
W, H = COLS * CW, ROWS * CH
DURATION = 12.0
DEFAULT_WORDS = ['HAPPY DIWALI', 'RAMAYANA', 'RAM', 'SITA', 'LAXMAN', 'AYODHYA', 'DEEPAVALI', 'LIGHT']
PALETTE = [.10, .055, .53, .76, .91, .085]


def ease(x):
    x = np.clip(x, 0, 1)
    return x*x*(3-2*x)


def mono(size, bold=False):
    paths = ([r'C:\Windows\Fonts\consolab.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf']
             if bold else [r'C:\Windows\Fonts\consola.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'])
    for path in paths:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


class TextFireworks:
    def __init__(self, words=None):
        self.words = list(words or DEFAULT_WORDS)
        self.bank = ' '.join(self.words) + ' '
        self.font = mono(13, True)
        self.tiles = {}
        self.rng = np.random.default_rng(4811)
        self.background = (3, 6, 11)
        self.events = []
        self.comets = [(.18, 1.55, (300, 865), (312, 260), 0)]
        self.add(312, 260, 1.55, 0, 155, 1.9, 112)
        for i, (x,y,end) in enumerate([(100,160,2.1),(514,195,2.3),(93,385,2.52),
                                       (522,430,2.73),(211,530,2.94),(442,612,3.15)]):
            self.comets.append((1.59+i*.035,end,(312,260),(x,y),i%6))
            self.add(x,y,end,i%6,115,1.65,66)
        for i in range(5):
            x=90+i*111; y=260+(i%2)*145; end=3.65+i*.18
            self.comets.append((2.92+i*.13,end,(312,930),(x,y),(i+1)%6))
            self.add(x,y,end,(i+1)%6,128,1.7,78)
        for i,(x,y) in enumerate([(178,260),(455,290),(312,490)]):
            end=4.75+i*.24
            self.comets.append((end-.65,end,(312,930),(x,y),0))
            self.add(x,y,end,0,180,1.8,100)
        for i in range(9):
            angle=i*2.4
            self.add(312+math.cos(angle)*205,460+math.sin(angle)*190,5.45+i*.065,1,43,.85,20)
        self.targets=self.title_targets()
        pool=[]
        for e in self.events:
            age=6.2-e['start']
            if 0<age<e['life']:
                x,y=self.position(e,age)
                pool.extend(zip(x,y))
        self.origins=np.asarray(pool)[self.rng.integers(0,len(pool),len(self.targets))]
        self.delays=self.rng.uniform(0,.3,len(self.targets))
        self.phases=self.rng.uniform(0,math.tau,len(self.targets))
        self.last_cells=0

    def add(self,x,y,start,color,speed,life,n):
        theta=self.rng.uniform(0,math.tau,n)
        r=np.sqrt(1-self.rng.uniform(-1,1,n)**2)*speed
        self.events.append(dict(x=x,y=y,start=start,color=color,life=life,
                                vx=np.cos(theta)*r,vy=np.sin(theta)*r,
                                phase=self.rng.uniform(0,math.tau,n),
                                ttl=life*self.rng.uniform(.75,1.12,n)))

    @staticmethod
    def position(e,age):
        drag=(1-np.exp(-.7*age))/.7
        return (e['x']+e['vx']*drag+np.sin(age*3+e['phase'])*age*10,
                e['y']+e['vy']*drag+34*age*age)

    def title_targets(self):
        # This mask only chooses character cells. It is never painted into a frame.
        mask=Image.new('L',(W,H));d=ImageDraw.Draw(mask)
        for word,y,size in [('HAPPY',310,132),('DIWALI',455,144)]:
            f=mono(size,True);b=d.textbbox((0,0),word,font=f)
            d.text(((W-(b[2]-b[0]))/2-b[0],y-b[1]),word,font=f,fill=255)
        coarse=np.asarray(mask.resize((COLS,ROWS),Image.Resampling.BOX))
        yy,xx=np.where(coarse>65)
        points=list(zip((xx+.5)*CW,(yy+.5)*CH))
        # The diya is also a text outline and a text-filled flame.
        for u in np.linspace(0,math.pi,70):
            points.append((312+66*math.cos(u),735+31*math.sin(u)))
        for x in np.arange(247,378,8):points.append((x,735))
        for y in np.arange(665,733,CH):
            radius=18*math.sin((y-665)/68*math.pi)**.8
            for x in np.arange(312-radius,313+radius,CW):points.append((x,y))
        cells={(int(x//CW),int(y//CH)) for x,y in points}
        return np.array([((x+.5)*CW,(y+.5)*CH) for x,y in sorted(cells)])

    def clear(self):
        self.energy=np.zeros((ROWS,COLS),dtype=float)
        self.colors=np.zeros((ROWS,COLS),dtype=np.uint8)
        self.letters={}

    def plot(self,x,y,brightness,color=0,char=None):
        col,row=int(x//CW),int(y//CH)
        if not (0<=col<COLS and 0<=row<ROWS) or brightness<=self.energy[row,col]:return
        self.energy[row,col]=min(1,brightness)
        self.colors[row,col]=color%len(PALETTE)
        if char is not None:self.letters[(row,col)]=char
        else:self.letters.pop((row,col),None)

    def text_path(self,points,word,color,alpha=1):
        # Each letter follows the path; whole words remain ordered along each trail.
        for i,(x,y) in enumerate(points):
            char=word[i%len(word)]
            if char!=' ':self.plot(x,y,alpha*(.35+.65*i/max(1,len(points)-1)),color,char)

    def orb(self,x,y,r,t,color=0):
        for row in range(max(0,int((y-r)/CH)),min(ROWS,int((y+r)/CH)+1)):
            for col in range(max(0,int((x-r)/CW)),min(COLS,int((x+r)/CW)+1)):
                dx,dy=((col+.5)*CW-x)/r,((row+.5)*CH-y)/r
                q=dx*dx+dy*dy
                if q>=1:continue
                depth=math.sqrt(1-q)
                light=.32+.68*max(0,depth*.82-dx*.4-dy*.2)
                char=self.bank[(col+row*7-int(t*14))%len(self.bank)]
                if char==' ':char='.'
                self.plot((col+.5)*CW,(row+.5)*CH,light,color,char)

    def comet(self,t,event):
        start,end,origin,target,color=event
        if not start<t<end:return
        u=(t-start)/(end-start)
        def at(v):
            v=np.asarray(v)
            bend=65 if color%2 else -65
            return np.column_stack([origin[0]+(target[0]-origin[0])*v+bend*np.sin(v*math.pi),
                                    origin[1]+(target[1]-origin[1])*v-28*np.sin(v*math.pi)])
        tail=at(np.linspace(max(0,u-.48),u,44))
        self.text_path(tail,self.words[color%len(self.words)],color)
        x,y=at([u])[0]
        if start<.5:self.orb(x,y,31,t,color)
        else:self.plot(x,y,1,color,'*')

    def burst(self,t,e):
        age=t-e['start']
        if age<0 or age>e['life']*1.12:return
        for k,lag in enumerate(np.linspace(.4,0,7)):
            a=max(0,age-lag)
            x,y=self.position(e,a)
            alpha=np.maximum(0,1-age/e['ttl'])**.55*(.2+.8*k/6)
            word=self.words[e['color']%len(self.words)]
            for i in range(len(x)):
                c=word[(i+k)%len(word)]
                if c!=' ':self.plot(x[i],y[i],alpha[i],e['color'],c)
        if age<.27:
            r=18+age*180
            pts=[(e['x']+r*math.cos(a),e['y']+r*.72*math.sin(a)) for a in np.linspace(0,math.tau,55)]
            self.text_path(pts,'HAPPY DIWALI ',e['color'],.7*(1-age/.27))

    def greeting(self,t):
        if t<6.2:return
        progress=np.clip((t-6.2-self.delays)/1.7,0,1)
        u=ease(progress)
        p=self.origins+(self.targets-self.origins)*u[:,None]
        p[:,0]+=np.sin(self.phases)*np.sin(progress*math.pi)*55
        p[:,1]-=np.sin(progress*math.pi)*55
        for i,(x,y) in enumerate(p):
            if progress[i]<=0:continue
            col,row=int(x//CW),int(y//CH)
            # Stable horizontal word texture once the characters arrive.
            index=(col+row*5)%len(self.bank) if progress[i]>=1 else i%len(self.bank)
            c=self.bank[index]
            if c==' ':c='.'
            shimmer=.86+.14*math.sin(t*2+i*.23)
            self.plot(x,y,(.4+.6*float(u[i]))*shimmer,0,c)
        if t>8.1:
            for j in range(45):
                age=(t+j*.137)%1.8
                i=(j*31)%len(self.targets)
                x,y=self.targets[i]
                self.plot(x+math.sin(j+age)*12,y-age*26,.48*(1-age/1.8),1,'+' if j%3 else '*')
            # Small character fireworks keep the title readable.
            for j,(x,y) in enumerate([(80,265),(540,650),(505,258),(90,670)]):
                age=t-(8.5+j*.53)
                if not 0<age<1.0:continue
                r=age*43
                pts=[(x+r*math.cos(a),y+r*math.sin(a)) for a in np.linspace(0,math.tau,24)]
                self.text_path(pts,'DIWALI ',0,1-age)

    def tile(self,c,color,level):
        key=(c,color,level)
        if key not in self.tiles:
            hue=PALETTE[color]
            values=colorsys.hsv_to_rgb(hue,.42 if level>6 else .6,.12+.88*(level/9)**.65)
            tile=Image.new('RGB',(CW,CH),self.background)
            ImageDraw.Draw(tile).text((0,-2),c,font=self.font,fill=tuple(round(v*255) for v in values))
            self.tiles[key]=tile
        return self.tiles[key]

    def phase_name(self,t):
        if t<1.55:return 'IGNITE'
        if t<3.3:return 'PROPAGATE'
        if t<5.3:return 'CELEBRATE'
        if t<6.2:return 'SCATTER'
        if t<8.2:return 'ASSEMBLE'
        return 'HAPPY DIWALI'

    def frame(self,t,hud=True):
        self.clear()
        if t<.25:self.plot(300,865,.7,0,'*')
        for e in self.comets:self.comet(t,e)
        for e in self.events:self.burst(t,e)
        self.greeting(t)
        im=Image.new('RGB',(W,H),self.background)
        yy,xx=np.where(self.energy>.12);self.last_cells=len(xx)
        for row,col in zip(yy,xx):
            c=self.letters.get((row,col),self.bank[(col+row*5)%len(self.bank)])
            if c==' ':continue
            level=min(9,round(self.energy[row,col]*9))
            im.paste(self.tile(c,int(self.colors[row,col]),level),(int(col)*CW,int(row)*CH))
        if hud:
            d=ImageDraw.Draw(im);f=mono(12)
            d.text((16,16),'python diwali_text_art.py',font=f,fill=(116,137,150))
            d.text((16,H-28),f'{self.phase_name(t):<14} t={t:05.2f}  glyphs={self.last_cells:04d}',font=f,fill=(137,160,163))
            if int(t*2)%2==0:d.text((W-28,H-28),'_',font=f,fill=(246,191,92))
        return im


def run(scene,width=546,speed=1.,hud=True):
    import tkinter as tk
    root=tk.Tk();root.title('Diwali | live text art')
    root.configure(bg='#03060b');root.resizable(False,False)
    label=tk.Label(root,bg='#03060b',bd=0);label.pack()
    bar=tk.Label(root,bg='#03060b',fg='#98a9af',font=('Consolas',9));bar.pack(pady=5)
    state=dict(t=0.,speed=speed,playing=True,last=time.perf_counter())
    def pause(_=None):state['playing']=not state['playing']
    def reset(_=None):state.update(t=0.,playing=True)
    def change(amount):state['speed']=round(float(np.clip(state['speed']+amount,.25,3)),2)
    def seek(amount):state['t']=float(np.clip(state['t']+amount,0,DURATION-.01))
    def tick():
        start=time.perf_counter();dt=start-state['last'];state['last']=start
        if state['playing']:state['t']=(state['t']+dt*state['speed'])%DURATION
        im=scene.frame(state['t'],hud)
        if width!=W:im=im.resize((width,round(H*width/W)),Image.Resampling.LANCZOS)
        photo=ImageTk.PhotoImage(im);label.configure(image=photo);label.image=photo
        bar.configure(text=f"Space: pause  R: replay  +/-: speed {state['speed']:g}x  Esc: close")
        root.after(max(1,33-round((time.perf_counter()-start)*1000)),tick)
    root.bind('<space>',pause);root.bind('r',reset);root.bind('R',reset)
    root.bind('<Left>',lambda e:seek(-.5));root.bind('<Right>',lambda e:seek(.5))
    root.bind('+',lambda e:change(.1));root.bind('=',lambda e:change(.1));root.bind('-',lambda e:change(-.1))
    root.bind('<Escape>',lambda e:root.destroy())
    tick();root.mainloop()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--speed',type=float,default=1.)
    p.add_argument('--width',type=int,default=546,help='Window width; 624 shows native-size glyphs')
    p.add_argument('--words',default=','.join(DEFAULT_WORDS),help='Comma-separated words, using English letters')
    p.add_argument('--no-hud',action='store_true',help='Hide the command and live counters')
    args=p.parse_args()
    words=[w.strip().upper() for w in args.words.split(',') if w.strip()]
    if not words or any(not all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789-!' for c in w) for w in words):
        p.error('Supply at least one word using English letters, spaces, numbers, hyphens or !')
    if not .25<=args.speed<=3 or not 234<=args.width<=1600:p.error('Speed: 0.25–3; width: 234–1600.')
    print('Starting live text art. Space: pause; R: restart; +/-: speed; Esc: close.',flush=True)
    run(TextFireworks(words),args.width,args.speed,not args.no_hud)


if __name__=='__main__':main()
