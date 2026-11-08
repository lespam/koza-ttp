# Uso: python docs/lottie/generar_arbol_evoluciona.py
# Los colores los pone static/css/documentacion.css (clases rama, nodo, hoja...), así sigue el modo claro u oscuro.
"""Genera static/lottie/arbol_evoluciona.json: un árbol de PG que crece,
cruza dos hojas (cruce) y cambia una (mutación). 30 fps, 150 cuadros."""
import json
FR=150
def st(v): return {"a":0,"k":v}
def anim(keys):  # keys: [(t, value_list)]
    ks=[]
    for i,(t,v) in enumerate(keys):
        k={"t":t,"s":v}
        if i<len(keys)-1: k.update({"i":{"x":[0.4],"y":[1]},"o":{"x":[0.6],"y":[0]}})
        ks.append(k)
    return {"a":1,"k":ks}
def tr(): return {"ty":"tr","p":st([0,0]),"a":st([0,0]),"s":st([100,100]),"r":st(0),"o":st(100),"sk":st(0),"sa":st(0)}
def layer(ind,nm,shapes,ks,cl):
    return {"ddd":0,"ind":ind,"ty":4,"nm":nm,"cl":cl,"sr":1,"ks":ks,"ao":0,"shapes":shapes,"ip":0,"op":FR,"st":0,"bm":0}
def ks(p=(0,0),s=None,o=None):
    return {"o":o or st(100),"r":st(0),"p":(p if isinstance(p,dict) else st([p[0],p[1],0])),"a":st([0,0,0]),"s":s or st([100,100,100])}
N={"r":(120,34),"a":(70,100),"b":(170,100),"a1":(40,166),"a2":(100,166),"b1":(140,166),"b2":(200,166)}
E=[("r","a",0),("r","b",6),("a","a1",18),("a","a2",22),("b","b1",26),("b","b2",30)]
L=[];i=1
# Ramas: crecen con trim path
for u,v,t0 in E:
    (x1,y1),(x2,y2)=N[u],N[v]
    sh={"ty":"sh","ks":st({"c":False,"v":[[x1,y1],[x2,y2]],"i":[[0,0],[0,0]],"o":[[0,0],[0,0]]})}
    stroke={"ty":"st","c":st([0.5,0.5,0.5,1]),"o":st(100),"w":st(3),"lc":2,"lj":2}
    trim={"ty":"tm","s":st(0),"e":anim([(t0,[0]),(t0+14,[100]),(FR-20,[100]),(FR-6,[0])]),"o":st(0),"m":1}
    L.append(layer(i,f"rama {u}-{v}",[{"ty":"gr","it":[sh,stroke,trim,tr()]}],ks(),"rama"));i+=1
def nodo(nm,pos,t0,r,cl,extra_p=None):
    el={"ty":"el","p":st([0,0]),"s":st([r*2,r*2])}
    fl={"ty":"fl","c":st([1,1,1,1]),"o":st(100),"r":1}
    stroke={"ty":"st","c":st([0.2,0.2,0.6,1]),"o":st(100),"w":st(3),"lc":2,"lj":2}
    s=anim([(t0,[0,0,100]),(t0+10,[110,110,100]),(t0+16,[100,100,100]),(FR-20,[100,100,100]),(FR-8,[0,0,100])])
    return layer(0,nm,[{"ty":"gr","it":[el,fl,stroke,tr()]}],ks(extra_p or pos,s=s),cl)
nodos=[("r",0,16,"nodo-raiz"),("a",12,13,"nodo"),("b",18,13,"nodo"),("a1",30,11,"hoja"),("a2",34,11,"hoja-a"),("b1",38,11,"hoja-b"),("b2",42,11,"hoja")]
for nm,t0,r,cl in nodos:
    x,y=N[nm]; p=None
    if nm in("a2","b1"):  # cruce: intercambian lugar entre los cuadros 62 y 84
        x2,y2=N["b1"] if nm=="a2" else N["a2"]; arc=-45 if nm=="a2" else 12
        p={"a":1,"k":[{"t":62,"s":[x,y,0],"to":[ (x2-x)/3, arc,0],"ti":[-(x2-x)/3, arc,0],"i":{"x":0.45,"y":1},"o":{"x":0.55,"y":0}},
                      {"t":84,"s":[x2,y2,0]}]}
    L2=nodo(nm,(x,y),t0,r,cl,p); L2["ind"]=i; i+=1; L.append(L2)
# Mutación: un destello en la hoja b2 (cuadros 96-112)
el={"ty":"el","p":st([0,0]),"s":anim([(96,[22,22]),(112,[48,48])])}
stroke={"ty":"st","c":st([0.5,0.2,0.3,1]),"o":anim([(96,[100]),(112,[0])]),"w":st(3),"lc":2,"lj":2}
L.append(layer(i,"mutación",[{"ty":"gr","it":[el,stroke,tr()]}],ks(N["b2"]),"mutacion"))
anim_json={"v":"5.12.2","fr":30,"ip":0,"op":FR,"w":240,"h":200,"nm":"arbol_evoluciona","ddd":0,"assets":[],"layers":list(reversed(L))}
from pathlib import Path
salida = Path(__file__).resolve().parents[2] / "static" / "lottie" / "arbol_evoluciona.json"
json.dump(anim_json, open(salida, "w"), separators=(",", ":"))
print("ok",len(L))
