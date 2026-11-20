# Paths in this folder point at /tmp/gsb work files from the Nov 2026 cut; adjust SRC/paths before re-running.
"""Render a tracked, gently cropped clip from the GSB wide shot.
usage: render.py START END OUT [W H]   (seconds in the original)"""
import cv2, numpy as np, subprocess, sys, os, tempfile, glob
SRC="/sessions/sleepy-gifted-thompson/mnt/academic-website/reel-source/Stanford GSB Workshop.mp4"
s,e,out=float(sys.argv[1]),float(sys.argv[2]),sys.argv[3]
CW,CH=(int(sys.argv[4]),int(sys.argv[5])) if len(sys.argv)>5 else (1440,810)
Y0=175                                     # crop top: keeps the lower half of the screens, him, and the front desk
d=tempfile.mkdtemp(dir="/tmp/gsb")
# 1) track at 2 fps: background-subtracted motion in the stage band
pad=6; ts=max(0,s-pad)
subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-ss",str(ts),"-t",str(e-ts+pad),"-i",SRC,"-vf","fps=2,crop=1920:560:0:300,scale=960:280","-q:v","4",f"{d}/t%05d.jpg"],check=True)
fs=sorted(glob.glob(f"{d}/t*.jpg"))
st=np.stack([cv2.cvtColor(cv2.imread(f),cv2.COLOR_BGR2GRAY) for f in fs]).astype(np.float32)
bg=np.median(st,axis=0); xs=[]
for g in st:
    m=(np.abs(g-bg)>28).astype(np.float32)[55:200,:]; m[:,:210]=0; m[:,780:]=0
    c=np.convolve(m.sum(0),np.ones(41)/41,mode="same")
    xs.append(np.argmax(c)*2 if c.max()>3 else np.nan)
xs=np.array(xs,dtype=float)
# fill gaps, median filter, then heavy smoothing (slow, steady pan)
idx=np.arange(len(xs)); ok=~np.isnan(xs)
xs=np.interp(idx,idx[ok],xs[ok]) if ok.any() else np.full(len(xs),960.0)
xs=np.array([np.median(xs[max(0,i-3):i+4]) for i in range(len(xs))])
k=9; xs=np.convolve(np.pad(xs,(k,k),mode="edge"),np.ones(2*k+1)/(2*k+1),mode="valid")
cx=np.clip(xs-CW/2,0,1920-CW)
times=ts+idx/2.0
# keep only the part inside [s,e]; express crop x as a piecewise-linear function of output time t
sel=(times>=s-0.5)&(times<=e+0.5); tt=times[sel]-s; xx=cx[sel]
pts=list(zip(tt[::2],xx[::2]))       # one key per second
expr=f"{pts[-1][1]:.1f}"
for (t0,x0),(t1,x1) in reversed(list(zip(pts[:-1],pts[1:]))):
    expr=f"if(lt(t,{t1:.2f}),{x0:.1f}+({x1-x0:.1f})*(t-{t0:.2f})/{max(t1-t0,0.01):.2f},{expr})"
vf=f"fps=30,crop={CW}:{CH}:'{expr}':{Y0},scale=1920:1080:flags=lanczos,format=yuv420p"
open(f"{d}/vf.txt","w").write(vf)
subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-ss",str(s),"-t",str(e-s),"-i",SRC,"-filter_script:v",f"{d}/vf.txt",
                "-c:v","libx264","-preset","veryfast","-crf","20","-c:a","aac","-b:a","160k","-ac","2","-ar","48000",out],check=True)
print("ok",out,len(pts),"keys")
