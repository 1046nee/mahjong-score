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
STEP = int(arg("--step", "4"))   # 鳴きの手順のどこまで進んだか（0=鳴く前 … 5=打牌まで）

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
    """ユニフォームの柄（実物の柄ではなく、配色だけ）。kind: zigzag / camo / lines / plain"""
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

def limb(name, a, b, r, m, parent=None):
    """a→b の円柱（腕）"""
    a, b = Vector(a), Vector(b); d = b - a
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d.length, location=(a + b) / 2, vertices=20)
    o = bpy.context.object; o.name = name
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    o.data.materials.append(m)
    for poly in o.data.polygons: poly.use_smooth = True
    if parent: o.parent = parent
    return o

def empty(name, parent=None):
    e = bpy.data.objects.new(name, None); add(e)
    if parent: e.parent = parent
    return e

# ---------------- 牌 ----------------
TW, TL, TT = 0.024, 0.032, 0.017      # 幅・長さ・厚み（m）
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
        o.rotation_euler = Euler((math.radians(90), 0, rz), "XYZ"); o.location = (x, y + TT, z)      # 底が z、表が -Y
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
    ["p3", "p4", "p6", "p7", "s3", "s5", "s6", "s7", "z7", "z7", "p9", "m4", "m5"],     # 席0（鳴く人）
    None, None, None,
]
RIVERS = [["z2", "m1", "p8"], ["z4", "p9", "s1", "m2"], ["s9", "z6", "p1"], ["z1", "m9", "p2", "s8", "z3", "m6"]]   # 席3の最後の六萬をチーする

def build_tiles():
    Z = TOP + .0005
    roots = [seat_root(i) for i in range(4)]
    named = {}
    for i, r in enumerate(roots):
        # 山（2段×13幢。手前の席から見て左右に）
        n = 13 if i != 0 else 11
        x0 = -(n - 1) / 2 * (TW + .0008)
        for k in range(n):
            for lv in range(2):
                tile("back", (x0 + k * (TW + .0008), -.235, Z + lv * TT), r, "down", rz=math.pi / 2 * 0)
        # 河（6枚で折り返す）
        rv = RIVERS[i]
        for k, c in enumerate(rv):
            gx = -.0675 + (k % 6) * (TW + .003); gy = -.118 - (k // 6) * (TL + .003)
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
            x0 = -(len(hand) - 1) / 2 * (TW + .0006) - .03
            for k, c in enumerate(hand):
                tile(c, (x0 + k * (TW + .0006), -.318, Z), r, "stand")
            mx, my = .305, -.325
            if STEP >= 2:   # 晒した2枚（寝かせる）
                tile("m4", (mx - TW - .001, my, Z), r, "lie"); tile("m5", (mx, my, Z), r, "lie")
            if STEP >= 3:   # 取ってきた牌は横向きで左に（上が左＝上家の方）
                tile("m6", (mx - TW * 1.5 - .001 - TL / 2 - .001, my - (TL - TW) / 2, Z), r, "lie", rz=math.pi / 2)
            if STEP >= 5:
                tile("s3", (-.0675 + 3 * (TW + .003), -.118, Z), r, "lie")
        else:
            x0 = -6 * (TW + .0006)
            for k in range(13):
                tile("back", (x0 + k * (TW + .0006), -.318, Z), r, "stand")   # 表は本人の側（-Y）。ほかの席からは背が見える
    return named

# ---------------- 選手（デフォルメ。顔は共通の作り・髪と体格と配色だけ変える）----------------
SKIN = "#F1CDB3"
PLAYERS = [   # 席0〜3。uniform=(柄, [色…4色まで])・hair=(形, 色)・build=体の幅・fem=線の細さ
    dict(uniform=("zigzag", ["#101820", "#39A9DB", "#E94B8A", "#101820"]), collar="#101820", hair=("short_messy", "#8A6238"), build=1.0, height=1.0),
    dict(uniform=("lines", ["#2B2422", "#C9A24B"]), collar="#C9A24B", hair=("mush", "#2E2019"), build=1.18, height=.97),
    dict(uniform=("camo", ["#2F6B3A", "#6FA05A", "#F2F2EE", "#E9C63A"]), collar="#1D2F5C", hair=("wavy", "#15130F"), build=1.06, height=1.02),
    dict(uniform=("lines", ["#17181B", "#C22B2B"]), collar="#C22B2B", hair=("bob", "#DDD3BE"), build=.86, height=.95),
]
def build_player(i, P):
    r = empty(f"player{i}"); r.rotation_euler = (0, 0, i * math.pi / 2)
    b = P["build"]; hgt = P["height"]
    um = pattern_mat(f"uni{i}", *P["uniform"])
    skin = mat("skin", SKIN, .6)
    y0 = -.80
    # 胴（少し前かがみ）
    torso = box(f"torso{i}", (.40 * b, .25 * b, .52 * hgt), (0, y0, .93), um, bevel=.09, parent=r)
    torso.rotation_euler = (math.radians(-10), 0, 0)
    box(f"collar{i}", (.20 * b, .06, .05), (0, y0 + .135, 1.17 * hgt + .0), mat(f"collar{i}", P["collar"], .6), bevel=.015, parent=r).rotation_euler = (math.radians(-25), 0, 0)
    limb(f"neck{i}", (0, y0 + .03, 1.15 * hgt), (0, y0 + .06, 1.26 * hgt), .05, skin, r)
    # 頭（少しうつむく）
    hz = 1.36 * hgt; hy = y0 + .09
    head = sphere(f"head{i}", .115, (0, hy, hz), skin, (1, 1, 1.08), r)
    for sx in (-1, 1):   # 目（伏し目の小さな線）
        box(f"eye{i}{sx}", (.026, .006, .006), (sx * .042, hy + .105, hz - .012), mat("eye", "#2A211D", .5), parent=r).rotation_euler = (math.radians(-20), 0, 0)
    # 髪
    kind, hc = P["hair"]; hm = mat(f"hair{i}", hc, .55)
    cap = sphere(f"hair{i}", .124, (0, hy - .022, hz + .02), hm, (1.02, 1.0, 1.06), r)
    if kind == "bob":      # あごまでのボブ＋前髪
        bpy.ops.mesh.primitive_cylinder_add(radius=.128, depth=.17, location=(0, hy - .03, hz - .075), vertices=32)
        o = bpy.context.object; o.data.materials.append(hm); o.parent = r; o.scale = (1.0, .92, 1)
        for poly in o.data.polygons: poly.use_smooth = True
        sphere(f"bang{i}", .08, (0, hy + .062, hz + .055), hm, (1.35, .55, .5), r)
    elif kind == "short_messy":
        for k in range(9):
            a = k / 9 * math.tau
            sphere(f"tuft{i}{k}", .045, (math.cos(a) * .07, hy - .02 + math.sin(a) * .07, hz + .105), hm, (1, 1, 1.25), r)
        sphere(f"bang{i}", .07, (0.02, hy + .07, hz + .06), hm, (1.4, .5, .5), r)
    elif kind == "wavy":
        for k in range(7):
            a = k / 7 * math.tau
            sphere(f"wave{i}{k}", .05, (math.cos(a) * .075, hy - .025 + math.sin(a) * .075, hz + .085), hm, (1, 1, .9), r)
        sphere(f"bang{i}", .06, (-.03, hy + .07, hz + .075), hm, (1.3, .5, .45), r)
    else:                  # mush: 丸く厚い前髪
        sphere(f"bang{i}", .095, (0, hy + .045, hz + .05), hm, (1.25, .75, .55), r)
    # 腕（両手を手牌のあたりに）
    am = um
    for sx in (-1, 1):
        sh = (sx * .21 * b, y0 + .02, 1.10 * hgt); el = (sx * .27 * b, y0 + .26, .90); wr = (sx * .21, y0 + .345, TOP + .04)
        limb(f"uarm{i}{sx}", sh, el, .055 * b, am, r); limb(f"farm{i}{sx}", el, wr, .042, skin, r)
        sphere(f"elb{i}{sx}", .056 * b, el, am, parent=r); sphere(f"shd{i}{sx}", .07 * b, sh, am, parent=r)
        sphere(f"hand{i}{sx}", .045, wr, skin, (1, 1.25, .7), r)
    # 椅子
    cm = mat("chair", "#EDEDEA" if THEME == "dark" else "#FFFFFF", .5)
    box(f"seat{i}", (.50, .48, .08), (0, y0 - .03, .50), cm, bevel=.03, parent=r)
    box(f"back{i}", (.48, .07, .62), (0, y0 - .30, .86), cm, bevel=.03, parent=r).rotation_euler = (math.radians(8), 0, 0)
    limb(f"cpole{i}", (0, y0 - .03, .06), (0, y0 - .03, .46), .03, mat("pole", "#16181A", .4), r)
    box(f"cfoot{i}", (.5, .5, .03), (0, y0 - .03, .03), mat("pole", "#16181A", .4), bevel=.01, parent=r)
    # サイドテーブルとカメラの黒いドーム（左手前）
    box(f"side{i}", (.34, .30, .03), (-.62, y0 + .12, .70), mat("pole", "#16181A", .4), bevel=.008, parent=r)
    limb(f"spole{i}", (-.62, y0 + .12, 0), (-.62, y0 + .12, .69), .02, mat("pole", "#16181A", .4), r)
    for dx in (-.08, .08):
        sphere(f"dome{i}{dx}", .075, (-.62 + dx, y0 + .12, .80), mat("dome", "#0B0C0E", .15), (1, 1, 1.25), r)

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
    "hand": ((0, -.60, 1.16), (0, -.24, .77), 26),      # 手前の選手の目線（手牌と河）     # 手牌に寄る（低い位置）
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

build_venue(); build_table(); build_tiles()
for i, P in enumerate(PLAYERS): build_player(i, P)

r = sc.render; r.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
r.resolution_x, r.resolution_y = SIZE; r.image_settings.file_format = "PNG"
sc.view_settings.view_transform = "Standard"
os.makedirs(OUT, exist_ok=True)
if "--save" in sys.argv:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f"mleague_base_{THEME}.blend"))
import time
for name in CAMS:
    if name not in CAM: continue
    sc.camera = add_cam(name)
    r.filepath = os.path.join(OUT, f"{THEME}_{name}_s{STEP}.png")
    t0 = time.time(); bpy.ops.render.render(write_still=True); print("RENDERED", name, round(time.time() - t0, 1), "s", flush=True)
