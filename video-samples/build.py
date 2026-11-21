
import subprocess,re
from PIL import Image,ImageDraw,ImageFont,ImageFilter
B='/workspace/india-news-now/';O=B+'video-samples/';import os;os.makedirs(O+'tmp',exist_ok=True)
dur=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',B+'episodes/2026-11-20.mp3']))
paras=[p.strip() for p in open(B+'scripts-in/2026-11-20.txt').read().split('\n\n') if p.strip()]
wc=[len(p.split()) for p in paras]
tot=sum(wc);print(dur,wc)
cards=[('INDIA NEWS TODAY','Friday, November 20, 2026','intro'),
('Weather','Cyclone Akvan makes landfall in Odisha','Weather'),
('Politics','Congress leads Rajasthan panchayat polls','Politics'),
('Politics','Modi presses industry on pay and hiring','Politics'),
('Diplomacy','Pakistan minister in Delhi for SCO forum','Diplomacy'),
('Science','India unveils home-grown bird flu vaccine for poultry','Science'),
('Markets','Sensex up 898 points; rupee at seven-month high','Markets'),
('Entertainment','Ramayana Part One enters top five grossers','Entertainment'),
('Cricket','India fight back in Wellington Test','Cricket'),
('That\'s India News Today','I\'m Nisha','outro')]
cols=[(0,0),(30,70),(60,40),(90,30),(40,90),(20,110),(10,120),(110,60),(30,100),(0,0)]
d=[dur*w/tot for w in wc]  # 10 paras incl intro & outro
def F(s,b=False):
    return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf' if b else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',s)
def wrap(dr,t,f,w):
    L=[];c=''
    for x in t.split():
        if dr.textlength((c+' '+x).strip(),f)>w:L.append(c);c=x
        else:c=(c+' '+x).strip()
    return L+[c]
segs=[]
for i,(lab,title,k) in enumerate(cards):
    W,H=2112,1188
    im=Image.new('RGB',(W,H));px=im.load()
    a=(14+cols[i][0]//3,27+cols[i][0]//4,60+cols[i][1]//2);b=(8,14,36)
    g=Image.linear_gradient('L').resize((W,H)).rotate(0)
    im=Image.composite(Image.new('RGB',(W,H),a),Image.new('RGB',(W,H),b),g)
    dr=ImageDraw.Draw(im)
    if k in('intro','outro'):
        c=Image.open(B+'cover-navy.jpg').convert('RGB');c.thumbnail((520,520));im.paste(c,((W-c.width)//2,170))
        y=740
        for t,s,bb in [(lab,64 if k=='intro' else 70,True),(title,44,False)]:
            f=F(s,bb);dr.text((W/2,y),t,font=f,fill=(255,255,255),anchor='mm');y+=90
    else:
        f=F(36,True);dr.rounded_rectangle((200,330,200+dr.textlength(lab.upper(),f)+60,400),12,fill=(230,170,60))
        dr.text((230,365),lab.upper(),font=f,fill=(10,20,40),anchor='lm')
        f=F(84,True);y=470
        for l in wrap(dr,title,f,1600):dr.text((200,y),l,font=f,fill=(255,255,255));y+=112
        dr.text((200,980),'India News Today with Nisha  |  Nov 20, 2026',font=F(32),fill=(160,175,205))
    p=O+f'tmp/c{i}.png';im.save(p)
    n=int(round(d[i]*25))
    z=f"zoompan=z='1+0.05*on/{n}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d={n}:s=1920x1080:fps=25,fade=t=in:d=0.5,fade=t=out:st={d[i]-0.5}:d=0.5"
    subprocess.check_call(['ffmpeg','-y','-loglevel','error','-loop','1','-i',p,'-vf',z,'-frames:v',str(n),'-c:v','libx264','-pix_fmt','yuv420p',O+f'tmp/s{i}.mp4'])
    segs.append(O+f'tmp/s{i}.mp4')
open(O+'tmp/l.txt','w').write(''.join(f"file '{s}'\n" for s in segs))
subprocess.check_call(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',O+'tmp/l.txt','-i',B+'episodes/2026-11-20.mp3','-c:v','copy','-c:a','aac','-shortest',O+'2026-11-20-sample.mp4'])
