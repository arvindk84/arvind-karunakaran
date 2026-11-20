# Paths in this folder point at /tmp/gsb work files from the Nov 2026 cut; adjust SRC/paths before re-running.
import subprocess, json, sys, re
OV="/tmp/gsb/ov"
clips={"A":[("lower-third",0.4,5.4),("tag-workflow",5.8,9.8)],"B":[("tag-team",0.4,4.4)],"C":[("tag-bundles",0.4,4.4)],"C2b":[],"C3":[],"D":[("tag-chains",0.4,4.4)]}
order=["A","B","C","C2b","C3","D"]
def dur(f): return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f],capture_output=True,text=True).stdout)
def enc(name):
    src=f"/tmp/gsb/hl/{name}.mp4"; d=dur(src); out=f"/tmp/gsb/fin/{name}.mp4"
    # loudness: first pass
    p=subprocess.run(["ffmpeg","-hide_banner","-i",src,"-vn","-af","loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json","-f","null","-"],capture_output=True,text=True).stderr
    m=json.loads(p[p.rfind("{"):p.rfind("}")+1])
    ln=f"loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true"
    inputs=["-i",src]; parts=["[0:v]null[v0]"]; cur="v0"
    for k,(png,a,b) in enumerate(clips[name]):
        inputs+=["-loop","1","-t",f"{d:.3f}","-i",f"{OV}/{png}.png"]
        parts.append(f"[{k+1}:v]format=rgba,fade=t=in:st={a}:d=0.3:alpha=1,fade=t=out:st={b-0.3}:d=0.3:alpha=1[o{k}]")
        parts.append(f"[{cur}][o{k}]overlay=0:0:enable='between(t,{a},{b})'[v{k+1}]"); cur=f"v{k+1}"
    vf=[]
    if name==order[0]: vf.append("fade=t=in:st=0:d=0.4")
    if name==order[-1]: vf.append(f"fade=t=out:st={d-0.7:.3f}:d=0.7")
    parts.append(f"[{cur}]{','.join(vf) if vf else 'null'},format=yuv420p[vout]")
    af=f"{ln},aresample=48000,afade=t=in:st=0:d={0.4 if name==order[0] else 0.06},afade=t=out:st={d-(0.7 if name==order[-1] else 0.08):.3f}:d={0.7 if name==order[-1] else 0.08}"
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-y",*inputs,"-filter_complex",";".join(parts),"-map","[vout]","-map","0:a","-af",af,
         "-c:v","libx264","-preset","fast","-crf","24","-r","30","-g","60","-c:a","aac","-b:a","128k","-ac","2","-t",f"{d:.3f}",out]
    subprocess.run(cmd,check=True); print("encoded",name,round(d,2))
for n in sys.argv[1:]: enc(n)
