"""Ramayana to Diwali, full-bleed 16:9 movie edition.

python diwali_ramayana_movie.py --fullscreen --paused

F11 toggles fullscreen. Space plays or pauses. R restarts playback.
Plus and minus zoom the scene. Zero resets zoom.
Escape leaves fullscreen or closes the window.
"""
from __future__ import annotations
import argparse
from functools import lru_cache
import math
import time
import numpy as np
from PIL import Image, ImageDraw, ImageTk, ImageFilter, ImageFont
from diwali_text_art import TextFireworks, mono, ease, DEFAULT_WORDS

W,H=960,1080
CW,CH=6,9
COLS,ROWS=W//CW,H//CH
MOVIE_W = 1920
MOVIE_COLS = MOVIE_W//CW
# The original character masks use the middle 960 pixels as world coordinates.
WORLD_OFFSET = (MOVIE_W-W)//2
DURATION=18.6
FESTIVAL_START=6.6
RELEASE=2.0
CHASE_START=2.3
IMPACT=4.2
TRAVEL=IMPACT-CHASE_START
CAMERA_CENTER=(480,520)
RAVANA_NEAR_SCALE=1.28
COLORS=[(255,208,119),(255,150,77),(111,198,255),(130,233,214),(219,138,229),(255,241,202)]
SCREEN_BLACK = "#000000"


def temple(draw, x, ground, width, height, stone, light, windows=False):
    """Draw a tiered tower and its light-facing edge into a color guide."""
    left, right = x-width/2, x+width/2
    shoulder = ground-height*.32
    draw.rectangle((left, shoulder, right, ground), fill=stone)
    draw.polygon([(left, shoulder), (x-width*.29, ground-height*.71),
                  (x-width*.12, ground-height*.89), (x, ground-height),
                  (x+width*.12, ground-height*.89), (x+width*.29, ground-height*.71),
                  (right, shoulder)], fill=stone)
    shadow = tuple(int(v*.66) for v in stone)
    draw.polygon([(x,ground-height),(x+width*.12,ground-height*.89),
                  (x+width*.29,ground-height*.71),(right,shoulder),
                  (right,ground),(x,ground)],fill=shadow)
    for fraction, span in ((.29,.55), (.39,.45), (.53,.36), (.68,.26), (.84,.15)):
        y = ground-height*fraction
        draw.rectangle((x-width*span, y-4, x+width*span, y+4), fill=light)
    draw.line((x, ground-height, x, ground-height-13), fill=light, width=3)
    if windows:
        for offset in (-.3, 0, .3):
            xx = x+width*offset
            draw.rounded_rectangle((xx-7, ground-height*.21, xx+7, ground-height*.06),
                                   radius=5, fill=(175, 103, 49))


def landscape(kind):
    """Paint value and color guides. Only the glyph translation reaches the screen."""
    yy, xx = np.mgrid[0:H, 0:MOVIE_W].astype(np.float32)
    xx -= WORLD_OFFSET
    warm = kind in ('festival', 'greeting')
    moon_x, moon_y, radius = (870, 310, 112) if kind == 'terrace' else (485, 322, 77)
    if warm:
        moon_x, moon_y, radius = 480, 432, 0
    distance = np.hypot(xx-moon_x, yy-moon_y)
    glow = np.exp(-distance**2/(2*230**2))
    horizon = np.exp(-((yy-665)/235)**2)
    cloud = np.maximum(0, np.sin(xx*.008+yy*.021) + .54*np.cos(xx*.017-yy*.042)
                       + .36*np.sin(xx*.035+yy*.011) - .32)
    cloud *= np.exp(-((yy-422)/370)**2)
    tones = ((14,10,29),(36,14,23),(24,10,20)) if warm else ((8,14,33),(10,26,39),(13,32,38))
    base, halo, dusk = (np.array(c, dtype=np.float32) for c in tones)
    rgb = base + glow[...,None]*halo + horizon[...,None]*dusk
    rgb += cloud[...,None]*np.array((17,8,20) if warm else (7,15,24))
    if radius:
        inside = distance < radius
        texture = .77+.11*np.sin(xx*.023+yy*.051)+.12*np.cos(xx*.048-yy*.042)
        rgb[inside] = texture[inside,None]*np.array((179,143,102) if kind=='terrace' else (106,136,161))
    image = Image.fromarray(np.uint8(np.clip(rgb,0,255)), 'RGB')
    draw = ImageDraw.Draw(image)
    xs = np.arange(-12, MOVIE_W+25, 12)
    for i, altitude in enumerate((628, 697, 754)):
        world_x = xs-WORLD_OFFSET
        ridge = altitude + 47*np.sin(world_x/(139-i*24)+i*2) + 24*np.cos(world_x/(54-i*5)+i)
        color = ((69,37,65),(49,26,47),(28,16,30))[i] if warm else ((39,76,97),(28,57,75),(15,36,53))[i]
        draw.polygon([*zip(xs,ridge),(MOVIE_W,H),(0,H)],fill=color)
        draw.line(list(zip(xs,ridge)), fill=tuple(v+14 for v in color), width=5)

    if kind == 'terrace':
        for x, width, height in ((-225,75,82),(-133,93,124),(614,62,93),
                                 (694,92,155),(790,60,101),(856,38,63),
                                 (1034,115,181),(1160,74,116)):
            temple(draw,x+WORLD_OFFSET,730,width,height,(41,57,71),(88,89,82))
        # Broken reflections give the distant shore a second, lower layer.
        draw.rectangle((0,731,MOVIE_W,829),fill=(20,39,55))
        for i in range(19):
            y=736+i*5
            mid=moon_x+WORLD_OFFSET+math.sin(i*2.27)*24
            span=30+i*4+17*math.sin(i*1.4)
            draw.line((mid-span,y,mid+span,y),fill=(67+i,77+i,83+i),width=2)
        draw.rectangle((0,830,MOVIE_W,H),fill=(24,27,42))
        for y in (835, 866, 901, 947, 1005):
            draw.line((0,y,MOVIE_W,y),fill=(62,65,78),width=4)
        for x in range(-260, MOVIE_W+350, 110):
            draw.line((MOVIE_W/2+(x-MOVIE_W/2)*.36,831,x,H),fill=(35,39,53),width=2)
        # Ink-and-gold columns and a double arch frame the archer and the moon.
        for x in (76, MOVIE_W-133):
            draw.rectangle((x,453,x+57,833),fill=(67,48,56))
            draw.rectangle((x+37,453,x+57,833),fill=(41,33,48))
            for n in range(5,57,10):
                draw.line((x+n,474,x+n,809),fill=(94,72,63),width=3)
            for y in (460,471,800,817):
                draw.rectangle((x-8,y,x+65,y+6),fill=(122,89,60))
        for inset, color in ((0,(104,79,58)),(13,(69,54,52)),(26,(113,85,55))):
            draw.arc((92+inset, 171+inset, MOVIE_W-92-inset, 752-inset),180,360,fill=color,width=7)
        for i in range((MOVIE_W-100)//39):
            x=56+i*39
            draw.line([(x,973),(x+11,960),(x+22,973),(x+11,986),(x,973)],fill=(60,49,58),width=2)
    elif kind == 'chase':
        center = MOVIE_W//2
        for side in (-1,1):
            for x, width, height in ((161,165,332),(299,87,190),(432,110,201),
                                     (594,138,263),(790,164,340)):
                temple(draw,center+side*x,741+int(x*.24),width,height,(32,46,67),(77,77,89))
        draw.polygon([(center-39,683),(center+39,683),(MOVIE_W-100,H),(100,H)],fill=(30,32,46))
        for x in range(120,MOVIE_W-110,120):
            draw.line((center+(x-center)*.045,683,x,H),fill=(49,50,66),width=2)
        for y in (710,744,786,840,912,1005):
            width=39+(y-683)*2.05
            draw.line((center-width,y,center+width,y),fill=(55,54,69),width=2)
    else:
        for x, width, height in ((-370,120,195),(-227,135,240),(-78,94,140),
                                 (76,103,165),(200,109,231),(337,97,131),(480,164,243),
                                 (625,97,131),(766,109,231),(890,103,165),
                                 (1038,94,140),(1187,135,240),(1330,120,195)):
            temple(draw,x+WORLD_OFFSET,927,width,height,(75,37,55),(149,78,64),windows=True)
        draw.rectangle((0,928,MOVIE_W,H),fill=(47,25,43))
        for y in (932, 951, 997):
            draw.line((0,y,MOVIE_W,y),fill=(107,57,58),width=4)
        for x in range(23, MOVIE_W, 37):
            draw.ellipse((x-3,959,x+3,965),fill=(174,94,42))
        if kind == 'greeting':
            # A filigree medallion sets off the title without filling its letter counters.
            for radius, color in ((333,(90,49,79)), (354,(136,73,69)), (378,(78,47,81))):
                points = []
                for a in np.linspace(0,math.tau,481):
                    r=radius*(.98+.023*math.cos(a*16))
                    points.append((MOVIE_W/2+r*math.cos(a),515+r*.92*math.sin(a)))
                draw.line(points,fill=color,width=6)
    return image


def glyph_backdrop(guide, font, ink):
    """Convert each color sample into a glyph with matching shade and density."""
    samples = np.asarray(guide.resize((MOVIE_COLS,ROWS),Image.Resampling.BOX), dtype=np.float32)
    ramp = '.:-=+x*#%@'
    row, col = np.indices((ROWS,MOVIE_COLS))
    value = samples.max(axis=-1)
    density = np.clip((value/22 + .9*np.sin(row*2.13+col*4.57)).astype(int),0,len(ramp)-1)
    atlas = []
    for char in ramp:
        stamp=Image.new('L',(CW,CH))
        ImageDraw.Draw(stamp).text((0,-1),char,font=font,fill=255)
        atlas.append(np.asarray(stamp,dtype=np.float32)/255)
    shade = np.stack(atlas)[density]
    cells = np.array(ink) + shade[...,None]*samples[:,:,None,None,:]*1.08
    pixels = cells.transpose(0,2,1,3,4).reshape(H,MOVIE_W,3)
    return Image.fromarray(np.uint8(np.clip(pixels,0,255)), 'RGB')


class Ramayana(TextFireworks):
    def __init__(self,words=None):
        super().__init__(words)
        self.rng=np.random.default_rng(9908)
        self.background=(4,6,13)
        self.font=mono(10,True)
        self.tiles={}
        self.backdrops = {name:glyph_backdrop(landscape(name), self.font, self.background)
                          for name in ('terrace','chase','festival','greeting')}
        self.atmosphere = np.random.default_rng(821).uniform(0,1,(155,4))
        # Space the same firework choreography across the wider skyline.
        def festival_x(x):
            return 480+(x-312)*W/624*1.8
        for e in self.events:
            e['x']=festival_x(e['x']);e['y']*=H/960
            e['vx']*=1.35;e['vy']*=1.1
        self.comets=[(a,b,(festival_x(x),y*H/960),(festival_x(xx),yy*H/960),c)
                     for a,b,(x,y),(xx,yy),c in self.comets[1:]]
        self.targets*=np.array([W/624,H/960])
        self.origins[:,0]=festival_x(self.origins[:,0])
        self.origins[:,1]*=H/960
        # Re-sample the big title on this stage's grid, rather than stretching sparse cells.
        mask=Image.new('L',(W,H));draw=ImageDraw.Draw(mask)
        for text,y,size in [('HAPPY',345,184),('DIWALI',510,215)]:
            f=mono(size,True);b=draw.textbbox((0,0),text,font=f)
            draw.text(((W-b[2]+b[0])/2,y-b[1]),text,font=f,fill=255)
        a=np.asarray(mask.resize((COLS,ROWS),Image.Resampling.BOX));yy,xx=np.where(a>65)
        title=np.column_stack([(xx+.5)*CW,(yy+.5)*CH])
        self.targets=np.concatenate([title,self.targets[self.targets[:,1]>700]])
        self.origins=self.origins[self.rng.integers(0,len(self.origins),len(self.targets))]
        self.delays=self.rng.uniform(0,.3,len(self.targets))
        self.phases=self.rng.uniform(0,math.tau,len(self.targets))
        # First shell: a flower-like outer layer plus a different inner shell.
        e=self.events[0]
        theta=np.linspace(0,math.tau,len(e['vx']),endpoint=False)
        r=195*(.8+.2*np.cos(theta*8))
        e['vx']=np.cos(theta)*r;e['vy']=np.sin(theta)*r*.82
        self.add(480,292.5,1.65,3,120,1.6,90)
        self.rama_cells=self.sample(self.rama_body(),'RAM SITA LAXMAN ')
        self.ravana_mask=self.ravana_body()
        self.ravana_near_mask=self.project_ravana(RAVANA_NEAR_SCALE)
        self.ravana_cells=self.sample(self.ravana_near_mask,'RAVANA LANKA ')
        self.fallen_mask=self.defeat_mask(1.5)
        self.fallen_cells=self.sample(self.fallen_mask,'RAVANA LANKA ')
        ids=np.linspace(0,len(self.fallen_cells)-1,110,dtype=int)
        self.embers=[self.fallen_cells[i] for i in ids]
        self.ring_angles=np.linspace(0,math.tau,150)
        self.rama_transform=None
        self.flight_dust=self.rng.uniform(0,1,(16,3))

    def clear(self):
        self.energy=np.zeros((ROWS,MOVIE_COLS))
        self.colors=np.zeros((ROWS,MOVIE_COLS),dtype=np.uint8)
        self.letters={}

    def plot(self,x,y,brightness,color=0,char=None):
        if self.rama_transform is not None:
            scale,cx,cy=self.rama_transform
            x=cx+(x-250)*scale;y=cy+(y-620)*scale
        col,row=int((x+WORLD_OFFSET)//CW),int(y//CH)
        if not (0<=col<MOVIE_COLS and 0<=row<ROWS) or brightness<=self.energy[row,col]:return
        self.energy[row,col]=min(1,brightness);self.colors[row,col]=color%6
        if char is not None:self.letters[(row,col)]=char
        else:self.letters.pop((row,col),None)

    def tile(self,c,color,level):
        key=(c,color,level)
        if key not in self.tiles:
            im=Image.new('RGB',(CW,CH),self.background)
            lum=.16+.84*(level/9)**.7
            ImageDraw.Draw(im).text((0,-1),c,font=self.font,fill=tuple(int(v*lum) for v in COLORS[color]))
            self.tiles[key]=im
        return self.tiles[key]

    @staticmethod
    def sample(mask,word,x_origin=0):
        a=np.asarray(mask)[CH//2::CH,CW//2::CW]
        yy,xx=np.where(a>0)
        return [(float(x_origin+x*CW+CW/2),float(y*CH+CH/2),int(a[y,x])-1,
                 '#' if a[y,x]==6 else
                 (word[(x+y*3)%len(word)] if word[(x+y*3)%len(word)]!=' ' else '.')) for x,y in zip(xx,yy)]

    @staticmethod
    def rama_body():
        m=Image.new('L',(W,H));d=ImageDraw.Draw(m)
        # Hair and topknot, right-facing profile, neck and torso.
        d.ellipse((187,446,242,504),fill=1)
        d.ellipse((199,427,225,452),fill=1)
        d.polygon([(209,468),(241,472),(245,489),(258,499),(243,506),(241,526),(215,529),(207,511)],fill=3)
        d.rectangle((219,515,237,549),fill=3)
        d.polygon([(206,541),(240,537),(267,565),(258,628),(239,657),(202,642),(196,594)],fill=3)
        # Sash, flared dhoti, bent leading knee and extended rear leg.
        d.polygon([(203,540),(214,538),(262,618),(250,634)],fill=1)
        d.polygon([(204,631),(256,633),(285,711),(245,736),(210,694),(179,725),(163,706)],fill=2)
        d.line([(181,708),(157,756),(125,811)],fill=3,width=22)
        d.line([(259,717),(302,749),(293,811)],fill=3,width=22)
        d.line([(123,814),(99,819)],fill=1,width=13)
        d.line([(290,814),(321,819)],fill=1,width=13)
        d.line([(208,645),(250,649)],fill=1,width=9)
        d.ellipse((228,486,233,491),fill=0)
        # Quiver and visible arrow ends behind the shoulder.
        d.polygon([(172,526),(190,520),(213,597),(190,606)],fill=1)
        for x in [161,171,181]:d.line([(x,487),(x+28,556)],fill=1,width=3)
        return m

    @staticmethod
    def ravana_body():
        m=Image.new('L',(W,H));d=ImageDraw.Draw(m)
        # One dominant face, eight separated side faces, and a tenth rear face.
        # Crowns, eyes, curled moustaches and a strong jaw survive glyph sampling.
        def head(cx,y,w,h):
            x=cx-w/2
            d.ellipse((x-3,y-4,x+w+3,y+h),fill=5)
            d.polygon([(x+4,y+10),(x+w-4,y+10),(x+w-3,y+h*.68),
                       (cx+w*.22,y+h),(cx-w*.22,y+h),(x+3,y+h*.68)],fill=2)
            crown=[(x-4,y+8),(x-1,y-h*.25),(x+w*.17,y-h*.11),
                   (x+w*.28,y-h*.4),(cx,y-h*.62),(x+w*.72,y-h*.4),
                   (x+w*.83,y-h*.11),(x+w+1,y-h*.25),(x+w+4,y+8)]
            d.polygon(crown,fill=1)
            d.line([(x-3,y+3),(x+w+3,y+3)],fill=6,width=3)
            d.ellipse((cx-3,y-h*.27-3,cx+3,y-h*.27+3),fill=2)
            for side in [-1,1]:
                ex=cx+side*w*.23
                d.line([(ex-w*.11,y+h*.29),(ex+w*.11,y+h*.25)],fill=0,width=max(3,int(w*.08)))
                d.ellipse((ex-w*.10,y+h*.34,ex+w*.10,y+h*.45),fill=6)
            d.line([(cx,y+h*.35),(cx-2,y+h*.61),(cx+3,y+h*.61)],fill=1,width=3)
            d.line([(x+3,y+h*.62),(x+w*.16,y+h*.75),(cx,y+h*.68),
                    (x+w*.84,y+h*.75),(x+w-3,y+h*.62)],fill=0,width=max(4,int(w*.11)))
            d.line([(x+3,y+h*.61),(x+w*.16,y+h*.7),(cx,y+h*.63),
                    (x+w*.84,y+h*.7),(x+w-3,y+h*.61)],fill=1,width=3)
            d.polygon([(cx-w*.13,y+h*.82),(cx+w*.13,y+h*.82),(cx,y+h*.99)],fill=0)
        head(720,326,49,49)
        for side in [-1,1]:
            for j in range(4):head(720+side*(69+j*48),408+j*9,36,49)
        head(720,408,82,91)
        # Fanned arms frame the king and keep his silhouette distinct from Rama.
        for side in [-1,1]:
            for j in range(5):
                shoulder=(720+side*55,525+j*13)
                elbow=(720+side*(90+j*9),505+j*31)
                hand=(720+side*(135+j*10),473+j*47)
                d.line([shoulder,elbow,hand],fill=5,width=12)
                d.ellipse((hand[0]-7,hand[1]-7,hand[0]+7,hand[1]+7),fill=1)
        d.rectangle((704,493,736,521),fill=2)
        d.polygon([(661,505),(775,505),(794,581),(763,669),(676,669),(650,582)],fill=5)
        d.polygon([(677,518),(761,518),(771,596),(719,627),(668,597)],fill=1)
        d.polygon([(689,532),(751,532),(756,585),(719,608),(684,585)],fill=2)
        # Neck ornaments, pauldrons and a central armor jewel.
        d.arc((684,490,756,553),0,180,fill=6,width=5)
        d.ellipse((712,555,728,573),fill=1)
        d.ellipse((655,504,686,536),fill=1)
        d.ellipse((754,504,785,536),fill=1)
        d.polygon([(676,640),(763,640),(799,745),(728,761),(646,739)],fill=1)
        d.polygon([(685,661),(750,661),(767,728),(721,746),(669,727)],fill=5)
        d.line([(679,735),(665,810)],fill=5,width=25)
        d.line([(758,736),(782,810)],fill=5,width=25)
        d.line([(665,813),(635,817)],fill=1,width=16)
        d.line([(781,813),(812,817)],fill=1,width=16)
        return m

    def paint_cells(self,cells,alpha=1,dx=0,dy=0):
        for x,y,c,ch in cells:self.plot(x+dx,y+dy,alpha,c,ch)

    def path(self,points,word='RAM ',color=0,alpha=1):
        # Equal-distance resampling prevents clumps of letters on long segments.
        points=np.asarray(points,float);out=[]
        for a,b in zip(points[:-1],points[1:]):
            n=max(2,int(np.linalg.norm(b-a)/5))
            out.extend(a+(b-a)*u for u in np.linspace(0,1,n,endpoint=False))
        for i,(x,y) in enumerate(out):
            c=word[i%len(word)]
            if c!=' ':self.plot(x,y,alpha,color,c)

    def rama(self,t):
        if t>=CHASE_START:return
        alpha=float(ease(t/.4))
        if alpha<=0:return
        # Rama is human-sized. At release the following camera leaves him behind.
        self.rama_transform=(1.15,278,604)
        self.paint_cells(self.rama_cells,alpha*.9)
        draw=float(ease((t-.55)/1.25)) if t<RELEASE else 0
        handx=330-105*draw if t<RELEASE else 244
        # Holding arm and drawing arm are separate articulated silhouettes.
        m=Image.new('L',(W,H));d=ImageDraw.Draw(m)
        d.line([(239,555),(315,566),(397,565)],fill=3,width=17)
        if t<RELEASE:d.line([(213,554),(181,585),(handx,565)],fill=3,width=15)
        else:d.line([(213,554),(184,574),(239,545)],fill=3,width=15)
        self.paint_cells(self.sample(m,'RAM '),alpha)
        u=np.linspace(0,1,65)
        bow=np.column_stack([345+(55-8*draw)*np.sin(u*math.pi),420+290*u])
        self.path(bow,'RAM ',0,alpha)
        stringx=330-105*draw if t<RELEASE else 346+8*math.sin((t-RELEASE)*38)*math.exp(-(t-RELEASE)*9)
        self.path([(345,420),(stringx,565),(345,710)],'|:|:',5,alpha*.75)
        if t<RELEASE:self.path([(handx,565),(425,565)],'---->',0,alpha)
        self.rama_transform=None

    @staticmethod
    def approach_scale(t):
        u=float(ease((t-CHASE_START)/TRAVEL))
        # Reveal usable detail earlier, then settle at a stable size before impact.
        return .32*(RAVANA_NEAR_SCALE/.32)**u

    def project_ravana(self,scale):
        # Sample the original silhouette again at every camera distance so enlarged
        # forms gain glyph detail instead of stretching into widely spaced letters.
        cx,cy=CAMERA_CENTER
        return self.ravana_mask.transform((W,H),Image.Transform.AFFINE,
                    (1/scale,0,720-cx/scale,0,1/scale,565-cy/scale),
                    resample=Image.Resampling.NEAREST)

    def defeat_mask(self,age):
        # Keep the figure intact through recoil and a controlled fall. Transform the
        # silhouette, then sample it anew: the letters never become a noisy cloud.
        recoil=float(ease(age/.32))*(1-float(ease((age-.4)/.3)))
        collapse=float(ease((age-.55)/.85))
        angle=5*recoil+68*collapse
        scale=1-.33*collapse
        radians=math.radians(angle)
        cs,sn=math.cos(radians),math.sin(radians)
        # Forward: rotate clockwise about the hips, shrink, then lower to the floor.
        px,py=480,665;dx,dy=25*collapse,150*collapse
        a,b=cs/scale,sn/scale;d,e=-sn/scale,cs/scale
        c=px-a*(px+dx)-b*(py+dy);f=py-d*(px+dx)-e*(py+dy)
        return self.ravana_near_mask.transform((W,H),Image.Transform.AFFINE,
                       (a,b,c,d,e,f),resample=Image.Resampling.NEAREST)

    def ravana(self,t):
        if t<CHASE_START:return
        if t<IMPACT:
            cells=self.sample(self.project_ravana(self.approach_scale(t)),'RAVANA LANKA ')
            self.paint_cells(cells,.94)
            return
        age=t-IMPACT
        if age<1.65:
            self.paint_cells(self.sample(self.defeat_mask(age),'RAVANA LANKA '),.94)
        elif age<2.35:
            fade=1-float(ease((age-1.65)/.7))
            self.paint_cells(self.fallen_cells,.85*fade)
        if 1.65<age<2.75:
            for i,(x,y,c,ch) in enumerate(self.embers):
                u=float(np.clip((age-1.65-(i%9)*.025)/.85,0,1))
                if not 0<u<1:continue
                # A restrained upward stream from the fallen body, with no re-forming blob.
                self.plot(x+math.sin(i*2.4)*u*12,y-u*80,.65*(1-u),0,ch)

    def arrow(self,t):
        if not RELEASE<=t<IMPACT+.28:return
        m=Image.new('L',(MOVIE_W,H));d=ImageDraw.Draw(m)
        if t<CHASE_START:
            u=(t-RELEASE)/(CHASE_START-RELEASE)
            # First show a clean horizontal release. Then cut directly behind it.
            tip=np.array([479+920*u,541.]);direction=np.array([1.,0.]);length=180
        else:
            u=float(np.clip((t-CHASE_START)/TRAVEL,0,1))
            tip=np.array([480.,610-90*float(ease((u-.55)/.45))])
            direction=np.array([0.,-1.]);length=335
            if t>=IMPACT:length=100
        tip[0] += WORLD_OFFSET
        normal=np.array([-direction[1],direction[0]])
        tail=tip-direction*length
        d.line([tuple(tail),tuple(tip-direction*24)],fill=6,width=9)
        # A filled, unmistakable arrowhead and two feather vanes, all sampled into glyphs.
        head=[tip,tip-direction*52+normal*24,tip-direction*39,
              tip-direction*52-normal*24]
        d.polygon([tuple(p) for p in head],fill=6)
        for sign in [-1,1]:
            feather=[tail+direction*9,tail+normal*sign*27,
                     tail+direction*67+normal*sign*16,tail+direction*80]
            d.polygon([tuple(p) for p in feather],fill=1)
        # A narrow empty margin separates the foreground arrow from the target's letters.
        # Expand by one glyph cell. Filtering the full pixel mask is costly during flight.
        occupied = m.resize((MOVIE_COLS, ROWS), Image.Resampling.BOX)
        halo = np.asarray(occupied.filter(ImageFilter.MaxFilter(3))) > 0
        self.energy[halo]=0
        self.paint_cells(self.sample(m,'RAM ',-WORLD_OFFSET),1-float(ease((t-IMPACT)/.28)))

    def flight_space(self,t):
        if not CHASE_START<=t<IMPACT:return
        u=(t-CHASE_START)/TRAVEL
        alpha=float(ease((t-CHASE_START)/.15))
        cx,cy=CAMERA_CENTER
        # Ground rays and outward-moving words sell the forward camera movement.
        for endx in [-250,180,780,1210]:
            self.path([(cx+(endx-cx)*.22,cy+100),(endx,1120)],'. : ',2,.14*alpha)
        for j,(angle,offset,rate) in enumerate(self.flight_dust):
            a=angle*math.tau
            depth=(offset+u*(.8+rate))%1
            r=65+720*depth**2
            x=cx+math.cos(a)*r;y=cy+math.sin(a)*r*.85
            # Keep the target's chest and faces free of competing decoration.
            if abs(x-cx)<280:continue
            tail=np.array([cx+(x-cx)*.92,cy+(y-cy)*.92])
            self.path([tail,(x,y)],'. : ',2,alpha*(.13+.12*depth))

    def impact(self,t):
        age=t-IMPACT
        if not 0<age<.32:return
        r=10+age*145
        p=[(480+r*math.cos(a),520+r*.7*math.sin(a)) for a in self.ring_angles]
        self.path(p,'RAM ',5,(1-age/.32)*.85)

    def first_bloom(self,ft):
        if not 0<ft<1.55:return
        u=ft/1.55
        center=np.array([480+45*math.sin(u*math.pi),680+(292-680)*ease(u)])
        # A braided rising column becomes a rotating rosette, all written in words.
        for strand in range(3):
            v=np.linspace(max(0,u-.6),u,85)
            xx=480+45*np.sin(v*math.pi)+np.sin(v*17+strand*math.tau/3)*(18+u*25)
            yy=680-388*ease(v)
            self.path(np.column_stack([xx,yy]),self.words[strand%len(self.words)]+' ',strand%2,.7)
        r=25+60*ease(u)
        for band in range(3):
            a=self.ring_angles+ft*(2 if band%2 else -2)
            rad=r*(.78+.22*np.cos(a*8))*(.6+band*.25)
            p=np.column_stack([center[0]+rad*np.cos(a),center[1]+rad*np.sin(a)*.8])
            self.path(p,'HAPPY DIWALI ',0,.9-band*.15)

    def diya(self,x,y,scale,t,alpha):
        u=np.linspace(0,math.pi,18)
        self.path([(x+26*scale*math.cos(a),y+10*scale*math.sin(a)) for a in u],'DIWALI ',0,alpha)
        self.path([(x-26*scale,y),(x+26*scale,y)],'AYODHYA ',0,alpha)
        for row in range(4):
            self.plot(x+math.sin(t*5+row)*2*scale,y-(row+1)*9*scale,alpha*(1-row*.14),0,'*' if row==3 else 'A')

    def stage(self,t):
        warm = t >= FESTIVAL_START
        for i, (px, py, offset, speed) in enumerate(self.atmosphere):
            x = 35-WORLD_OFFSET+px*(MOVIE_W-70) + math.sin(t*.9+offset*7)*13
            y = 164+(py*790 - t*(9+speed*15))%790
            if CHASE_START <= t < FESTIVAL_START and 255<x<705:
                continue
            flicker = .5+.5*math.sin(t*(2+speed)+offset*math.tau)
            self.plot(x,y,.12+flicker*(.22 if warm else .16),0 if warm or i%4==0 else 2,
                      '+' if i%9==0 else '.')
        if t < CHASE_START:
            for x in (110-WORLD_OFFSET,MOVIE_W-106-WORLD_OFFSET):
                self.diya(x,820,1.05,t,.65)
        if t>FESTIVAL_START+.3:
            for i, x in enumerate(range(90-WORLD_OFFSET,MOVIE_W-60-WORLD_OFFSET,86)):
                alpha=float(ease((t-FESTIVAL_START-.3-i*.07)/.35))*.65
                self.diya(x,938,.7,t+i,alpha)

    def backdrop(self, t):
        if t < CHASE_START:
            return self.backdrops['terrace'].copy()
        if t < FESTIVAL_START:
            return self.backdrops['chase'].copy()
        ft = t-FESTIVAL_START
        if ft < .85:
            return Image.blend(self.backdrops['chase'],self.backdrops['festival'],float(ease(ft/.85)))
        if ft < 6.2:
            return self.backdrops['festival'].copy()
        if ft >= 7.9:
            return self.backdrops['greeting'].copy()
        return Image.blend(self.backdrops['festival'],self.backdrops['greeting'],float(ease((ft-6.2)/1.7)))

    def festival(self,t):
        ft=t-FESTIVAL_START
        if ft<0:return
        self.first_bloom(ft)
        for c in self.comets:self.comet(ft,c)
        for e in self.events:self.burst(ft,e)
        # Final word assembly is still made only from small character tiles.
        if ft>=6.2:
            u=ease(np.clip((ft-6.2-self.delays)/1.7,0,1))
            p=self.origins+(self.targets-self.origins)*u[:,None]
            p[:,0]+=np.sin(self.phases)*np.sin(u*math.pi)*55
            for i,(x,y) in enumerate(p):
                if u[i]<=0:continue
                c=self.bank[(int(x//CW)+int(y//CH)*5)%len(self.bank)]
                self.plot(x,y,.45+.55*u[i],0,c if c!=' ' else '.')
            if ft>8.2:
                for j,(x,y) in enumerate([(-170,260),(1130,730),(1110,310),(-150,740)]):
                    age=ft-8.5-j*.55
                    if 0<age<1:
                        r=50*age
                        self.path([(x+r*math.cos(a),y+r*math.sin(a)) for a in self.ring_angles[::5]],'DIWALI ',0,1-age)

    def frame(self,t):
        self.clear();self.stage(t);self.flight_space(t);self.rama(t);self.ravana(t);self.arrow(t);self.impact(t);self.festival(t)
        im=self.backdrop(t)
        yy,xx=np.where(self.energy>.12)
        for row,col in zip(yy,xx):
            c=self.letters.get((row,col),self.bank[(col+row*5)%len(self.bank)])
            if c==' ':continue
            im.paste(self.tile(c,int(self.colors[row,col]),min(9,round(self.energy[row,col]*9))),
                     (int(col)*CW,int(row)*CH))
        return im


def fit_size(width, height, aspect):
    return (max(1, min(width, round(height*aspect))),
            max(1, min(height, round(width/aspect))))


def chapter(t):
    if t < RELEASE:
        return "The Last Arrow"
    if t < CHASE_START:
        return "Release"
    if t < IMPACT+.55:
        return ""
    if t < FESTIVAL_START:
        return "Ravana Falls"
    if t < FESTIVAL_START+1.8:
        return "Light Returns"
    if t < FESTIVAL_START+6.2:
        return "Ayodhya Lights Up for Rama’s Return"
    return ""


@lru_cache(maxsize=8)
def movie_fonts(height):
    scale = height/H
    try:
        title = ImageFont.truetype("C:/Windows/Fonts/georgia.ttf", max(1, round(57*scale)))
    except OSError:
        title = mono(max(1, round(47*scale)))
    return mono(max(1, round(23*scale))), title, mono(max(1, round(28*scale)))


class RecordingFrame:
    def __init__(self, scene, title):
        self.scene = scene
        self.title = title

    def frame(self, t, size, zoom=1.0):
        frame = self.scene.frame(t)
        if frame.size != size or zoom != 1:
            crop_w, crop_h = MOVIE_W/zoom, H/zoom
            left, top = (MOVIE_W-crop_w)/2, (H-crop_h)/2
            frame = frame.resize(size, Image.Resampling.LANCZOS,
                                 box=(left, top, left+crop_w, top+crop_h))
        width, height = size
        name_font, title_font, label_font = movie_fonts(height)
        draw = ImageDraw.Draw(frame)
        outline = (4,6,13)
        draw.text((width/2, .027*height), " ".join(self.title.upper()),
                  font=name_font, fill=(222,182,117), anchor="mt",
                  stroke_width=1, stroke_fill=outline)
        draw.text((width/2, .061*height), "A Festival of Light",
                  font=title_font, fill=(230,191,128), anchor="mt",
                  stroke_width=1, stroke_fill=outline)
        label = chapter(t)
        if label:
            draw.text((width/2, .128*height), label, font=label_font,
                      fill=(210,185,146), anchor="mt", stroke_width=1, stroke_fill=outline)
        return frame


def run(scene, width, height, speed, start_at=0., fullscreen=False, paused=False,
        title="Diwali", zoom=1.0):
    import tkinter as tk
    recording = RecordingFrame(scene, title)
    root = tk.Tk()
    root.title(f"{title} · A Festival of Light")
    root.configure(bg=SCREEN_BLACK)
    screen_w, screen_h = root.winfo_screenwidth(), root.winfo_screenheight()
    w, h = fit_size(min(width, max(1, screen_w-32)),
                    min(height, max(1, screen_h-100)), width/height)
    root.geometry(f"{w}x{h}+{(screen_w-w)//2}+{(screen_h-h)//2}")
    root.attributes("-fullscreen", fullscreen)
    canvas = tk.Canvas(root, bg=SCREEN_BLACK, bd=0, highlightthickness=0, cursor="none")
    canvas.pack(fill="both", expand=True)
    frame_id = canvas.create_image(0, 0, anchor="center")
    state = dict(t=start_at, speed=speed, zoom=zoom, playing=not paused, last=time.perf_counter())
    rendered = None
    photo = None

    def reset(_=None):
        state.update(t=0., playing=True, last=time.perf_counter())

    def pause(_=None):
        state["playing"] = not state["playing"]
        state["last"] = time.perf_counter()

    def seek(delta):
        state["t"] = float(np.clip(state["t"]+delta, 0, DURATION-.01))

    def zoom_by(delta):
        state["zoom"] = float(np.clip(state["zoom"]+delta, 1, 1.6))

    def reset_zoom(_=None):
        state["zoom"] = 1.0

    def toggle_fullscreen(_=None):
        root.attributes("-fullscreen", not root.attributes("-fullscreen"))

    def escape(_=None):
        if root.attributes("-fullscreen"):
            root.attributes("-fullscreen", False)
        else:
            root.destroy()

    def tick():
        nonlocal rendered, photo
        begin = time.perf_counter()
        if state["playing"]:
            state["t"] = (state["t"]+(begin-state["last"])*state["speed"])%DURATION
        state["last"] = begin
        vw, vh = canvas.winfo_width(), canvas.winfo_height()
        units = min(vw//16, vh//9)
        size = (16*units, 9*units)
        key = (state["t"], vw, vh, state["zoom"])
        if min(size) >= 32 and key != rendered:
            photo = ImageTk.PhotoImage(recording.frame(state["t"], size, state["zoom"]), master=root)
            canvas.itemconfigure(frame_id, image=photo)
            canvas.coords(frame_id, vw/2, vh/2)
            rendered = key
        root.after(max(1, 33-round((time.perf_counter()-begin)*1000)), tick)

    root.bind("<space>", pause)
    root.bind("<r>", reset)
    root.bind("<R>", reset)
    root.bind("<Left>", lambda event: seek(-.5))
    root.bind("<Right>", lambda event: seek(.5))
    root.bind("<plus>", lambda event: zoom_by(.1))
    root.bind("<equal>", lambda event: zoom_by(.1))
    root.bind("<minus>", lambda event: zoom_by(-.1))
    root.bind("<0>", reset_zoom)
    root.bind("<F11>", toggle_fullscreen)
    root.bind("<Escape>", escape)
    root.after_idle(tick)
    root.mainloop()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--width',type=int,help='Window width in pixels')
    p.add_argument('--height',type=int,help='Window height in pixels')
    p.add_argument('--title',choices=('diwali','ramayana'),default='diwali',
                   help='Choose the heading above the chapter labels')
    p.add_argument('--zoom',type=float,default=1.,help='Artwork zoom, from 1 to 1.6')
    p.add_argument('--speed',type=float,default=1.)
    p.add_argument('--start-at',type=float,default=0.,help='Jump to a time in the story, in seconds')
    p.add_argument('--fullscreen',action='store_true',help='Fit the 16:9 movie to the monitor')
    p.add_argument('--paused',action='store_true',help='Wait for Space before playing')
    p.add_argument('--words',default=','.join(DEFAULT_WORDS))
    args=p.parse_args()
    words=[w.strip().upper() for w in args.words.split(',') if w.strip()]
    if not words or any(any(c not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789-!' for c in w) for w in words):
        p.error('Use comma-separated English words.')
    for name, dimension in (('width', args.width), ('height', args.height)):
        if dimension is not None and not 320 <= dimension <= 7680:
            p.error(f'{name} must be 320–7680 pixels')
    if not 1<=args.zoom<=1.6 or not .25<=args.speed<=3 or not 0<=args.start_at<DURATION:
        p.error('Zoom 1–1.6; speed 0.25–3; start-at 0–18.6 (exclusive).')
    aspect = 16/9
    width = args.width or (round(args.height*aspect) if args.height else 1280)
    height = args.height or round(width/aspect)
    run(Ramayana(words), width, height, args.speed, args.start_at, args.fullscreen,
        args.paused, args.title.capitalize(), args.zoom)


if __name__=='__main__':main()
