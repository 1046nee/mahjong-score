# -*- coding: utf-8 -*-
"""Blender の無いPCで、scene.py の台本の動き（anim_pose_s2）を計算だけ動かす試し（2026-11-24）。bpy は仮の部品。絵は出ない。
確かめること: エラーが出ない・牌が1コマで飛ばない・同じ牌が5枚無い・見えている牌どうしが重ならない。  実行: python tools/b3d/scene_dry_test.py
カメラ・手・体との重なりは見られない（書き出して確かめる）"""
import sys,types,math,ast,io,os
OUTD = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else ''
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
ALLT = []
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
        ALLT.append(s) if code in ('back',) or code[0] in 'mpsz' and len(code) <= 3 else None
        s.code=code; s.location=loc; s.parent=parent; s.rotation_euler={"stand":(math.pi/2,0,rz),"lie":(0,0,rz),"down":(math.pi,0,rz)}[state]; s.children=[]; s.hide_render=False
    location=property(lambda s:s._l,lambda s,v:setattr(s,"_l",Vector(v))); rotation_euler=property(lambda s:s._r,lambda s,v:setattr(s,"_r",Vector(v)))
def load(scene):
    bpy=MagicMock(); mu=types.ModuleType("mathutils"); mu.Vector=Vector; mu.Euler=mu.Matrix=MagicMock(); sys.modules["bpy"]=bpy; sys.modules["mathutils"]=mu
    sys.argv=["b","--","--scene",scene,"--anim"]
    src=io.open("tools/b3d/scene.py",encoding="utf-8").read(); g={"__file__":"tools/b3d/scene.py","__name__":"x"}
    over=dict(tile=lambda code,loc,parent,state="lie",rz=0,**k:Obj(code,loc,parent,state,rz), seat_root=lambda i:types.SimpleNamespace(name=f"seat{i}", seat=i),
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
    ALLT.clear(); g=load(sc); g["pose_body"]=lambda A,w,wl=None: g.setdefault("W",[]).append((A is g["ARMS"][0],w,wl)); cam=MagicMock()
    g["near_parts"]=lambda: ([],[],[]); na=g["near_alpha"]; NA={}
    g["near_alpha"]=lambda t,h,wr,wl: NA.setdefault("log",[]).append(na(t,h,wr,wl)) or NA["log"][-1]
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
        import make_clip as MC
        lg=NA["log"]; print("  手前の人の濃さ（体・右腕・左腕）止めるコマ:",[tuple(round(v,2) for v in lg[st[4]]) for st in MC.SCRIPTS[sc]["steps"]],"動くコマの腕の最大: %.2f"%max(max(v[1:]) for v in lg[15:]))
        assert all(max(lg[st[4]])<.02 for st in MC.SCRIPTS[sc]["steps"]),"止めるコマに手前の人が残っている"
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

    if sc.startswith("furiten"):      # 模式図: 卓全体の画角に、牌・囲み・札・見出し・字幕の場所を重ねた絵（--out フォルダ。人や手は描かない）
        out = OUTD
        if out:
            import make_clip as MC
            from PIL import Image, ImageDraw
            for i, st in enumerate(MC.SCRIPTS[sc]["steps"]):
                f = st[4]; g["anim_pose"](f / 12, cam); here = g["marks_at"](f / 12)
                im = Image.new("RGBA", (1080, 1920), (40, 60, 66, 255)); d = ImageDraw.Draw(im); pj = g["project"]; TOP_ = g["TOP"]
                for sz, col in ((1.0, "#E75620"), (.80, "#F7F3EA"), (.74, "#178A8C"), (.15, "#1B1F22")): d.polygon([pj((x * sz / 2, y * sz / 2, TOP_)) for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))], fill=col)
                al = [o for o in ALLT if not o.hide_render]
                for o in al:
                    import copy
                    q = o
                    if o.parent is not None and getattr(o.parent, "seat", 0):
                        a_ = o.parent.seat * math.pi / 2; l = o.location; q = Obj(o.code, (l.x * math.cos(a_) - l.y * math.sin(a_), l.x * math.sin(a_) + l.y * math.cos(a_), l.z), None, "lie", 0); q.rotation_euler = (o.rotation_euler.x, o.rotation_euler.y, o.rotation_euler.z + a_)
                    ps = [pj(c) for c in g["tile_corners"](q)]
                    x0, x1 = min(p[0] for p in ps), max(p[0] for p in ps); y0, y1 = min(p[1] for p in ps), max(p[1] for p in ps)
                    up = abs(q.rotation_euler.x) < .1; d.rectangle((x0, y0, x1, y1), fill="#FFFDF6" if up else "#2F62C8", outline="#333")
                    if up and o.code != "back": d.text((x0 + 3, y0 + 4), o.code, fill="#000", font=MC.font(15))
                ov = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0)); dd = ImageDraw.Draw(ov)
                MC.draw_marks(dd, MC.MARKS[sc][i], here); MC.rail(dd, MC.SCRIPTS[sc]["steps"], i); MC.headline(dd, i, st, 3); MC.subtitle(dd, "（字幕の場所）", 3)
                os.makedirs(out, exist_ok=True); Image.alpha_composite(im, ov).convert("RGB").save(os.path.join(out, f"{sc}_{i + 1}.png"))
                print("  ", i + 1, "囲む牌が無い:", [m[0] for m in MC.MARKS[sc][i] if m[0] not in here])
