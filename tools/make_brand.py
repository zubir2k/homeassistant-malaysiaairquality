from PIL import Image, ImageDraw, ImageFont
import math
COLS=["#1E5AC8","#2E9E44","#F2C200","#F07C00","#D0021B"]
def icon(size, wave="#37474F"):
    S=size*4; im=Image.new("RGBA",(S,S),(0,0,0,0)); d=ImageDraw.Draw(im)
    cx,cy=S/2,S*0.56; r=S*0.40; w=S*0.105
    start,span=150,240; gap=5; seg=(span-gap*4)/5
    for i,c in enumerate(COLS):
        a0=start+i*(seg+gap); a1=a0+seg
        d.arc([cx-r,cy-r,cx+r,cy+r],a0,a1,fill=c,width=int(w))
        # round caps on ends of whole gauge
        for a,end in ((a0,i==0),(a1,i==4)):
            if end:
                rr=r-w/2; x=cx+rr*math.cos(math.radians(a)); y=cy+rr*math.sin(math.radians(a))
                d.ellipse([x-w/2,y-w/2,x+w/2,y+w/2],fill=c)
    # haze waves
    lw=int(S*0.048)
    for k,(yo,half) in enumerate([(-0.10,0.22),(0.0,0.26),(0.10,0.18)]):
        y0=cy+S*yo; pts=[]
        x_start=cx-S*half; x_end=cx+S*half
        n=120
        for j in range(n+1):
            x=x_start+(x_end-x_start)*j/n
            y=y0+S*0.022*math.sin((j/n)*2*math.pi*1.5+k)
            pts.append((x,y))
        dense=[]
        for j in range(len(pts)-1):
            (x0,y0_),(x1,y1)=pts[j],pts[j+1]
            for t in range(8): dense.append((x0+(x1-x0)*t/8,y0_+(y1-y0_)*t/8))
        dense.append(pts[-1])
        for p in dense:
            d.ellipse([p[0]-lw/2,p[1]-lw/2,p[0]+lw/2,p[1]+lw/2],fill=wave)
    im=im.resize((size,size),Image.LANCZOS)
    return im.crop(im.getbbox()).resize((size,size),Image.LANCZOS) if False else im
def trimmed_square(im,size):
    b=im.crop(im.getbbox()); w,h=b.size; m=max(w,h)
    c=Image.new("RGBA",(m,m),(0,0,0,0)); c.paste(b,((m-w)//2,(m-h)//2)); return c.resize((size,size),Image.LANCZOS)
def logo(h, text, sub, wave):
    S=4; H=h*S
    ic=trimmed_square(icon(1024,wave),H)
    fb=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",int(H*0.40))
    fr=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",int(H*0.26))
    t1="Air Quality"; t2="MALAYSIA"
    w1=fb.getbbox(t1)[2]; w2=fr.getbbox(t2)[2]
    W=H+int(H*0.15)+max(w1,w2)
    im=Image.new("RGBA",(W,H),(0,0,0,0)); im.paste(ic,(0,0),ic); d=ImageDraw.Draw(im)
    x=H+int(H*0.15)
    d.text((x,int(H*0.10)),t2,font=fr,fill=sub)
    d.text((x,int(H*0.42)),t1,font=fb,fill=text)
    im=im.crop(im.getbbox())
    return im.resize((im.width//S,im.height//S),Image.LANCZOS)
trimmed_square(icon(1024),256).save("icon.png"); trimmed_square(icon(2048),512).save("icon@2x.png")
for scale,suf in ((1,""),(2,"@2x")):
    logo(128*scale,"#263238","#607D8B","#37474F").save(f"logo{suf}.png")
    logo(128*scale,"#FFFFFF","#B0BEC5","#ECEFF1").save(f"dark_logo{suf}.png")
    trimmed_square(icon(1024*scale,"#ECEFF1"),256*scale).save(f"dark_icon{suf}.png")
# preview
pv=Image.new("RGB",(1100,520),"white"); dk=Image.new("RGB",(1100,260),"#1c1c1c")
for name,bg,y in (("icon.png",pv,20),): pass
i=Image.open("icon.png"); pv.paste(i,(20,10),i)
l=Image.open("logo.png"); pv.paste(l,(320,70),l)
di=Image.open("dark_icon.png"); dl=Image.open("dark_logo.png")
dk.paste(di,(20,2),di); dk.paste(dl,(320,70),dl); pv.paste(dk,(0,260))
s=Image.open("icon.png").resize((32,32),Image.LANCZOS); pv.paste(s,(1040,20),s)
pv.save("/workspace/work/brand_preview.png")
