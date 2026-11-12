# -*- coding: utf-8 -*-
"""3Dの対局の土台（2026-11-11〜・ユーザーの依頼）。Blender（bpy）で、会場・卓・牌・選手4人・カメラを作る。
  <bpyの入ったpython> tools/b3d/scene.py --tex <牌の絵のフォルダ> --out <出力フォルダ> [--theme dark|green] [--cams wide,mid,...] [--size 720x1280] [--samples 48]
- 牌の絵は tools/b3d/make_tile_tex.py で作る（まじゃすこの牌の表の面）
- 選手は実在の人の顔を写さない。髪の色と形・体格・ユニフォームの配色（4色まで）だけで「それらしさ」を出す。名前・ロゴ・実物の柄は使わない
- 席: 0=手前（南）・1=右・2=奥・3=左。各席の中身は「手前の席の座標」で作って、Z軸で90度ずつ回す
"""
import bpy, math, os, sys, random
from mathutils import Vector, Euler, Matrix

def arg(name, default):
    a = sys.argv
    return a[a.index(name) + 1] if name in a else default
TEX = arg("--tex", "")
OUT = arg("--out", ".")
THEME = arg("--theme", "dark")
CAMS = arg("--cams", "wide,mid,hand,top,meld").split(",")
SIZE = [int(x) for x in arg("--size", "720x1280").split("x")]
SAMPLES = int(arg("--samples", "48"))
FACE = arg("--face", "nm")   # nm＝目・鼻・口（今の決まり。2026-11-12 ユーザーの判断）／eyes＝目だけ
ANIM = "--anim" in sys.argv      # 動きの試し（チーの5つの手順）。1コマずつ書き出す。途中で止まっても、できたコマは飛ばして続きから
FPS = int(arg("--fps", "12"))
STEP = 0 if ANIM else int(arg("--step", "4"))   # 鳴きの手順のどこまで進んだか（0=鳴く前 … 5=打牌まで）

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
col = sc.collection
random.seed(7)

# ---------------- 材質 ----------------
def hexc(h):
    h = h.lstrip("#"); r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda v: v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4   # sRGB → リニア
    return (f(r), f(g), f(b), 1)

_mats = {}
def mat(name, color, rough=.5, emit=0.0, metal=0.0):
    if name in _mats: return _mats[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    c = hexc(color) if isinstance(color, str) else color
    p.inputs["Base Color"].default_value = c
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if emit:
        p.inputs["Emission Color"].default_value = c
        p.inputs["Emission Strength"].default_value = emit
    _mats[name] = m
    return m

def tex_mat(code):
    name = "face_" + code
    if name in _mats: return _mats[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    path = os.path.join(TEX, code + ".png")
    if os.path.exists(path):
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path, check_existing=True)
        nt.links.new(t.outputs["Color"], p.inputs["Base Color"])
    else:
        p.inputs["Base Color"].default_value = hexc("#FFFDF6")
    p.inputs["Roughness"].default_value = .25
    _mats[name] = m
    return m

def pattern_mat(name, kind, cols):
    """ユニフォームの柄（実物の柄ではなく、配色だけ）。kind: zigzag / camo / lines / check / plain"""
    if name in _mats: return _mats[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]; p.inputs["Roughness"].default_value = .7
    tc = nt.nodes.new("ShaderNodeTexCoord")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cs = [hexc(c) for c in cols]
    el = ramp.color_ramp.elements
    while len(el) < len(cs): el.new(.5)
    for i, c in enumerate(cs):
        el[i].position = i / len(cs); el[i].color = c
    ramp.color_ramp.interpolation = "CONSTANT"
    if kind == "zigzag":
        w = nt.nodes.new("ShaderNodeTexWave"); w.wave_type = "BANDS"; w.bands_direction = "DIAGONAL"
        w.inputs["Scale"].default_value = 3.2; w.inputs["Distortion"].default_value = 6.0; w.inputs["Detail"].default_value = 0.0; w.inputs["Detail Scale"].default_value = .6
        nt.links.new(tc.outputs["Object"], w.inputs["Vector"]); nt.links.new(w.outputs["Fac"], ramp.inputs["Fac"])
    elif kind == "camo":
        n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 9.0; n.inputs["Detail"].default_value = 1.0
        nt.links.new(tc.outputs["Object"], n.inputs["Vector"]); nt.links.new(n.outputs["Fac"], ramp.inputs["Fac"])
        for i in range(len(cs)): el[i].position = .36 + i * .1
    elif kind == "lines":
        w = nt.nodes.new("ShaderNodeTexWave"); w.wave_type = "BANDS"; w.bands_direction = "DIAGONAL"
        w.inputs["Scale"].default_value = 2.2; w.inputs["Distortion"].default_value = 0.0
        nt.links.new(tc.outputs["Object"], w.inputs["Vector"]); nt.links.new(w.outputs["Fac"], ramp.inputs["Fac"])
        el[0].position = 0;
        for i in range(1, len(cs)): el[i].position = .86 + (i - 1) * .06
    elif kind == "check":     # 地の色に、市松の模様がところどころ入る（色1=地・色2=市松の明るい色・色3=差し色）
        ck = nt.nodes.new("ShaderNodeTexChecker"); ck.inputs["Scale"].default_value = 42.0
        ck.inputs["Color1"].default_value = cs[1]; ck.inputs["Color2"].default_value = cs[0]
        n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 4.0; n.inputs["Detail"].default_value = 0.0
        mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = .56; mr.inputs["From Max"].default_value = .58
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.inputs["A"].default_value = cs[0]
        for a_, b_ in ((tc.outputs["Object"], ck.inputs["Vector"]), (tc.outputs["Object"], n.inputs["Vector"]), (n.outputs["Fac"], mr.inputs["Value"]),
                       (mr.outputs["Result"], mx.inputs["Factor"]), (ck.outputs["Color"], mx.inputs["B"]), (mx.outputs["Result"], p.inputs["Base Color"])):
            nt.links.new(a_, b_)
        _mats[name] = m; return m
    else:
        p.inputs["Base Color"].default_value = cs[0]; _mats[name] = m; return m
    nt.links.new(ramp.outputs["Color"], p.inputs["Base Color"])
    _mats[name] = m
    return m

# ---------------- 形 ----------------
def add(obj):
    col.objects.link(obj); return obj

def box(name, size, loc, m, bevel=0.0, rot=(0, 0, 0), parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = size
    o.data.materials.append(m)
    if bevel:
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        b = o.modifiers.new("bevel", "BEVEL"); b.width = bevel; b.segments = 4
        for poly in o.data.polygons: poly.use_smooth = True
    if parent: o.parent = parent
    return o

def sphere(name, r, loc, m, scale=(1, 1, 1), parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=32, ring_count=16)
    o = bpy.context.object; o.name = name; o.scale = scale; o.data.materials.append(m)
    for poly in o.data.polygons: poly.use_smooth = True
    if parent: o.parent = parent
    return o

def set_limb(o, a, b):
    a, b = Vector(a), Vector(b); d = b - a
    o.location = (a + b) / 2; o.scale = (1, 1, d.length)
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()

def limb(name, a, b, r, m, parent=None):
    """a→b の円柱（腕）"""
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=1, vertices=20)
    o = bpy.context.object; o.name = name
    set_limb(o, a, b)
    o.data.materials.append(m)
    for poly in o.data.polygons: poly.use_smooth = True
    if parent: o.parent = parent
    return o

UA_LEN, FA_LEN = .29, .27        # 上腕・前腕の長さ（固定。腕を伸び縮みさせない）
def ik_elbow(sh, w, pole):
    """肩 sh と手首 w から、ひじの位置を決める（2本の骨の長さは固定・ひじは pole の向きに曲がる）"""
    d = w - sh; D = max(abs(UA_LEN - FA_LEN) + 1e-4, min(d.length, (UA_LEN + FA_LEN) * .999))
    n = d.normalized() if d.length > 1e-6 else Vector((0, 1, 0))
    a = (UA_LEN ** 2 - FA_LEN ** 2 + D * D) / (2 * D)
    h = math.sqrt(max(0.0, UA_LEN ** 2 - a * a))
    p = pole - n * pole.dot(n)
    p = p.normalized() if p.length > 1e-6 else Vector((1, 0, 0))
    return sh + n * a + p * h

def pose_arm(A, sh, w):
    """腕1本を、肩 sh・手首 w の位置に合わせる。ひじは外・後ろ・下へ曲がる。手は前腕の向きに向ける"""
    sh, w = Vector(sh), Vector(w)
    el = ik_elbow(sh, w, Vector((.55 * A["sx"], -.45, -.7)))
    if el.y > -.50: el.z = max(el.z, TOP + .07)          # 卓の上では、ひじを卓にめりこませない
    set_limb(A["ua"], sh, el); set_limb(A["fa"], el, w)
    A["eb"].location = el; A["shd"].location = sh; A["hand"].location = w
    A["hand"].rotation_euler = (w - el).to_track_quat("Y", "Z").to_euler()

def pose_body(B, w_right):
    """右手の行き先に合わせて、腕が届かない分だけ上体を前に倒す（腕を棒のように伸ばさない）。左腕は休みの位置のまま肩だけ付いていく"""
    R, L = B["R"], B["L"]
    w = Vector(w_right)
    need = max(0.0, (w - R["sh"]).length - (UA_LEN + FA_LEN) * .92)
    k = min(need, .16)      # 倒しすぎると、大きな頭が左肩の上のカメラをふさぐ（.40 で画面が真っ黒になった）
    d = w - R["sh"]; d.z = 0
    d = d.normalized() if d.length > 1e-6 else Vector((0, 1, 0))
    lean = d * k + Vector((0, 0, -.22 * k))
    ang = math.atan2(k, .34)
    B["torso"].rotation_euler = (B["torso_rx"] - ang, 0, -.5 * ang * d.x)
    B["torso"].location = B["torso_loc"] + Vector((lean.x * .45, lean.y * .45, lean.z * .4))
    B["collar"].location = B["collar_loc"] + lean * .9
    B["head"].location = B["head_loc"] + lean * .95
    B["head"].rotation_euler = (math.radians(8) + ang * .35, 0, 0)
    pose_arm(R, R["sh"] + lean, w)
    pose_arm(L, L["sh"] + lean * .6, L["rest"])

def empty(name, parent=None):
    e = bpy.data.objects.new(name, None); add(e)
    if parent: e.parent = parent
    return e

# ---------------- 牌 ----------------
TS = 1.2                                 # 牌の大きさの倍率（本物は1.0。小さくて絵が読めなかったので大きく作る。1.35 は大きすぎた→1.2。2026-11-12 ユーザーの依頼）
TW, TL, TT = 0.024 * TS, 0.032 * TS, 0.017 * TS      # 幅・長さ・厚み（m）
HP = TW + .0006                          # 手牌のとなりとの間隔
HX0 = -6 * HP - .03                      # 席0の手牌（13枚）の左端の中心
RP = TW + .003                           # 河のとなりとの間隔
RX0 = -2.5 * RP                          # 河の1枚目の中心（6枚で折り返す）
RY, WY, HY = -.118, -.215, -.335         # 河・山・手牌の位置（手前の席の座標の y）。手牌と山のあいだは、倒した牌1枚（TL）が入る広さにする（-.255/-.318 だと、晒した牌が山の下にもぐった）
BACK = {"dark": "#2F62C8", "green": "#177083"}[THEME]   # 牌の背の色
_tile_mesh = {}
def tile_mesh(code):
    """寝かせた牌（表が上・絵の上が +Y）。白い本体＋背の色の層＋表の絵の面"""
    if code in _tile_mesh: return _tile_mesh[code]
    hw, hl = TW / 2, TL / 2
    zb = TT * .32
    V = [(-hw, -hl, 0), (hw, -hl, 0), (hw, hl, 0), (-hw, hl, 0),           # 0-3 底
         (-hw, -hl, zb), (hw, -hl, zb), (hw, hl, zb), (-hw, hl, zb),       # 4-7 背の層の上
         (-hw, -hl, TT), (hw, -hl, TT), (hw, hl, TT), (-hw, hl, TT)]       # 8-11 表
    F = [(3, 2, 1, 0), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7),     # 背の層
         (4, 5, 9, 8), (5, 6, 10, 9), (6, 7, 11, 10), (7, 4, 8, 11),               # 白い側面
         (8, 9, 10, 11)]                                                              # 表
    me = bpy.data.meshes.new("tile_" + code); me.from_pydata(V, [], F)
    me.materials.append(mat("tile_back", BACK, .35)); me.materials.append(mat("tile_white", "#FBF8EE", .3))
    me.materials.append(tex_mat(code) if code != "back" else mat("tile_white", "#FBF8EE", .3))
    for i, poly in enumerate(me.polygons):
        poly.material_index = 0 if i < 5 else (1 if i < 9 else 2)
    uv = me.uv_layers.new(name="UV")
    for poly in me.polygons:
        if poly.index == 9:
            for li, co in zip(poly.loop_indices, [(0, 0), (1, 0), (1, 1), (0, 1)]):
                uv.data[li].uv = co
    me.update()
    _tile_mesh[code] = me
    return me

def tile(code, loc, parent, pose="lie", rz=0.0, name=None):
    """pose: lie（表が上）/ stand（立てる・表が手前＝-Y）/ down（裏が上）"""
    o = bpy.data.objects.new(name or ("t_" + code), tile_mesh(code)); add(o); o.parent = parent
    x, y, z = loc
    if pose == "stand":
        o.rotation_euler = Euler((math.radians(90), 0, rz), "XYZ"); o.location = (x, y + TT, z + TL / 2)      # 底が z、表が -Y
    elif pose == "down":
        o.rotation_euler = Euler((math.radians(180), 0, rz), "XYZ"); o.location = (x, y, z + TT)
    else:
        o.rotation_euler = Euler((0, 0, rz), "XYZ"); o.location = (x, y, z)
    return o

# ---------------- 卓 ----------------
TOP = 0.76                 # フェルトの高さ
FELT = 0.74                # フェルトの1辺
def build_table():
    t = empty("table")
    body_col = {"dark": "#E75620", "green": "#F4F4F1"}[THEME]     # 暗い会場＝卓の側をまじゃすこのオレンジに／緑の背景＝白い卓
    felt_col = "#178A8C" if THEME == "dark" else "#1A8F86"
    box("tbl_body", (1.0, 1.0, .13), (0, 0, TOP - .071), mat("tbl_body", body_col, .35), bevel=.035, parent=t)
    box("tbl_felt", (FELT, FELT, .012), (0, 0, TOP - .006 + .0005), mat("felt", felt_col, .95), parent=t)
    box("tbl_rim", (FELT + .06, FELT + .06, .02), (0, 0, TOP - .0125), mat("tbl_rim", "#FFFFFF" if THEME == "green" else "#F7F3EA", .4), parent=t)
    box("console", (.15, .15, .012), (0, 0, TOP + .006), mat("console", "#1B1F22", .3, metal=.4), bevel=.004, parent=t)
    box("console_led", (.05, .05, .004), (0, 0, TOP + .014), mat("console_led", "#C8D8FF", .3, emit=1.5), parent=t)
    box("tbl_pole", (.14, .14, .62), (0, 0, .33), mat("pole", "#16181A", .4), parent=t)
    box("tbl_foot", (.62, .62, .04), (0, 0, .02), mat("pole", "#16181A", .4), bevel=.01, parent=t)
    for i in range(4):   # 点数の表示（赤いLEDの帯）。各席の右手前の側面
        e = empty(f"disp_piv{i}", t); e.rotation_euler = (0, 0, i * math.pi / 2)
        box(f"disp{i}", (.22, .008, .035), (.24, -.503, TOP - .05), mat("disp", "#101214", .3), parent=e)
        box(f"led{i}", (.16, .004, .016), (.24, -.5075, TOP - .05), mat("led_red", "#FF2A1A", .3, emit=4.0), parent=e)
    return t

# ---------------- 席ごとの牌 ----------------
def seat_root(i):
    e = empty(f"seat{i}"); e.rotation_euler = (0, 0, i * math.pi / 2); return e

HANDS = [
    ["p3", "p4", "p6", "p7", "p8", "s3", "s5", "s6", "s7", "s8", "s8", "m4", "m5"],     # 席0（鳴く人）。左から。六萬をチーして三索を切ると、二筒・五筒待ちのテンパイ（2026-11-13 ユーザーの指定）
    None, None, None,
]
RIVERS = [["z7", "z2", "s1"], ["z4", "p9", "m2"], ["s9", "z6", "p1"], ["z1", "m9", "z3", "m6"]]   # 席3（上家）の最後の六萬をチーする。枚数は巡目に合わせる（自分が3枚なら、上家は4枚目を切ったところ・ほかは3枚）。字牌と端の牌から切る、ふつうの序盤の河に
CALL_K = len(RIVERS[3]) - 1     # 鳴く牌が上家の河の何枚目か（0始まり）

def build_tiles():
    Z = TOP + .0005
    roots = [seat_root(i) for i in range(4)]
    named = {}
    for i, r in enumerate(roots):
        # 山（2段×13幢。手前の席から見て左右に）
        n = int((2 * (abs(WY) - TL / 2 - .012)) / (TW + .0008))      # 山の長さは、となりの席の山と角で重ならない数にする（牌の大きさから計算）
        x0 = -(n - 1) / 2 * (TW + .0008)
        for k in range(n):
            for lv in range(2):
                tile("back", (x0 + k * (TW + .0008), WY, Z + lv * TT), r, "down", rz=math.pi / 2 * 0)
        # 河（6枚で折り返す）
        rv = RIVERS[i]
        for k, c in enumerate(rv):
            gx = RX0 + (k % 6) * RP; gy = RY - (k // 6) * (TL + .003)
            last = (i == 3 and k == len(rv) - 1)
            if last and STEP >= 3: continue
            t = tile(c, (gx, gy, Z), r, "lie")
            if last: named["called"] = t
        # 手牌
        if i == 0:
            hand = list(HANDS[0])
            use = ["m4", "m5"]
            if STEP >= 2: hand = [c for c in hand if c not in use]
            if STEP >= 5: hand.remove("s3")
            x0 = -(len(hand) - 1) / 2 * HP - .03
            for k, c in enumerate(hand):
                named["hand_" + c] = tile(c, (x0 + k * HP, HY, Z), r, "stand")
            mx, my = .305, HY + TL / 2
            if STEP >= 2:   # 晒した2枚（寝かせる）
                tile("m4", (mx - TW - .001, my, Z), r, "lie"); tile("m5", (mx, my, Z), r, "lie")
            if STEP >= 3:   # 取ってきた牌は横向きで左に（上が左＝上家の方）
                tile("m6", (mx - TW * 1.5 - .001 - TL / 2 - .001, my - (TL - TW) / 2, Z), r, "lie", rz=math.pi / 2)
            if STEP >= 5:
                tile("s3", (RX0 + 3 * RP, RY, Z), r, "lie")
        else:
            x0 = -6 * HP
            for k in range(13):
                tile("back", (x0 + k * HP, HY, Z), r, "stand")   # 表は本人の側（-Y）。ほかの席からは背が見える
    return named

# ---------------- 選手（デフォルメ。顔は共通の作り・髪と体格と配色だけ変える）----------------
SKIN = "#F1CDB3"
PLAYERS = [   # 席0〜3。uniform=(柄, [色…4色まで])・hair=(形, 色)・build=体の幅・fem=線の細さ
    dict(uniform=("zigzag", ["#101820", "#39A9DB", "#E94B8A", "#101820"]), collar="#101820", hair=("short_messy", "#8A6238"), build=1.0, height=1.0),
    dict(uniform=("lines", ["#2B2422", "#C9A24B"]), collar="#C9A24B", hair=("mush", "#2E2019"), build=1.18, height=.97),
    dict(uniform=("camo", ["#2F6B3A", "#6FA05A", "#F2F2EE", "#E9C63A"]), collar="#1D2F5C", hair=("wavy", "#15130F"), build=1.06, height=1.02, eyes="tare"),
    dict(uniform=("lines", ["#17181B", "#C22B2B"]), collar="#C22B2B", hair=("bob", "#E9C46A"), build=.86, height=.95, eyes="cute"),      # 赤いユニフォーム＝金髪のボブの女性（2026-11-12 ユーザーの指摘。前は髪が白っぽく、女性に見えなかった）
]
SHEET = arg("--sheet", "")    # 1人の見本（前・横・後ろ）を書き出す。名簿の id を渡す
ROSTER = arg("--roster", "")  # 名簿（チーム＝ユニフォーム・人＝髪や眼鏡）。実名が入るので素材リポジトリ（非公開）に置く: まじゃすこ素材/3d/roster.json
SEATS = arg("--seats", "")    # 座らせる4人の id（席0=手前・1=右・2=奥・3=左）。例: --seats p01,p05,p10,p23
def person(roster, pid):
    """名簿の1人 → 選手の形。チームのユニフォームに、人ごとの髪・目・眼鏡・肌・体格を重ねる。書いていない所は性別の標準"""
    pp = roster["people"][pid]; tm = roster["teams"][pp["team"]]
    fem = pp.get("gender") == "f"
    d = dict(uniform=(tm["uniform"][0], tm["uniform"][1]), collar=tm.get("collar", tm["uniform"][1][0]),
             hair=tuple(pp.get("hair") or (("bob", "#2A211D") if fem else ("short_messy", "#2A211D"))),
             build=pp.get("build") or (.86 if fem else 1.04), height=pp.get("height") or (.95 if fem else 1.0),
             eyes=pp.get("eyes") or ("cute" if fem else "normal"))
    if tm.get("sleeve"): d["sleeve"] = tm["sleeve"]
    for k in ("skin", "glasses", "hair2", "beard"):
        if pp.get(k): d[k] = pp[k]
    return d
if ROSTER:
    import json as _json
    _R = _json.load(open(ROSTER, encoding="utf-8"))
    if SEATS: PLAYERS = [person(_R, x) for x in SEATS.split(",")]
    if SHEET: PLAYERS = [person(_R, SHEET)]
CAST = arg("--cast", "")     # 座る4人を外のファイルで差しかえる（tools/b3d/casts/*.json。動画ごとに人を変える。2026-11-12 ユーザーの依頼）
if CAST:
    import json as _json
    PLAYERS = [dict(p, uniform=(p["uniform"][0], p["uniform"][1]), hair=(p["hair"][0], p["hair"][1])) for p in _json.load(open(CAST, encoding="utf-8"))["players"]]
    assert len(PLAYERS) == 4, "cast は4人ぶん"
def build_player(i, P):
    r = empty(f"player{i}"); r.rotation_euler = (0, 0, i * math.pi / 2)
    b = P["build"]; hgt = P["height"]
    um = pattern_mat(f"uni{i}", *P["uniform"])
    skin = mat(f"skin{i}", P.get("skin", SKIN), .6)
    y0 = -.80
    # 胴（少し前かがみ）
    torso = box(f"torso{i}", (.40 * b, .25 * b, .52 * hgt), (0, y0, .93), um, bevel=.09, parent=r)
    torso.rotation_euler = (math.radians(-10), 0, 0)
    collar = box(f"collar{i}", (.20 * b, .06, .05), (0, y0 + .15, .93 + .215 * hgt), mat(f"collar{i}", P["collar"], .6), bevel=.015, parent=r)
    collar.rotation_euler = (math.radians(-25), 0, 0)
    # 頭（首は作らない。大きめの頭を胴にじかにのせる＝2026-11-11 ユーザーの判断。首があると、ずれたときに変に見える）
    HS = 1.5
    hd = empty(f"headroot{i}", r); hd.location = (0, y0 + .07, .93 + .26 * hgt + .115 * 1.08 * HS * .86); hd.scale = (HS, HS, HS)
    hd.rotation_euler = (math.radians(8), 0, 0)   # 少しうつむく
    hy = 0; hz = 0
    head = sphere(f"head{i}", .115, (0, hy, hz), skin, (1, 1, 1.08), hd)
    # 目は4種類（2026-11-12 ユーザーの依頼）: normal＝ふつう／tare＝タレ目／kiri＝キリッとした目／cute＝かわいらしい目（ふつうの目＋まつ毛3本ずつ）。白い点（キラキラ）は付けない
    ek = P.get("eyes", "normal"); em = mat("eye", "#2A211D", .45)
    ER, ESC, ETILT = {"normal": (.015, (1, .5, 1.2), 0), "tare": (.015, (1.25, .5, .95), 24), "kiri": (.015, (1.35, .5, .72), -20), "cute": (.015, (1, .5, 1.2), 0)}[ek]
    for sx in (-1, 1):
        e = sphere(f"eye{i}{sx}", ER, (sx * .042, hy + .106, hz - .006), em, ESC, hd)
        e.rotation_euler = (0, math.radians(sx * ETILT), 0)      # 顔の面の中で傾ける（＋で目じりが下がる）
        if ek == "kiri":     # まゆ（目じりが上がる短い線）
            box(f"brow{i}{sx}", (.03, .006, .0055), (sx * .043, hy + .104, hz + .017), em, bevel=.002, parent=hd).rotation_euler = (math.radians(-12), math.radians(sx * -16), 0)
        if ek == "cute":     # まつ毛3本（目の上の外がわに、扇のように開く短い線）
            for k, ang in enumerate((-12, 22, 56)):      # 真上からの角度（外がわへ倒す）
                a2 = math.radians(ang); r0, r1 = .0165, .0275
                cx = sx * (.042 + math.sin(a2) * (r0 + r1) / 2); cz = hz - .006 + math.cos(a2) * (r0 + r1) / 2 * 1.1
                ly = math.sqrt(max(1e-6, .115 ** 2 - cx * cx - ((cz - hz) / 1.08) ** 2))      # 頭の丸みの上に置く（決め打ちの奥行きだと、上の1本が頭にうまった）
                box(f"lash{i}{sx}{k}", (.0042, .007, r1 - r0), (cx, hy + ly, cz), em, bevel=.0012, parent=hd).rotation_euler = (math.radians(-8), math.radians(sx * ang), 0)
    if P.get("glasses"):   # めがね: "色" か [色, 形]。形 round＝丸い細ぶち／rect＝四角い細ぶち／thick＝太い四角
        g = P["glasses"]; gc, gs = (g, "round") if isinstance(g, str) else (g[0], g[1])
        gm = mat(f"glass{i}", gc, .3, metal=.3)
        for sx in (-1, 1):
            bpy.ops.mesh.primitive_torus_add(major_radius={"thick": .025}.get(gs, .027), minor_radius={"thick": .0052, "rect": .0036}.get(gs, .0032), location=(sx * .042, hy + .112, hz - .006), rotation=(math.radians(90), 0, 0),
                                             major_segments=4 if gs in ("rect", "thick") else 48, minor_segments=8)
            o = bpy.context.object; o.data.materials.append(gm); o.parent = hd
            if gs in ("rect", "thick"): o.rotation_euler = (math.radians(90), math.radians(45), 0); o.scale = (1.2, .85, 1)
            for poly in o.data.polygons: poly.use_smooth = True
        box(f"bridge{i}", (.03, .005, .005), (0, hy + .116, hz - .004), gm, parent=hd)
    if FACE == "nm":     # 鼻＝小さな丸いふくらみ／口＝短い横線（全員同じ）
        sphere(f"nose{i}", .011, (0, hy + .116, hz - .026), mat("nose", "#E3B79B", .6), (1, .7, .9), hd)
        # 口＝少し口角の上がった線（頭の丸みに沿わせた曲線。幅は目と目の間の半分ほど）
        cu = bpy.data.curves.new(f"mouth{i}", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = .0032; cu.bevel_resolution = 3; cu.use_fill_caps = True
        sp = cu.splines.new("POLY"); N = 9; sp.points.add(N - 1)
        for k in range(N):
            u = k / (N - 1) * 2 - 1; x = u * .021; z = -.054 + .0065 * u * u
            y = math.sqrt(max(1e-6, .115 ** 2 - x * x - (z / 1.08) ** 2)) + .001
            sp.points[k].co = (x, hy + y, hz + z, 1)
        mo = bpy.data.objects.new(f"mouth{i}", cu); add(mo); mo.parent = hd; cu.materials.append(mat("mouth", "#8A4A3C", .6))
    if P.get("beard"):
        bm = mat(f"beard{i}", P.get("hair", ("", "#2A211D"))[1] if P["beard"] != "gray" else "#6E6A66", .7)
        if P["beard"] in ("mustache", "both"): sphere(f"must{i}", .02, (0, hy + .113, hz - .042), bm, (1.25, .35, .32), hd)
        if P["beard"] in ("goatee", "both"): sphere(f"goat{i}", .014, (0, hy + .1, hz - .078), bm, (1.0, .45, .8), hd)
    # 髪
    kind, hc = P["hair"]; hm = mat(f"hair{i}", hc, .55)
    hm2 = mat(f"hairb{i}", P["hair2"], .55) if P.get("hair2") else hm      # 後ろ・内側の色（金髪の下が黒い など）
    cap = sphere(f"hair{i}", .124, (0, hy - .022, hz + .02), hm, (1.02, 1.0, 1.06), hd)
    if kind == "bob":      # あごの長さのボブ: 後ろと横を丸く包み、顔の両わきに内巻きの毛先、まっすぐな前髪
        sphere(f"bobback{i}", .125, (0, hy - .042, hz - .045), hm, (1.13, .95, 1.02), hd)
        for sx in (-1, 1):
            sphere(f"bobside{i}{sx}", .05, (sx * .108, hy + .028, hz - .058), hm, (.55, .95, 1.55), hd)
        sphere(f"bang{i}", .085, (0, hy + .058, hz + .062), hm, (1.32, .62, .46), hd)
    elif kind == "short_messy":
        for k in range(9):
            a = k / 9 * math.tau
            sphere(f"tuft{i}{k}", .045, (math.cos(a) * .07, hy - .02 + math.sin(a) * .07, hz + .105), hm, (1, 1, 1.25), hd)
        sphere(f"bang{i}", .07, (0.02, hy + .07, hz + .06), hm, (1.4, .5, .5), hd)
    elif kind == "wavy":
        for k in range(7):
            a = k / 7 * math.tau
            sphere(f"wave{i}{k}", .05, (math.cos(a) * .075, hy - .025 + math.sin(a) * .075, hz + .085), hm, (1, 1, .9), hd)
        sphere(f"bang{i}", .06, (-.03, hy + .07, hz + .075), hm, (1.3, .5, .45), hd)
    elif kind == "short":  # 短く整えた髪＋横に流した前髪
        sphere(f"bang{i}", .07, (.025, hy + .07, hz + .07), hm, (1.5, .5, .42), hd).rotation_euler = (0, math.radians(-12), 0)
    elif kind == "medium": # 耳にかかる長さ＋目の上までの前髪（毛先を少し散らす）
        for sx in (-1, 1):
            sphere(f"mside{i}{sx}", .06, (sx * .1, hy - .005, hz + .0), hm, (.55, 1.0, 1.25), hd)
        sphere(f"mback{i}", .12, (0, hy - .05, hz - .01), hm, (1.08, .9, 1.0), hd)
        for k in range(5):
            sphere(f"bang{i}{k}", .03, (-.05 + k * .025, hy + .085, hz + .045 - abs(k - 2) * .006), hm, (1.0, .6, 1.3), hd)
    elif kind == "curly":  # くせ毛のふんわりした中くらいの長さ（耳にかかる）
        for k in range(12):
            a = k / 12 * math.tau
            sphere(f"curl{i}{k}", .052, (math.cos(a) * .095, hy - .03 + math.sin(a) * .07, hz + .055 - abs(math.sin(a)) * .02), hm, (1, 1, 1.1), hd)
        for sx in (-1, 1): sphere(f"cside{i}{sx}", .05, (sx * .108, hy - .01, hz - .03), hm, (.7, 1, 1.1), hd)
        sphere(f"bang{i}", .06, (.0, hy + .075, hz + .07), hm, (1.4, .5, .5), hd)
    elif kind == "slick":  # 後ろへなでつけた髪（前髪なし・額が見える）
        sphere(f"slick{i}", .12, (0, hy - .03, hz + .045), hm, (1.03, 1.0, .82), hd)
    elif kind == "long":   # 肩より長いまっすぐな髪＋前髪（後ろに長く垂らす）
        sphere(f"lback{i}", .12, (0, hy - .055, hz - .07), hm2, (1.08, .7, 1.75), hd)
        for sx in (-1, 1):
            sphere(f"lside{i}{sx}", .045, (sx * .107, hy + .02, hz - .07), hm, (.55, .9, 2.0), hd)
        sphere(f"bang{i}", .085, (0, hy + .058, hz + .062), hm, (1.3, .6, .46), hd)
    elif kind == "updo":   # まとめ髪（後ろの高い所にお団子）＋顔の横に少し垂らす毛＋分けた前髪
        sphere(f"bun{i}", .055, (0, hy - .115, hz + .06), hm2, parent=hd)
        for sx in (-1, 1):
            sphere(f"strand{i}{sx}", .014, (sx * .1, hy + .05, hz - .05), hm, (.7, .7, 3.0), hd)
        sphere(f"bang{i}", .07, (-.02, hy + .068, hz + .07), hm, (1.5, .5, .42), hd).rotation_euler = (0, math.radians(10), 0)
    elif kind == "ponytail":  # 後ろでひとつに結んだ髪＋前髪
        sphere(f"tail{i}", .045, (0, hy - .14, hz - .02), hm2, (.8, .8, 2.0), hd)
        sphere(f"bang{i}", .08, (0, hy + .06, hz + .065), hm, (1.35, .55, .45), hd)
    else:                  # mush: 丸く厚い前髪
        sphere(f"bang{i}", .095, (0, hy + .045, hz + .05), hm, (1.25, .75, .55), hd)
    # 腕（両手を手牌のあたりに）
    am = mat(f"sleeve{i}", P["sleeve"], .7) if P.get("sleeve") else um     # そでだけ別の色のチーム（白い胴に黒いそで など）
    body = dict(torso=torso, torso_rx=math.radians(-10), torso_loc=torso.location.copy(), collar=collar, collar_loc=collar.location.copy(), head=hd, head_loc=hd.location.copy())
    for sx in (-1, 1):
        sh = (sx * .192 * b, y0 + .02, 1.075 * hgt); el = (sx * .27 * b, y0 + .26, .90); wr = (sx * .21, y0 + .345, TOP + .04)
        ua = limb(f"uarm{i}{sx}", sh, el, .055 * b, am, r); fa = limb(f"farm{i}{sx}", el, wr, .03, skin, r)     # 前腕は手首まで肌の色・少し太く
        eb = sphere(f"elb{i}{sx}", .056 * b, el, am, parent=r); sd = sphere(f"shd{i}{sx}", .057 * b, sh, am, parent=r)      # 肩の丸みは上腕と同じ太さ・胴の角の中におさめる（.07 で外・上に置くと、肩が盛り上がって見えた。2026-11-13 ユーザーの指摘）
        hn = sphere(f"hand{i}{sx}", .036, wr, skin, (1.05, 1.0, .6), r)     # 手のひら
        for fk, fx in enumerate((-.024, -.008, .008, .024)):               # 指4本（手の向き＝+Y にのびる）
            sphere(f"fing{i}{sx}{fk}", .0105, (fx, .042 - abs(fx) * .25, -.004), skin, (1, 2.6, 1.5), hn)
        sphere(f"thumb{i}{sx}", .012, (-sx * .036, .012, -.004), skin, (1, 2.0, 1.4), hn).rotation_euler = (0, 0, sx * math.radians(35))    # 親指は内がわ
        body["R" if sx == 1 else "L"] = dict(sx=sx, sh=Vector(sh), ua=ua, fa=fa, eb=eb, shd=sd, hand=hn, rest=Vector(wr))
    pose_body(body, body["R"]["rest"])       # 止まった絵でも、ひじを曲げた形にしておく
    arm = body
    # 椅子
    cm = mat("chair", "#EDEDEA" if THEME == "dark" else "#FFFFFF", .5)
    if not SHEET: box(f"seat{i}", (.50, .48, .08), (0, y0 - .03, .50), cm, bevel=.03, parent=r)
    if not SHEET:
        box(f"back{i}", (.48, .07, .62), (0, y0 - .30, .86), cm, bevel=.03, parent=r).rotation_euler = (math.radians(8), 0, 0)
        limb(f"cpole{i}", (0, y0 - .03, .06), (0, y0 - .03, .46), .03, mat("pole", "#16181A", .4), r)
        box(f"cfoot{i}", (.5, .5, .03), (0, y0 - .03, .03), mat("pole", "#16181A", .4), bevel=.01, parent=r)
    if SHEET: return arm          # 見本（前・横・後ろ）では、椅子の横の机は出さない
    # サイドテーブルと、ストローの刺さったペットボトルの水（左手前。2026-11-12 ユーザーの依頼で黒い球から変えた）
    box(f"side{i}", (.34, .30, .03), (-.62, y0 + .12, .70), mat("pole", "#16181A", .4), bevel=.008, parent=r)
    limb(f"spole{i}", (-.62, y0 + .12, 0), (-.62, y0 + .12, .69), .02, mat("pole", "#16181A", .4), r)
    bottle(f"btl{i}", (-.60, y0 + .10, .715), r)
    return arm

def bottle(name, base, parent):
    """500mLのペットボトルの水（高さ約21cm）＋白いキャップ＋青いラベル＋曲がったストロー"""
    x, y, z = base
    water = mat("bottle", "#CFE6F2", .05)
    p = water.node_tree.nodes["Principled BSDF"]
    p.inputs["Transmission Weight"].default_value = .85; p.inputs["IOR"].default_value = 1.33; p.inputs["Alpha"].default_value = .9
    bpy.ops.mesh.primitive_cylinder_add(radius=.034, depth=.17, location=(x, y, z + .085), vertices=28)
    o = bpy.context.object; o.name = name; o.data.materials.append(water); o.parent = parent
    for poly in o.data.polygons: poly.use_smooth = True
    sphere(name + "_sh", .034, (x, y, z + .17), water, (1, 1, .75), parent)                           # 肩（丸くすぼまる）
    limb(name + "_nk", (x, y, z + .185), (x, y, z + .2), .014, water, parent)                          # 口
    limb(name + "_cap", (x, y, z + .2), (x, y, z + .216), .016, mat("cap", "#F4F6F7", .4), parent)
    limb(name + "_lb", (x, y, z + .07), (x, y, z + .115), .0352, mat("label", "#2F7FD0", .5), parent)  # ラベル
    st = mat("straw", "#F7F7F7", .35)
    a, b2, c = Vector((x + .004, y, z + .2)), Vector((x + .006, y, z + .285)), Vector((x + .03, y - .006, z + .30))
    limb(name + "_s1", a, b2, .0035, st, parent); limb(name + "_s2", b2, c, .0035, st, parent)
    sphere(name + "_sj", .0035, b2, st, parent=parent)

# ---------------- 会場 ----------------
def build_venue():
    if THEME == "dark":
        floor = box("floor", (30, 30, .02), (0, 0, -.13), mat("floor", "#050607", .18))
        box("stage", (4.6, 4.6, .12), (0, 0, -.06), mat("stage", "#08090B", .12))
        led = mat("led", "#BFD0FF", .3, emit=4.0)
        for a in range(4):       # 舞台のふちの光る線
            e = empty(f"ledp{a}"); e.rotation_euler = (0, 0, a * math.pi / 2)
            box(f"led_s{a}", (4.6, .03, .02), (0, -2.3, -.005), led, parent=e)
            box(f"led_o{a}", (9.0, .04, .02), (0, -4.6, -.11), led, parent=e)
        wall = mat("wall", "#0E1014", .6)
        for side in range(2):    # 奥と右の壁＝高さのちがう縦の板。足もとから青白い光
            e = empty(f"wallp{side}"); e.rotation_euler = (0, 0, -side * math.pi / 2)
            box(f"wall{side}", (12, .2, 5), (0, 5.4, 2.4), mat("wall_b", "#040506", .8), parent=e)
            for k in range(46):
                h = random.uniform(1.2, 3.6); d = random.uniform(.08, .35)
                box(f"slat{side}_{k}", (.2, d, h), (-5.6 + k * .245, 5.2 - d / 2, h / 2 - .1), wall, parent=e)
            box(f"wall_led{side}", (11.5, .05, .05), (0, 4.9, -.08), mat("led2", "#9FB4FF", .3, emit=6.0), parent=e)
        w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
        w.node_tree.nodes["Background"].inputs[0].default_value = (.002, .003, .006, 1)
        key = [("AREA", (0, 0, 3.2), (0, 0, 0), 70, 1.6), ("AREA", (0, -3.2, 2.6), (58, 0, 0), 45, 2.0), ("AREA", (3.2, 0, 2.6), (58, 0, 90), 40, 2.0),
               ("AREA", (0, 3.2, 2.6), (58, 0, 180), 40, 2.0), ("AREA", (-3.2, 0, 2.6), (58, 0, 270), 40, 2.0)]
    else:
        bg = "#DCEFE3"            # ふだんのショート動画の背景に近い薄い緑
        box("floor", (40, 40, .02), (0, 0, -.01), mat("floor", bg, .9))
        w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
        w.node_tree.nodes["Background"].inputs[0].default_value = hexc(bg)
        w.node_tree.nodes["Background"].inputs[1].default_value = .9
        key = [("AREA", (0, 0, 3.4), (0, 0, 0), 60, 3.0), ("AREA", (2.5, -3, 3), (50, 0, 35), 50, 2.5)]
    for k, (typ, loc, rot, energy, size) in enumerate(key):
        ld = bpy.data.lights.new(f"L{k}", typ); ld.energy = energy; ld.size = size
        o = bpy.data.objects.new(f"L{k}", ld); add(o); o.location = loc; o.rotation_euler = [math.radians(x) for x in rot]

# ---------------- カメラ ----------------
CAM = {   # 名前: (位置, 見る点, レンズmm)
    "wide": ((3.6, -4.6, 2.5), (0, 0, .95), 30),          # 会場の引き
    "mid":  ((1.25, -2.2, 1.7), (0, .05, 1.0), 38),      # 手前の選手の肩ごし
    "hand": ((0, -.50, 1.20), (0, -.22, .77), 26),      # 手前の選手の目線（手牌と河）     # 手牌に寄る（低い位置）
    "face3": ((.12, .26, 1.44), (-.72, 0, 1.28), 34),       # 左の選手（席3）の顔のアップ
    "face": ((.28, -.15, 1.46), (0, .72, 1.30), 34),       # 奥の選手の顔のアップ（顔の作りを確かめる用）
    "top":  ((0, -.02, 2.6), (0, 0, .76), 42),            # 真上
    "meld": ((.52, -.58, 1.05), (.27, -.33, .76), 70),     # 右端に並べた牌のアップ
}
def add_cam(name):
    loc, tgt, lens = CAM[name]
    cd = bpy.data.cameras.new(name); cd.lens = lens; cd.dof.use_dof = name in ("hand", "meld"); cd.dof.aperture_fstop = 2.8
    o = bpy.data.objects.new("cam_" + name, cd); add(o); o.location = loc
    d = Vector(tgt) - Vector(loc)
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    cd.dof.focus_distance = d.length
    return o

if SHEET:
    # 見本: 薄い灰緑の地に1人。椅子の背もたれは後ろ姿を隠すので出さない（build_player の中で SHEET を見る）
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = hexc("#DCE6E3"); w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    box("floor", (8, 8, .02), (0, 0, -.01), mat("floor", "#DCE6E3", .9))
    for k, (loc, rot, e) in enumerate((((1.5, .8, 2.6), (40, 0, 120), 120), ((-1.6, -2.4, 2.2), (55, 0, -35), 80), ((0, -3.2, 2.0), (65, 0, 0), 60))):
        ld = bpy.data.lights.new(f"S{k}", "AREA"); ld.energy = e; ld.size = 2.5
        o = bpy.data.objects.new(f"S{k}", ld); add(o); o.location = loc; o.rotation_euler = [math.radians(v) for v in rot]
    ARMS = [build_player(0, PLAYERS[0])]
    r = sc.render; r.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True
    r.resolution_x, r.resolution_y = SIZE; r.image_settings.file_format = "PNG"; sc.view_settings.view_transform = "Standard"
    os.makedirs(OUT, exist_ok=True)
    tgt = Vector((0, -.80, 1.16))      # 頭のてっぺんから胴まで入る高さ
    for nm, loc in (("front", (0, .55, 1.25)), ("side", (1.55, -.80, 1.22)), ("back", (0, -2.15, 1.30))):
        cd = bpy.data.cameras.new(nm); cd.lens = 40; o = bpy.data.objects.new("cam_" + nm, cd); add(o)
        o.location = loc; o.rotation_euler = (tgt - Vector(loc)).to_track_quat("-Z", "Y").to_euler(); sc.camera = o
        r.filepath = os.path.join(OUT, f"{SHEET}_{nm}.png"); bpy.ops.render.render(write_still=True); print("SHEET", SHEET, nm, flush=True)
    sys.exit(0)

build_venue(); build_table(); NAMED = build_tiles()
ARMS = [build_player(i, P) for i, P in enumerate(PLAYERS)]

r = sc.render; r.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
r.resolution_x, r.resolution_y = SIZE; r.image_settings.file_format = "PNG"
sc.view_settings.view_transform = "Standard"
os.makedirs(OUT, exist_ok=True)
if "--save" in sys.argv:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f"mleague_base_{THEME}.blend"))
import time

# ---------------- 動きの試し: チーの5つの手順（8秒）----------------
def ease(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
def seg(t, a, b):
    return ease((t - a) / (b - a))
def lerp(a, b, k):
    return Vector(a).lerp(Vector(b), k)
ANIM_DUR = 8.0 + 3 * .7      # もとの動き8秒＋見せるための間3回
# 手順が終わるたびに、手をどけて牌を見せる間を入れる（2026-11-12 ユーザーの指摘「開示で牌が手で隠れて見えない」）。
# FREEZE＝もとの時刻（②開示のあと・③回収のあと・④副露のあと）。その間 PAUSE 秒は牌を止め、手だけ手前へ引き、カメラが牌に寄る
FREEZE = (2.0, 3.8, 5.0); PAUSE = .7
def warp(t):
    """実際の時刻 → もとの動きの時刻（間のあいだは進まない）"""
    for f in FREEZE:
        if t <= f: return t
        if t <= f + PAUSE: return f
        t -= PAUSE
    return t
def pause_k(t, n):
    """n番目の間で、手がどいている度合い（0〜1）"""
    a = FREEZE[n] + n * PAUSE
    return seg(t, a, a + .22) - seg(t, a + PAUSE - .05, a + PAUSE + .3)
# 手順の区切り（秒）: ①声 0〜1.5 ②晒す 1.5〜2.1 ③取る 2.1〜3.8 ④右端に並べる 3.8〜5.0 ⑤切る 5.0〜6.6
def anim_setup():
    bpy.context.view_layer.update()
    c = NAMED["called"]; mw = c.matrix_world.copy(); c.parent = None; c.matrix_world = mw     # 上家の河の六萬を、卓の座標で動かせるように
    cd = bpy.data.cameras.new("anim"); o = bpy.data.objects.new("cam_anim", cd); add(o); sc.camera = o
    return o
def anim_pose(t, cam):
    tr = t; t = warp(t)          # tr＝実際の時刻・t＝もとの動きの時刻
    Z = TOP + .0005
    m4, m5, s3, m6 = NAMED["hand_m4"], NAMED["hand_m5"], NAMED["hand_s3"], NAMED["called"]
    X4, X5, XS = HX0 + 11 * HP, HX0 + 12 * HP, HX0 + HANDS[0].index("s3") * HP     # 手牌の四萬・五萬・三索の位置（牌の大きさから計算する）
    # 晒した牌の置き場＝手牌の延長線上の右（手牌と平行・手前のふちをそろえる）。倒していない手牌とのあいだは GAP だけ空ける（2026-11-12 ユーザーの依頼。前は手牌の奥に倒していて、近くて見えにくかった）
    GAP = .028
    LY = HY + TL / 2                            # 倒した牌の中心（手前のふちが手牌の表の面と同じ線）
    E6 = HX0 + 10 * HP + TW / 2 + GAP + TL / 2  # 取ってきた六萬（横向き）の中心
    E4 = E6 + TL / 2 + .001 + TW / 2; E5 = E4 + TW + .001      # 晒した四萬・五萬の中心
    DX, DY = .305 - E5, 0.0                     # 右の隅へ寄せる分（同じ線の上をすべらせる）
    # ② 晒す（立てた牌を向こうへ倒す）
    k2 = seg(t, 1.5, 2.0); k4 = seg(t, 4.2, 5.0)
    for o, x, ex in ((m4, X4, E4), (m5, X5, E5)):
        o.rotation_euler = (math.radians(90) * (1 - k2), 0, 0)
        o.location = lerp((x, HY + TT, Z + TL / 2), (ex, LY, Z), k2) + Vector((0, 0, .03 * math.sin(math.pi * k2))) + Vector((DX, DY, 0)) * k4
    # ③ 取る（上家の河 → 晒した2枚の左。牌は横向きのまま）
    k3 = seg(t, 2.9, 3.8)
    p0 = Vector((RY, -(RX0 + CALL_K * RP), Z)); p1 = Vector((E6, LY - TL / 2 + TW / 2, Z))
    m6.location = lerp(p0, p1, k3) + Vector((0, 0, .05 * math.sin(math.pi * k3))) + Vector((DX, DY, 0)) * k4
    m6.rotation_euler = (0, 0, -math.pi / 2)
    # ⑤ 切る（手牌の三索 → 河の4枚目）
    k5 = seg(t, 5.7, 6.5)
    s3.rotation_euler = (math.radians(90) * (1 - seg(t, 5.9, 6.4)), 0, 0)
    s3.location = lerp((XS, HY + TT, Z + TL / 2), (RX0 + 3 * RP, RY, Z), k5) + Vector((0, 0, .06 * math.sin(math.pi * k5)))
    # 右手（道すじ: 休み → 手の2枚 → 河の六萬 → 2枚の左 → 3枚の上 → 右の隅 → 三索 → 河 → 休み）
    A = ARMS[0]["R"]; R = A["rest"]; hz = TOP + TL + .012; OFF = Vector((.004, -.026 * TS, 0))   # 手は牌の手前がわに置く（牌の絵が隠れないように）
    keys = [(0.0, R), (0.9, R), (1.5, (X4 + .012, HY + .01, hz + .02)), (2.0, ((E4 + E5) / 2, LY, hz)), (2.9, (p0.x, p0.y, hz)), (3.8, (p1.x, p1.y, hz)),
            (4.2, (E4, LY, hz)), (5.0, (E4 + DX, LY + DY, hz)), (5.7, (XS, HY + .01, hz + .02)), (6.5, (RX0 + 3 * RP, RY, hz)), (7.2, R), (ANIM_DUR, R)]
    w = Vector(keys[-1][1])
    for (ta, pa), (tb, pb) in zip(keys, keys[1:]):
        if ta <= t <= tb:
            k = seg(t, ta, tb); d = (Vector(pb) - Vector(pa)).length
            w = lerp(pa, pb, k) + Vector((0, 0, min(.07, d * .3) * math.sin(math.pi * k))); break
    w = w + OFF * (seg(t, .9, 1.5) - seg(t, 6.5, 7.2))
    pk = [pause_k(tr, n) for n in range(3)]
    w = w + Vector((.085, -.085, .03)) * max(pk)      # 間のあいだは、手を右手前へ引いて牌を見せる
    pose_body(ARMS[0], w)      # ひじを曲げ、届かない分は上体を倒す
    # カメラ: 肩ごし → 卓の上から → 右の隅に寄る
    c0 = (Vector(CAM["mid"][0]), Vector(CAM["mid"][1]), 38.0)
    px = .03 + .13 * (seg(t, 3.8, 5.0) - seg(t, 5.2, 5.9)) - .14 * (seg(t, 2.1, 2.9) - seg(t, 3.1, 3.8))      # 手の動きに合わせて、見る点を少し左右に振る
    c1 = (Vector((-.40 + px * .5, -.62, 1.27)), Vector((.02 + px, -.24, .77)), 33.0)   # 手前の選手の左肩の上から（右腕が画面を横切らない・手牌の表が見える）
    c2 = (Vector((.36, -.60, 1.22)), Vector((.25, -.31, .77)), 42.0)
    ka = seg(t, .4, 1.4); kb = seg(t, 6.8, 7.8)
    loc = c0[0].lerp(c1[0], ka).lerp(c2[0], kb); tgt = c0[1].lerp(c1[1], ka).lerp(c2[1], kb)
    loc = loc + Vector((-.22, -.10, .34)) * math.sin(math.pi * ka)      # 肩ごしから卓の上へは、手前の選手の頭の上を回りこむ（まっすぐ行くと体の中を通って画面が黒くなる）
    cam.data.lens = (c0[2] + (c1[2] - c0[2]) * ka) * (1 - kb) + c2[2] * kb
    # 間のあいだは、見せたい牌に寄る（②晒した2枚・③取ってきた牌と2枚・④右の隅の3枚）
    focus = [Vector((E4 - .01, LY, .77)), Vector((E4 - .012, LY, .77)), Vector((E4 + DX - .012, LY + DY, .77))]
    # 寄るときは、牌のほぼ真上（少し手前）から見下ろす。左肩の上からのままだと、倒した牌が立っている手牌と山のあいだに隠れて見えない
    for n in range(3):
        loc = loc.lerp(focus[n] + Vector((-.02, -.17, .50)), pk[n]); tgt = tgt.lerp(focus[n], pk[n])
        cam.data.lens += (50 - cam.data.lens) * pk[n]
    cam.location = loc; cam.rotation_euler = (tgt - loc).to_track_quat("-Z", "Y").to_euler()

# ---------------- 入り（イントロ）: 会場を卓のまわりからドローンのように回りこんで、本題の最初の画角（肩ごし）に着く ----------------
# 3Dの卓の解説動画は、どれもこの入りから始める（2026-11-12 ユーザーの依頼）。題名は make_clip.py がこの上にのせる
INTRO_DUR = 4.0
def intro_pose(u, cam):
    """u=0〜1。遠く高い所から、卓を中心に回りながら近づき、anim_pose(0) のカメラにぴったり重なって終わる"""
    e = 1 - (1 - max(0.0, min(1.0, u))) ** 1.6          # はじめ速く、着くときはゆっくり
    end, tg1 = Vector(CAM["mid"][0]), Vector(CAM["mid"][1])
    a1 = math.atan2(end.y, end.x); r1 = math.hypot(end.x, end.y)
    a = a1 - math.radians(170) * (1 - e)                # 170度ぶん回る（壁のある奥と右が背景に入る側だけを通る）
    rr = r1 + (4.9 - r1) * (1 - e); z = end.z + (3.3 - end.z) * (1 - e)
    loc = Vector((math.cos(a) * rr, math.sin(a) * rr, z)); tgt = Vector((0, 0, .85)).lerp(tg1, e)
    cam.data.lens = 26 + (CAM["mid"][2] - 26) * e
    cam.location = loc; cam.rotation_euler = (tgt - loc).to_track_quat("-Z", "Y").to_euler()

# ---------------- 締め（アウトロ）: 入りの逆。本題の最後の形のまま、肩ごしから回りながら引いて会場全体に戻る ----------------
# 3Dの卓の解説動画は、どれもこの締めで終わる（2026-11-12 ユーザーの判断・案A）。ロゴと「麻雀のスコア記録は まじゃすこ で」は make_clip.py がのせる
OUTRO_DUR = 3.0
if ANIM and "--outro" in sys.argv:      # 締めのコマを o0000.png〜 に書き出す
    cam = anim_setup(); anim_pose(ANIM_DUR, cam)
    n = int(OUTRO_DUR * FPS)
    only = arg("--frames", "")
    for f in ([int(x) for x in only.split(",")] if only else range(n)):
        fp = os.path.join(OUT, f"o{f:04d}.png")
        if os.path.exists(fp): continue
        intro_pose(1 - f / (n - 1), cam)
        r.filepath = fp
        t0 = time.time(); bpy.ops.render.render(write_still=True); print("OUTRO", f, round(time.time() - t0, 1), "s", flush=True)
    sys.exit(0)

if ANIM and "--intro" in sys.argv:      # 入りのコマだけを i0000.png〜 に書き出す（選手や卓は本題の最初の形のまま）
    cam = anim_setup(); anim_pose(0.0, cam)
    n = int(INTRO_DUR * FPS)
    only = arg("--frames", "")
    for f in ([int(x) for x in only.split(",")] if only else range(n)):
        fp = os.path.join(OUT, f"i{f:04d}.png")
        if os.path.exists(fp): continue
        intro_pose(f / n, cam)
        r.filepath = fp
        t0 = time.time(); bpy.ops.render.render(write_still=True); print("INTRO", f, round(time.time() - t0, 1), "s", flush=True)
    sys.exit(0)

if ANIM:
    cam = anim_setup()
    n = int(ANIM_DUR * FPS)
    only = arg("--frames", "")
    todo = [int(x) for x in only.split(",")] if only else range(n)
    if "--marks" in sys.argv:      # 書き出さずに、動く牌が画面のどこにあるかだけを marks.json に（make_clip.py が印をのせるのに使う）
        import json
        from bpy_extras.object_utils import world_to_camera_view
        names = {"m4": "hand_m4", "m5": "hand_m5", "s3": "hand_s3", "m6": "called"}
        out = {}
        for f in range(n):
            anim_pose(f / FPS, cam); bpy.context.view_layer.update()
            d = {}
            for k, nm in names.items():
                v = world_to_camera_view(sc, cam, NAMED[nm].matrix_world @ Vector((0, 0, TT / 2)))
                d[k] = [round(v.x, 4), round(1 - v.y, 4)]
            v = world_to_camera_view(sc, cam, Vector((0, -.66, 1.42))); d["head0"] = [round(v.x, 4), round(1 - v.y, 4)]
            out[f] = d
        json.dump(out, open(os.path.join(OUT, "marks.json"), "w")); print("MARKS", n); sys.exit(0)
    for f in todo:
        fp = os.path.join(OUT, f"f{f:04d}.png")
        if os.path.exists(fp): continue
        anim_pose(f / FPS, cam)
        r.filepath = fp
        t0 = time.time(); bpy.ops.render.render(write_still=True); print("FRAME", f, round(time.time() - t0, 1), "s", flush=True)
    sys.exit(0)

for name in CAMS:
    if name not in CAM: continue
    sc.camera = add_cam(name)
    r.filepath = os.path.join(OUT, f"{THEME}_{name}_s{STEP}.png")
    t0 = time.time(); bpy.ops.render.render(write_still=True); print("RENDERED", name, round(time.time() - t0, 1), "s", flush=True)
