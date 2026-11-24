# -*- coding: utf-8 -*-
"""Blender の無いPCで、scene.py の台本の動き（anim_pose_s2）を計算だけ動かす試し（2026-11-24）。bpy は仮の部品。絵は出ない。
確かめること: エラーが出ない・牌が1コマで飛ばない・同じ牌が5枚無い・見えている牌どうしが重ならない。  実行: python tools/b3d/scene_dry_test.py
カメラ・手・体との重なりは見られない（書き出して確かめる）"""
import sys,types,math,ast,io
from unittest.mock import MagicMock
class Vector:
    def __init__(s,v=(0,0,0)):
        v=list(v); s.v=[float(x) for x in v]+[0.0]*(3-len(v))
    x=property(lambda s:s.v[0],lambda s,a:s.v.__setitem__(0,a)); y=property(lambda s:s.v[1],lambda s,a:s.v.__setitem__(1,a)); z=property(lambda s:s.v[2],lambda s,a:s.v.__setitem__(2,a))
    def __iter__(s): return iter(s.v)
    def __getitem__(s,i): return s.v[i]
    def __len__(s): return 3
    def __add__(s,o): return Vector(a+b for a,b in zip(s.v,o))
    def __sub__(s,o): return Vector(a-b for a,b in zip(s.v,o))
    def __mul__(s,k): return Vector(a*k for a in s.v)
    __rmul__=__mul__
    def lerp(s,o,k): return Vector(a+(b-a)*k for a,b in zip(s.v,o))
    length=property(lambda s:math.sqrt(sum(a*a for a in s.v)))
    def normalized(s): return s*(1/s.length)
    def to_track_quat(s,*a): return MagicMock()
    def copy(s): return Vector(s.v)
class Obj(dict):
    def __init__(s,code,loc,parent,state,rz): 
        s.code=code; s.location=loc; s.parent=parent; s.rotation_euler={"stand":(math.pi/2,0,rz),"lie":(0,0,rz),"down":(math.pi,0,rz)}[state]; s.children=[]; s.hide_render=False
    location=property(lambda s:s._l,lambda s,v:setattr(s,"_l",Vector(v))); rotation_euler=property(lambda s:s._r,lambda s,v:setattr(s,"_r",Vector(v)))
def load(scene):
    bpy=MagicMock(); mu=types.ModuleType("mathutils"); mu.Vector=Vector; mu.Euler=mu.Matrix=MagicMock(); sys.modules["bpy"]=bpy; sys.modules["mathutils"]=mu
    sys.argv=["b","--","--scene",scene,"--anim"]
    src=io.open("tools/b3d/scene.py",encoding="utf-8").read(); g={"__file__":"tools/b3d/scene.py","__name__":"x"}
    over=dict(tile=lambda code,loc,parent,state="lie",rz=0,**k:Obj(code,loc,parent,state,rz), seat_root=lambda i:types.SimpleNamespace(name=f"seat{i}"),
      build_player=lambda i,P:{"R":{"rest":Vector((.2,-.5,.8))},"L":{"rest":Vector((-.2,-.5,.8))}}, build_venue=lambda:None, build_table=lambda:None, box=lambda n,s,loc=(0,0,0),*a,**k:Obj(n,loc,None,"lie",0), sphere=lambda *a,**k:None)
    for n in ast.parse(src).body:
        if isinstance(n,(ast.FunctionDef,ast.Import,ast.ImportFrom,ast.Assign,ast.AugAssign)) or (isinstance(n,ast.If) and "ANIM" not in ast.unparse(n.test)) or (isinstance(n,ast.Expr) and "build_venue" in ast.unparse(n)):
            if isinstance(n,ast.FunctionDef) and n.name in over: g[n.name]=over[n.name]; continue
            try: exec(compile(ast.Module([n],[]),"s","exec"),g)
            except SystemExit: raise
            except Exception as e:
                if n.lineno>355 and n.lineno<1100: print("skip",n.lineno,repr(e)[:90])
    return g
import collections
for sc in ["furiten","furiten2","furiten3","riichi","dahai","kakan"]:
    g=load(sc); g["pose_body"]=lambda A,w,wl=None: g.setdefault("W",[]).append((A is g["ARMS"][0],w,wl)); cam=MagicMock()
    g["anim_setup"]()
    N=g["NAMED"]; d=g["ANIM_DUR"]; nf=int(d*12)
    prev={}; mj=0; worst=None
    for f in range(nf):
        g["anim_pose"](f/12,cam)
        for k,o in N.items():
            if k in prev and not o.hide_render and not prev[k][1]:
                j=(Vector(o.location)-prev[k][0]).length
                if j>mj: mj=j; worst=(k,f)
            prev[k]=(Vector(o.location),o.hide_render)
    print(sc,"frames",nf,"max jump/frame %.3f"%mj,worst)
    if sc.startswith("furiten"):
        cnt=collections.Counter(o.code for k,o in N.items() if not k.startswith("h1") and o.code!="back")
        vis=sum(g["RIVERS"],[])+g["HANDS"][0]+g["MELD0"]+[g["DORA"]]+[c for c in (g["NEXT_CODE"],g["NEXT2_CODE"]) if c!="back"]
        print("  4枚超:",{k:v for k,v in collections.Counter(vis).items() if v>4})
        # 最後の位置が河の升に重ならないか（見えている牌どうしの距離）
        L=[(k,o.location) for k,o in N.items() if not o.hide_render and not k.startswith("rin") and not (k.startswith("h") and k[1:2].isdigit())]
        seen=set()
        for i,(a,pa) in enumerate(L):
            for b,pb in L[i+1:]:
                if N[a] is not N[b] and (pa-pb).length<.02: print("  近い",a,b,round((pa-pb).length,4))
        for k in ("o1","o2","o3","o4","o5","o6","called","next","next2"):
            if k in N: print("  ",k,N[k].code,[round(v,3) for v in N[k].location],[round(v,2) for v in N[k].rotation_euler])
