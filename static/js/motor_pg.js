/* El motor PG por dentro (/demo/motor-pg/).
   Lee <script id="motor-pg-datos"> (tesis.motor_pg):
     {regla: "por(entre(...), 0.587)", a_mano: costo,
      generaciones: [{mejor, mediana, individuos: [[árbol, costo, origen], ...]}], textos}
   - Dibuja el árbol de la regla aprendida (texto de DEAP en notación prefija).
   - Gráfica: cada punto es un árbol de la población; líneas del mejor y la mediana.
   - Control de generación (deslizador y Reproducir) y el mejor árbol de esa generación.
   Sin JavaScript, la página muestra la fórmula y la tabla de generaciones. */
(function () {
    "use strict";
    const nodo = document.getElementById("motor-pg-datos");
    if (!nodo) return;
    const D = JSON.parse(nodo.textContent);
    const T = D.textos;
    const idioma = document.documentElement.lang || "es";
    const NS = "http://www.w3.org/2000/svg";
    const el = (tag, attrs, padre, texto) => {
        const e = document.createElementNS(NS, tag);
        for (const [k, v] of Object.entries(attrs || {})) e.setAttribute(k, v);
        if (texto !== undefined) e.textContent = texto;
        if (padre) padre.appendChild(e);
        return e;
    };
    const poner = (t, v) => t.replace(/\{(\w+)\}/g, (_m, k) => v[k]);
    const fmt = (n, d) => new Intl.NumberFormat(idioma, { minimumFractionDigits: d, maximumFractionDigits: d }).format(n);
    const millones = (c) => fmt(c / 1e6, 3);

    /* ---------- Árbol: leer "por(entre(a, b), 0.5)" ---------- */
    function leer(texto) {
        const fichas = texto.match(/[A-Za-z_]\w*|-?\d+(?:\.\d+)?(?:e-?\d+)?|[(),]/g) || [];
        let i = 0;
        function nodo() {
            const f = fichas[i++];
            const n = { t: f, h: [] };
            if (fichas[i] === "(") {
                i++;
                while (fichas[i] !== ")") { n.h.push(nodo()); if (fichas[i] === ",") i++; }
                i++;
            }
            return n;
        }
        return nodo();
    }
    function etiqueta(t) {
        if (T.piezas[t]) return T.piezas[t];
        const n = Number(t);
        if (Number.isFinite(n)) return new Intl.NumberFormat(idioma, { maximumFractionDigits: 3, useGrouping: false }).format(n);
        return t;
    }
    // Acomodo: cada hoja ocupa su ancho; un padre queda centrado sobre sus hijos
    const ALTO_NIVEL = 74, ALTO_CAJA = 34, SEP = 14;
    function medir(n) {
        n.texto = etiqueta(n.t);
        n.ancho = Math.max(48, n.texto.length * 9.2 + 22);
        n.h.forEach(medir);
        const hijos = n.h.reduce((s, h) => s + h.total, 0) + SEP * Math.max(0, n.h.length - 1);
        n.total = Math.max(n.ancho, hijos);
    }
    function colocar(n, x0, nivel) {
        n.y = 24 + nivel * ALTO_NIVEL;
        if (!n.h.length) { n.x = x0 + n.total / 2; return; }
        const hijos = n.h.reduce((s, h) => s + h.total, 0) + SEP * (n.h.length - 1);
        let x = x0 + (n.total - hijos) / 2;
        for (const h of n.h) { colocar(h, x, nivel + 1); x += h.total + SEP; }
        n.x = (n.h[0].x + n.h[n.h.length - 1].x) / 2;
    }
    function profundidad(n) { return 1 + Math.max(0, ...n.h.map(profundidad)); }
    function dibujarArbol(contenedor, texto) {
        const raiz = leer(texto);
        medir(raiz);
        colocar(raiz, 8, 0);
        const ancho = raiz.total + 16;
        const alto = profundidad(raiz) * ALTO_NIVEL;
        const svg = el("svg", { viewBox: `0 0 ${ancho} ${alto}`, role: "img", "aria-label": T.arbol + ". " + texto, class: "pg-arbol" });
        // Tamaño natural: en pantallas angostas se desliza en vez de achicar la letra
        svg.style.width = ancho + "px";
        svg.style.minWidth = ancho + "px";
        const ramas = el("g", {}, svg), cajas = el("g", {}, svg);
        (function dibujar(n) {
            for (const h of n.h) {
                el("line", { class: "pg-rama", x1: n.x, y1: n.y + ALTO_CAJA / 2, x2: h.x, y2: h.y - ALTO_CAJA / 2 }, ramas);
                dibujar(h);
            }
            const g = el("g", { class: "pg-nodo" + (n.h.length ? "" : " pg-hoja") }, cajas);
            el("rect", { x: n.x - n.ancho / 2, y: n.y - ALTO_CAJA / 2, width: n.ancho, height: ALTO_CAJA, rx: n.h.length ? 6 : ALTO_CAJA / 2 }, g);
            el("text", { x: n.x, y: n.y + 5.5, "text-anchor": "middle" }, g, n.texto);
        })(raiz);
        contenedor.replaceChildren(svg);
        return raiz;
    }
    const lienzoRegla = document.getElementById("pg-arbol-regla");
    if (lienzoRegla) dibujarArbol(lienzoRegla, D.regla);

    /* ---------- Gráfica de generaciones ---------- */
    const figura = document.getElementById("pg-evolucion");
    if (!figura || !D.generaciones.length) return;
    figura.hidden = false;
    const G = D.generaciones;
    const W = 720, H = 360, M = { i: 64, d: 16, a: 40, b: 46 };
    const todos = G.flatMap((g) => g.individuos.map((x) => x[1])).sort((a, b) => a - b);
    const yMin = Math.min(...G.map((g) => g.mejor), D.a_mano) * 0.995;
    const yMax = Math.max(todos[Math.floor(todos.length * 0.75)], ...G.map((g) => g.mediana)) * 1.01;
    const px = (gen) => M.i + (W - M.i - M.d) * (G.length === 1 ? 0.5 : gen / (G.length - 1));
    const py = (c) => M.a + (H - M.a - M.b) * (1 - (Math.min(c, yMax) - yMin) / (yMax - yMin));
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-labelledby": "pg-grafica-titulo", class: "pg-grafica" });
    el("title", { id: "pg-grafica-titulo" }, svg, T.grafica);
    const banda = el("rect", { class: "pg-banda", y: M.a, height: H - M.a - M.b, width: 28 }, svg);
    // Ejes
    for (let k = 0; k <= 4; k++) {
        const c = yMin + (yMax - yMin) * k / 4;
        el("line", { class: "pg-rejilla", x1: M.i, x2: W - M.d, y1: py(c), y2: py(c) }, svg);
        el("text", { class: "pg-eje", x: M.i - 8, y: py(c) + 5, "text-anchor": "end" }, svg, fmt(c / 1e6, 2));
    }
    G.forEach((_g, i) => el("text", { class: "pg-eje", x: px(i), y: H - M.b + 22, "text-anchor": "middle" }, svg, String(i)));
    el("text", { class: "pg-eje pg-eje-titulo", x: (M.i + W - M.d) / 2, y: H - 4, "text-anchor": "middle" }, svg, T.eje_x);
    el("text", { class: "pg-eje pg-eje-titulo", x: 14, y: 22, "text-anchor": "start" }, svg, T.eje_y);
    // Población: un punto por árbol (los de costo muy alto quedan como triángulo arriba)
    const puntos = el("g", { class: "pg-poblacion" }, svg);
    G.forEach((g, i) => g.individuos.forEach(([, c], j) => {
        const x = px(i) + ((j * 7) % 19) - 9;
        if (c > yMax) el("path", { class: "pg-fuera", d: `M${x - 4} ${M.a - 2} L${x + 4} ${M.a - 2} L${x} ${M.a - 9} z` }, puntos);
        else el("circle", { cx: x, cy: py(c), r: 3.2 }, puntos);
    }));
    // Líneas
    el("line", { class: "pg-mano", x1: M.i, x2: W - M.d, y1: py(D.a_mano), y2: py(D.a_mano) }, svg);
    el("polyline", { class: "pg-mediana", points: G.map((g, i) => `${px(i)},${py(g.mediana)}`).join(" ") }, svg);
    el("polyline", { class: "pg-mejor", points: G.map((g, i) => `${px(i)},${py(g.mejor)}`).join(" ") }, svg);
    G.forEach((g, i) => el("circle", { class: "pg-mejor-punto", cx: px(i), cy: py(g.mejor), r: 5 }, svg));
    const marca = el("circle", { class: "pg-marca", r: 9 }, svg);
    // Tocar una columna elige esa generación
    G.forEach((_g, i) => {
        const r = el("rect", { class: "pg-columna", x: px(i) - 14, y: M.a, width: 28, height: H - M.a - M.b }, svg);
        r.addEventListener("click", () => { detener(); elegir(i); });
    });
    document.getElementById("pg-grafica").appendChild(svg);

    // Leyenda con muestra de cada línea (forma, no solo color)
    const leyenda = document.getElementById("pg-leyenda");
    for (const [clase, texto, forma] of [
        ["pg-mejor", T.mejor, "line"], ["pg-mediana", T.mediana, "line"], ["pg-mano", T.a_mano, "line"],
        ["pg-poblacion", T.arbolito, "circle"], ["pg-fuera", T.fuera, "path"]]) {
        const li = document.createElement("li");
        const m = el("svg", { viewBox: "0 0 36 14", width: 36, height: 14, "aria-hidden": "true" }, li);
        if (forma === "line") el("line", { class: clase, x1: 2, x2: 34, y1: 7, y2: 7 }, m);
        else if (forma === "circle") el("circle", { cx: 18, cy: 7, r: 4 }, el("g", { class: clase }, m));
        else el("path", { class: clase, d: "M13 12 L23 12 L18 2 z" }, m);
        li.append(" " + texto);
        leyenda.appendChild(li);
    }

    /* ---------- Árbol genealógico: una fila por generación, de mejor (izquierda) a peor ---------- */
    // individuos: [árbol, costo, origen, id, padres (ids de la generación anterior)]
    const conPadres = G.some((g) => g.individuos.some((x) => x[4] && x[4].length));
    const donde = {};
    G.forEach((g, i) => g.individuos.forEach((x, k) => { donde[x[3]] = [i, k]; }));
    const clase = (c) => (c < D.a_mano ? 0 : c < D.a_mano * 1.01 ? 1 : c < D.a_mano * 1.05 ? 2 : 3);
    const POB = Math.max(...G.map((g) => g.individuos.length));
    const GW = 70 + POB * 26, GH = 30 + G.length * 52;
    const gx = (k) => 70 + k * 26 + 13, gy = (i) => 26 + i * 52;
    const lienzoGenea = document.getElementById("pg-genealogia");
    let lineas = {}, nodos = {};
    if (lienzoGenea && conPadres) {
        const sg = el("svg", { viewBox: `0 0 ${GW} ${GH}`, role: "img", "aria-labelledby": "pg-genealogia-titulo", class: "pg-genealogia" });
        sg.style.minWidth = Math.min(GW, 620) + "px";
        el("title", { id: "pg-genealogia-titulo" }, sg, T.genealogia);
        G.forEach((_g, i) => el("text", { class: "pg-eje", x: 4, y: gy(i) + 5 }, sg, poner(T.gen_corta, { gen: i })));
        const capaL = el("g", { class: "pg-lineas" }, sg), capaN = el("g", {}, sg);
        G.forEach((g, i) => g.individuos.forEach(([, c, o, id, padres], k) => {
            for (const p of padres || []) {
                const [pi, pk] = donde[p];
                lineas[id + "-" + p] = el("line", { class: o === "elite" ? "pg-linea pg-linea-elite" : "pg-linea",
                    x1: gx(pk), y1: gy(pi) + 8, x2: gx(k), y2: gy(i) - 8 }, capaL);
            }
            const n = el("circle", { class: "pg-gen-nodo pg-c" + clase(c), cx: gx(k), cy: gy(i), r: 8 }, capaN);
            el("title", {}, n, poner(T.lugar, { pos: k + 1, n: g.individuos.length, gen: i }) + " · " + millones(c));
            n.addEventListener("click", () => { detener(); elegir(i, k); });
            nodos[id] = n;
        }));
        lienzoGenea.appendChild(sg);
        const ley = document.getElementById("pg-genealogia-leyenda");
        [T.clase0, T.clase1, T.clase2, T.clase3].forEach((t, c) => {
            const li = document.createElement("li");
            const m = el("svg", { viewBox: "0 0 16 16", width: 16, height: 16, "aria-hidden": "true" }, li);
            el("circle", { class: "pg-gen-nodo pg-c" + c, cx: 8, cy: 8, r: 6 }, m);
            li.append(" " + t);
            ley.appendChild(li);
        });
        const li = document.createElement("li");
        const m = el("svg", { viewBox: "0 0 36 14", width: 36, height: 14, "aria-hidden": "true" }, li);
        el("line", { class: "pg-linea pg-linaje", x1: 2, x2: 34, y1: 7, y2: 7 }, m);
        li.append(" " + T.linaje);
        ley.appendChild(li);
    } else if (lienzoGenea) lienzoGenea.closest("[data-genealogia]")?.setAttribute("hidden", "");
    function marcarLinaje(id) {
        Object.values(lineas).forEach((l) => l.classList.remove("pg-linaje"));
        Object.values(nodos).forEach((n) => n.classList.remove("pg-en-linaje", "pg-elegido"));
        if (!nodos[id]) return;
        nodos[id].classList.add("pg-elegido");
        const vistos = new Set();
        (function subir(x) {
            if (vistos.has(x)) return;
            vistos.add(x);
            nodos[x].classList.add("pg-en-linaje");
            const [i, k] = donde[x];
            for (const p of G[i].individuos[k][4] || []) {
                if (lineas[x + "-" + p]) lineas[x + "-" + p].classList.add("pg-linaje");
                subir(p);
            }
        })(id);
    }

    /* ---------- Generación y árbol elegidos ---------- */
    const rango = document.getElementById("pg-generacion");
    const estado = document.getElementById("pg-estado");
    const origenes = document.getElementById("pg-origenes");
    const tituloMejor = document.getElementById("pg-mejor-titulo");
    const lienzoGen = document.getElementById("pg-arbol-generacion");
    const vinoDe = document.getElementById("pg-vino-de");
    const formula = document.getElementById("pg-mejor-formula");
    const selectArbol = document.getElementById("pg-arbol-lugar");
    function elegir(i, k = 0) {
        const g = G[i];
        rango.value = i;
        banda.setAttribute("x", px(i) - 14);
        marca.setAttribute("cx", px(i));
        marca.setAttribute("cy", py(g.mejor));
        estado.textContent = poner(T.estado, { gen: i, total: G.length - 1, mejor: millones(g.mejor), mediana: millones(g.mediana) });
        const cuenta = {};
        g.individuos.forEach(([, , o]) => { cuenta[o] = (cuenta[o] || 0) + 1; });
        const lista = ["elite", "cruce", "mutacion", "seleccion", "nuevo"].filter((o) => cuenta[o])
            .map((o) => poner(T.origen[o], { n: cuenta[o] }));
        origenes.textContent = poner(T.origenes, { n: g.individuos.length, lista: lista.join(", ") });
        if (selectArbol) {
            selectArbol.replaceChildren(...g.individuos.map(([, c], j) => {
                const op = document.createElement("option");
                op.value = j;
                op.textContent = poner(T.opcion, { pos: j + 1, costo: millones(c) });
                return op;
            }));
            selectArbol.value = k;
        }
        const [arbol, costo, origen, id, padres] = g.individuos[k];
        const raiz = dibujarArbol(lienzoGen, arbol);
        let piezas = 0;
        (function contar(n) { piezas++; n.h.forEach(contar); })(raiz);
        tituloMejor.textContent = k === 0
            ? poner(T.mejor_de, { gen: i, nodos: piezas })
            : poner(T.lugar_de, { pos: k + 1, gen: i, nodos: piezas });
        let texto = poner(T.costo_de, { costo: millones(costo) }) + " " + (T.vino_de[origen] || "");
        if (padres && padres.length) {
            texto += " " + poner(padres.length > 1 ? T.padres : T.padre,
                { a: donde[padres[0]][1] + 1, b: padres[1] !== undefined ? donde[padres[1]][1] + 1 : "", gen: i - 1 });
        }
        vinoDe.textContent = texto;
        formula.textContent = arbol;
        marcarLinaje(id);
    }
    if (selectArbol) selectArbol.addEventListener("change", () => { detener(); elegir(Number(rango.value), Number(selectArbol.value)); });
    let reloj = null;
    const boton = document.getElementById("pg-reproducir");
    function detener() { clearInterval(reloj); reloj = null; boton.textContent = T.reproducir; }
    boton.addEventListener("click", () => {
        if (reloj) { detener(); return; }
        let i = Number(rango.value) >= G.length - 1 ? 0 : Number(rango.value);
        elegir(i);
        boton.textContent = T.pausar;
        reloj = setInterval(() => {
            i++;
            if (i >= G.length) { detener(); return; }
            elegir(i);
        }, 1100);
    });
    rango.addEventListener("input", () => { detener(); elegir(Number(rango.value)); });
    // Al llegar: el mejor árbol de la última generación y toda su familia
    elegir(conPadres ? G.length - 1 : 0);
})();
