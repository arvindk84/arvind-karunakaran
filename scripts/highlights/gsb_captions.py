# Paths in this folder point at /tmp/gsb work files from the Nov 2026 cut; adjust SRC/paths before re-running.
# Captions for the GSB workshop highlights. Text: YouTube automatic transcript, cleaned (fillers like "uh" and
# discourse "like" dropped, stutters removed, ASR fixes: "Taiwan" -> "tier-one", "Jans" -> "Jevons" not used,
# "strong bond" -> "strong bundle"). Times: original-recording seconds of each cue's first word.
import subprocess, sys
SEGS=[("A",9225.25),("B",9305.32),("C",9534.16),("C2b",9611.50),("C3",9653.88),("D",9727.78)]
ENDS={"A":9256.36,"B":9375.32,"C":9604.69,"C2b":9636.28,"C3":9673.78,"D":9769.64}
CUES={
"A":[(9225.28,"So start with the workflow, right?"),(9226.88,"Start with what is the workflow, or workflows,"),(9228.80,"two or three, that you're really trying to re-engineer,"),
     (9232.88,"because that is where the value is."),(9234.24,"The workflow touches on different roles and functions."),
     (9237.52,"So if you identify, this is a workflow that I'm really going to make better,"),(9241.28,"and your product is in service of making that workflow better,"),
     (9244.96,"then you'll have a lot more clarity on what needs to change:"),(9247.76,"what incentives, what job roles need to change."),
     (9251.04,"So I would think almost like a workflow mindset, right?"),(9254.48,"And having your own playbooks around that.")],
"B":[(9305.68,"So if the transformation unit is only constituted by executives"),(9311.92,"and technologists, like AI experts, then it is not going well,"),
     (9316.48,"because they don't really even have visibility into"),(9318.88,"what workflows they try to optimize, what job roles are implicated."),
     (9322.72,"But if the transformation team is very multidisciplinary,"),(9326.24,"you have domain experts, your end users,"),
     (9328.64,"at least one or two representatives from each role implicated in that workflow."),(9333.52,"And more importantly, what we have found is"),
     (9335.68,"if the transformation team, or the center of excellence, has work design experts,"),(9340.24,"think of your Six Sigma black belt type of people,"),
     (9343.36,"not process-obsessed people, right?"),(9345.28,"Because that's also another warning, right?"),(9347.76,"If they're too process-obsessed, that's not great."),
     (9349.84,"But they should have an inclination towards understanding"),(9352.80,"work and workflow as a system,"),
     (9356.08,"and how do you go about redesigning the system, redesigning the work itself?"),(9360.24,"That makes a huge difference."),
     (9361.44,"They think of it from that workflow redesign perspective"),(9364.40,"rather than just a technology adoption, or this build versus buy,"),
     (9368.32,"a classic CIO, IT department perspective, right?"),(9371.76,"Like, a work redesign perspective. So that works.")],
"C":[(9534.24,"So the idea of a bundle is: if you think of a job as a bundle of tasks,"),(9538.72,"there is a glue that holds the different tasks together."),
     (9541.92,"Say if you're a coder, there are certain tasks you do."),(9544.72,"If you're an M&A lawyer, there are certain tasks you do."),
     (9547.60,"If you're a radiologist, you do certain tasks."),(9550.24,"Some of those jobs, the glue is very strong."),
     (9552.88,"In other words, you have to be good at task A to be good at task B,"),(9557.04,"to be good at task C, even if AI is getting better at task A, right?"),
     (9561.20,"So that's an idea of a strong bundle. In other words, the glue is very strong."),
     (9566.32,"Whereas there are certain other jobs where the glue is very weak."),(9568.96,"There are only three or four tasks that particular individual does."),
     (9571.84,"The tasks are loosely related. You don't need to be good at task A"),(9574.80,"to be good at task B, right?"),
     (9576.24,"So what would be the examples? Like a radiologist."),(9580.16,"Remember Geoff Hinton's famous prediction in 2016"),
     (9583.92,"that you don't need to train radiologists anymore because AI is getting better."),(9587.52,"Not only did it turn out not to be true,"),
     (9590.16,"or at least one part of his prediction came true."),(9593.44,"The AI capabilities improved in interpreting these scans,"),
     (9597.20,"but the other part of the message, that you don't need to train radiologists,"),(9600.40,"or there's going to be less demand for them, did not come out to be true.")],
"C2b":[(9611.52,"The most important reason is the job of a radiologist is a strong one."),(9616.00,"In other words, you had to do at least some"),
     (9618.80,"of the interpreting of the scans yourself to do your other tasks:"),(9623.04,"talk to the attendings, train the residents, talk to the patients."),
     (9626.56,"So if you try to unbundle a job that has a strong glue,"),(9630.80,"we have found time and again through empirical research that it's not going well."),
     (9634.00,"The performance of that person suffers, right?")],
"C3":[(9653.92,"Think of a job as a medical transcriptionist"),(9657.12,"or a tier-one customer support agent."),(9659.60,"That's a job where the glue is weak, right?"),
     (9661.92,"They do some tasks. They're loosely related."),(9664.56,"Those types of tasks you can really redesign, right, between human and AI."),
     (9668.80,"You can completely rethink, reimagine those jobs,"),(9671.68,"sometimes consolidate two roles into one.")],
"D":[(9727.92,"You have to think about how do you do the chaining between human and AI."),(9732.32,"Think of it as a speed breaker on a street, right? On a highway,"),
     (9736.16,"if you have a speed breaker every 10 meters, it's not helpful."),(9739.04,"You're really in a bumpy ride."),
     (9741.28,"But if you have a speed breaker every 300 miles, that's also not useful, right?"),
     (9745.76,"Here, the speed breaker is when should the human intervene and verify, right?"),(9749.44,"That's the speed breaker."),
     (9750.88,"So you had to architect that, what we call a chain, right?"),(9754.40,"Or think of it as a seam, say in your clothes or your pants."),
     (9758.72,"How are you designing that seam?"),(9760.40,"In other words, when should the human intervene, verify, give feedback,"),
     (9764.72,"and architect that loop?"),(9766.40,"That matters too when you're trying to redesign job roles.")],
}
def dur(f): return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f],capture_output=True,text=True).stdout)
def two_lines(t):
    if len(t)<=42: return t
    w=t.split(); best=None
    for i in range(1,len(w)):
        a,b=" ".join(w[:i])," ".join(w[i:]); s=max(len(a),len(b))+(0 if a[-1] in ",.?;:" else 4)
        if best is None or s<best[0]: best=(s,a,b)
    return best[1]+"\n"+best[2]
def ts(x): return f"{int(x//3600):02d}:{int(x%3600//60):02d}:{x%60:06.3f}"
off=0; out=["WEBVTT","","NOTE Arvind Karunakaran, workshop at Stanford GSB (Nov 9, 2026), highlights. Captions from YouTube's automatic transcript, cleaned; review before publishing.",""]
n=1
for seg,t_in in SEGS:
    d=dur(f"/tmp/gsb/fin/{seg}.mp4"); cs=CUES[seg]
    for i,(t,txt) in enumerate(cs):
        a=off+max(0,t-t_in-0.05); b=off+((cs[i+1][0]-t_in-0.05) if i+1<len(cs) else (ENDS[seg]-t_in))
        b=min(b, off+d-0.02)
        out+=[str(n),f"{ts(a)} --> {ts(b)}",two_lines(txt),""]; n+=1
    off+=d
open(sys.argv[1],"w",encoding="utf-8").write("\n".join(out)); print(n-1,"cues; total",round(off,2))
