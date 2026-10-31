import math, os, random
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen
import json
from PIL import Image, ImageDraw

USER = os.environ.get('GITHUB_USER', 'RianaMalhotra')
OUT = os.environ.get('ROCKET_OUTPUT', 'assets/rocket.gif')
TOKEN = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')

def contribution_count():
    until = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    since = until - timedelta(days=7)
    query = '''query($login:String!, $from:DateTime!, $to:DateTime!) {
      user(login:$login) { contributionsCollection(from:$from, to:$to) {
        contributionCalendar { weeks { contributionDays { date contributionCount } } }
      } }
    }'''
    data = json.dumps({'query':query, 'variables':{'login':USER,'from':since.isoformat(),'to':until.isoformat()}}).encode()
    headers={'Authorization':'Bearer '+TOKEN,'Content-Type':'application/json','User-Agent':'profile-rocket'}
    req=Request('https://api.github.com/graphql',data=data,headers=headers,method='POST')
    with urlopen(req,timeout=25) as resp:
        payload=json.load(resp)
    if payload.get('errors') or not payload.get('data',{}).get('user'):
        raise RuntimeError('GitHub contribution query failed: '+str(payload.get('errors')))
    days=[d for w in payload['data']['user']['contributionsCollection']['contributionCalendar']['weeks'] for d in w['contributionDays']]
    return sum(d['contributionCount'] for d in days if since.date().isoformat() <= d['date'] < until.date().isoformat())

W,H,S=300,125,3
BG=(31,25,57); MID=(64,48,111); CLOUD=(95,72,151)
random.seed(84)
stars=[(random.randrange(W),random.randrange(8,H-7),random.choice([1,1,1,2])) for _ in range(85)]

def rocket(d,x,y,flame):
    x,y=int(x),int(y)
    def poly(points,fill):d.polygon([(x+a,y+b) for a,b in points],fill=fill)
    def rect(coords,fill):d.rectangle((x+coords[0],y+coords[1],x+coords[2],y+coords[3]),fill=fill)
    black=(23,21,34)
    for j in range(flame):
        spread=int(2*math.sin(j*.65))
        rect((-j-6, -2+spread, -j-4, 2+spread), (255,175,66) if j<flame*.65 else (249,93,111))
    poly([(-4,-6),(0,-6),(0,6),(-4,6)],black)
    poly([(0,-7),(17,-7),(23,-4),(23,4),(17,7),(0,7)],black)
    poly([(1,-5),(16,-5),(21,-2),(21,2),(16,5),(1,5)],(228,234,245))
    rect((2,3,17,4),(184,199,226))
    poly([(20,-5),(27,0),(20,5)],black)
    poly([(20,-3),(25,0),(20,3)],(244,112,120))
    poly([(3,-6),(8,-12),(14,-12),(11,-6)],black)
    poly([(5,-7),(9,-10),(12,-10),(10,-7)],(218,83,112))
    poly([(3,6),(8,12),(14,12),(11,6)],black)
    poly([(5,7),(9,10),(12,10),(10,7)],(218,83,112))
    d.ellipse((x+10,y-4,x+18,y+4),fill=black)
    d.ellipse((x+12,y-2,x+16,y+2),fill=(115,194,229))
    rect((-2,-5,0,5),(111,108,133))

def make():
    count=contribution_count()
    print('Last seven complete UTC days:',count,'contributions')
    intensity=math.log1p(count)/math.log1p(35)
    speed=0.35+1.25*intensity
    frames=[]
    n=36
    for i in range(n):
        image=Image.new('RGB',(W,H),BG)
        d=ImageDraw.Draw(image)
        d.rectangle((0,42,W,H),fill=MID)
        d.ellipse((252,12,277,37),fill=(113,82,168))
        d.ellipse((258,16,272,30),fill=(162,114,194))
        offset=int(i*speed*1.8)
        for layer in range(4):
            yy=44+layer*12
            for j in range(-2,18):
                xx=(j*28-offset*(layer+1)//2)%(W+56)-28
                d.rectangle((xx,yy+(j*7+layer*3)%13,xx+26, yy+11+(j*7+layer*3)%13),fill=CLOUD if layer%2 else MID)
        for k,(sx,sy,sz) in enumerate(stars):
            xx=(sx-int(i*speed*(.7+sz*.5)))%W
            light=(235,226,255) if (i//4+k)%4 else (173,165,218)
            d.rectangle((xx,sy,xx+sz-1,sy+sz-1),fill=light)
            if sz==2:d.rectangle((xx-1,sy+1,xx+2,sy+1),fill=light)
        progress=(i/n)**max(0.55, 1.15-0.20*intensity)
        x=int(-36+(W+65)*progress)
        y=int(72+2*math.sin(i*.55))
        flicker=10+int(13*intensity)+int(5*abs(math.sin(i*1.5)))
        for p in range(12):
            px=x-12-(p*11+int(i*speed*4))%65
            py=y+int(6*math.sin(p*2+i*.5))
            if 0<=px<W and 0<=py<H:
                d.rectangle((px,py,px+1,py+1),fill=(255,164,128) if p%2 else (244,130,204))
        rocket(d,x,y,flicker)
        frames.append(image.resize((W*S,H*S),Image.Resampling.NEAREST))
    os.makedirs(os.path.dirname(OUT) or '.',exist_ok=True)
    frame_duration=max(30, round(140/(1+0.85*intensity)))
    print('Animation frame duration:',frame_duration,'ms; motion speed:',round(speed,2))
    frames[0].save(OUT,save_all=True,append_images=frames[1:],duration=frame_duration,loop=0,optimize=True,disposal=2)
    print('Wrote',OUT, 'bytes',os.path.getsize(OUT))

if __name__=='__main__':make()
