/* Historia paso a paso (/historia/).
   El texto de cada paso está en la plantilla. Este archivo:
   1) muestra un paso a la vez (botones, índice y flechas del teclado);
   2) dibuja la escena de cada paso en SVG.
   Con "reducir movimiento" activado, cada escena aparece ya terminada. */
(() => {
    "use strict";
    const raiz = document.getElementById("historia");
    const datosNodo = document.getElementById("historia-datos");
    if (!raiz || !datosNodo) return;

    const DATOS = JSON.parse(datosNodo.textContent);
    const T = DATOS.textos;
    const ESTADIOS = DATOS.estadios;
    const quieto = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const NS = "http://www.w3.org/2000/svg";
    const lienzo = document.getElementById("historia-lienzo");
    const leyendaNodo = document.getElementById("historia-leyenda");
    const estadoNodo = document.getElementById("historia-estado");
    const controles = document.getElementById("historia-controles");
    const pasos = Array.from(raiz.querySelectorAll(".historia-paso"));
    const enlaces = Array.from(raiz.querySelectorAll(".historia-indice a"));
    const pistaNodo = document.getElementById("historia-pista");
    const anterior = document.getElementById("historia-anterior");
    const siguiente = document.getElementById("historia-siguiente");

    const fmt = (n) => Math.round(n).toLocaleString(document.documentElement.lang || "es-MX");
    const poner = (plantilla, valores) => plantilla.replace(/\{(\w+)\}/g, (_, k) => valores[k] ?? "");

    function el(tag, attrs, padre) {
        const e = document.createElementNS(NS, tag);
        for (const k in attrs || {}) e.setAttribute(k, attrs[k]);
        if (padre) padre.appendChild(e);
        return e;
    }
    function texto(tag, attrs, contenido, padre) {
        const e = el(tag, attrs, padre);
        e.textContent = contenido;
        return e;
    }

    let temporizadores = [];
    let animacion = 0;
    const luego = (ms, fn) => {
        if (quieto) { fn(); return; }
        temporizadores.push(setTimeout(fn, ms));
    };
    const limpiar = () => {
        temporizadores.forEach(clearTimeout);
        temporizadores = [];
        animacion++;
    };

    function nuevoSvg(ancho, alto, etiqueta, { ancho_minimo = false } = {}) {
        const svg = el("svg", { viewBox: `0 0 ${ancho} ${alto}`, role: "img", "aria-label": etiqueta });
        if (ancho_minimo) svg.classList.add("ancho");
        lienzo.appendChild(svg);
        return svg;
    }
    function leyenda(t) { leyendaNodo.textContent = t || ""; }
    function boton(t, fn, extra) {
        const b = document.createElement("button");
        b.type = "button";
        b.className = "boton-secundario";
        b.textContent = t;
        if (extra) Object.assign(b.dataset, extra);
        b.addEventListener("click", fn);
        controles.appendChild(b);
        return b;
    }
    function contar(nodo, fin) {
        if (!nodo) return;
        const sufijo = " " + T.km;
        if (quieto) { nodo.textContent = fmt(fin) + sufijo; return; }
        const id = animacion, t0 = performance.now(), dur = 2400;
        const paso = (t) => {
            if (id !== animacion) return;
            const k = Math.min(1, (t - t0) / dur);
            nodo.textContent = fmt(fin * (1 - (1 - k) ** 3)) + sufijo;
            if (k < 1) requestAnimationFrame(paso);
        };
        requestAnimationFrame(paso);
    }

    /* ---------- Mapa ---------- */
    const W = 640, H = 380;
    const px = (lon) => 30 + (lon + 125) / 59 * (W - 60);
    const py = (lat) => 20 + (49.5 - lat) / 25 * (H - 50);
    const km = (a, b) => {
        const R = 6371, r = Math.PI / 180;
        const dLa = (b.lat - a.lat) * r, dLo = (b.lon - a.lon) * r;
        const h = Math.sin(dLa / 2) ** 2 + Math.cos(a.lat * r) * Math.cos(b.lat * r) * Math.sin(dLo / 2) ** 2;
        return 2 * R * Math.asin(Math.sqrt(h));
    };
    let semilla = 7;
    const azar = () => { semilla = (semilla * 16807) % 2147483647; return (semilla - 1) / 2147483646; };
    let equipoElegido = "SEA";
    const nombre = (cod) => { const e = ESTADIOS.find((x) => x.codigo === cod); return e ? e.equipo : cod; };

    function giraAlAzar(cod) {
        semilla = 7 + cod.charCodeAt(0) + cod.charCodeAt(2);
        const casa = ESTADIOS.find((e) => e.codigo === cod);
        const otros = ESTADIOS.filter((e) => e.codigo !== cod);
        for (let i = otros.length - 1; i > 0; i--) {
            const j = Math.floor(azar() * (i + 1));
            [otros[i], otros[j]] = [otros[j], otros[i]];
        }
        const paradas = [casa];
        otros.slice(0, 12).forEach((o) => { paradas.push(o); if (azar() < 0.4) paradas.push(casa); });
        paradas.push(casa);
        return paradas;
    }
    const largo = (r) => r.slice(1).reduce((s, p, i) => s + km(r[i], p), 0);

    function mapa({ conGira = false, aparecer = false, alElegir } = {}) {
        const svg = nuevoSvg(W, H, T.mapa);
        if (window.KOZA_MAPA) {
            // Contorno de los países y fronteras de los estados (historia_mapa.js)
            el("path", { class: "h-estados", d: window.KOZA_MAPA.estados }, svg);
            el("path", { class: "h-tierra", d: window.KOZA_MAPA.tierra }, svg);
        } else {
            for (let lon = -120; lon <= -70; lon += 10) el("line", { class: "h-reticula", x1: px(lon), x2: px(lon), y1: 10, y2: H - 20 }, svg);
            for (let lat = 25; lat <= 45; lat += 5) el("line", { class: "h-reticula", x1: 20, x2: W - 20, y1: py(lat), y2: py(lat) }, svg);
        }
        const capaRuta = el("g", {}, svg);
        const capaPuntos = el("g", {}, svg);
        let total = 0;
        if (conGira) {
            const gira = giraAlAzar(equipoElegido);
            total = largo(gira);
            const d = gira.map((p, i) => (i ? "L" : "M") + px(p.lon).toFixed(1) + " " + py(p.lat).toFixed(1)).join(" ");
            const ruta = el("path", { class: "h-ruta", d }, capaRuta);
            if (!quieto) {
                const L = ruta.getTotalLength();
                ruta.style.strokeDasharray = L;
                ruta.style.strokeDashoffset = L;
                ruta.style.transition = "stroke-dashoffset 2.4s ease-in-out";
                requestAnimationFrame(() => requestAnimationFrame(() => { ruta.style.strokeDashoffset = 0; }));
            }
        }
        ESTADIOS.forEach((e, i) => {
            const activo = conGira && e.codigo === equipoElegido;
            const c = el("circle", {
                class: "h-estadio" + (activo ? " activo" : "") + (aparecer ? " h-aparece" : ""),
                cx: px(e.lon), cy: py(e.lat), r: activo ? 9 : 7,
                tabindex: 0, role: "button", "aria-label": `${e.equipo} (${e.codigo})`,
            }, capaPuntos);
            texto("title", {}, `${e.equipo} · ${e.estadio}`, c);
            if (aparecer) luego(60 + i * 45, () => c.classList.add("visible"));
            const elegir = () => alElegir(e.codigo);
            c.addEventListener("click", elegir);
            c.addEventListener("keydown", (ev) => {
                if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); elegir(); }
            });
        });
        if (conGira) {
            const e = ESTADIOS.find((x) => x.codigo === equipoElegido);
            texto("text", { class: "h-etiqueta", x: px(e.lon) + 12, y: py(e.lat) - 10 }, e.codigo, capaPuntos);
        }
        return total;
    }

    /* ---------- Árboles ---------- */
    const N = (t, ...h) => ({ t, h });
    const padreA = () => N(T.combinar,
        N(T.intercambiar, N("SEA–NYA"), N("BOS–TEX")),
        N(T.invertir, N("LAN–CHN"), N(T.casa)));
    const padreB = () => N(T.combinar,
        N(T.invertir, N("MIA–ATL"), N(T.visita)),
        N(T.intercambiar, N("HOU–COL"), N("DET–SDN")));

    function acomodar(raizArbol, x0, ancho, y0, paso) {
        const hojas = [];
        (function rec(n, d) { n.d = d; if (!n.h.length) hojas.push(n); n.h.forEach((h) => rec(h, d + 1)); })(raizArbol, 0);
        hojas.forEach((h, i) => { h.x = x0 + ancho * (i + 0.5) / hojas.length; });
        (function pos(n) {
            n.h.forEach(pos);
            if (n.h.length) n.x = n.h.reduce((s, h) => s + h.x, 0) / n.h.length;
            n.y = y0 + n.d * paso;
        })(raizArbol);
        return raizArbol;
    }
    function recorrer(raizArbol) {
        const cola = [raizArbol], orden = [];
        while (cola.length) { const n = cola.shift(); orden.push(n); cola.push(...n.h); }
        return orden;
    }
    function arbol(svg, raizArbol, { aparecer = false, retraso = 0, marcas = new Map() } = {}) {
        const g = el("g", {}, svg);
        const ramas = el("g", {}, g);
        const nodos = el("g", {}, g);
        recorrer(raizArbol).forEach((n, i) => {
            const t = retraso + i * 220;
            n.h.forEach((h) => {
                const l = el("line", { class: "h-rama" + (aparecer ? " oculta" : ""), x1: n.x, y1: n.y + 15, x2: h.x, y2: h.y - 15 }, ramas);
                if (aparecer) luego(t + 220, () => l.classList.remove("oculta"));
            });
            const clases = ["h-nodo"];
            if (!n.h.length) clases.push("hoja");
            if (marcas.get(n)) clases.push(marcas.get(n));
            if (aparecer) clases.push("h-aparece");
            const ng = el("g", { class: clases.join(" ") }, nodos);
            const ancho = Math.max(54, n.t.length * 8.6 + 16);
            el("rect", { x: n.x - ancho / 2, y: n.y - 15, width: ancho, height: 30, rx: n.h.length ? 6 : 15 }, ng);
            texto("text", { x: n.x, y: n.y + 5, "text-anchor": "middle" }, n.t, ng);
            n.g = ng;
            if (aparecer) luego(t, () => ng.classList.add("visible"));
        });
    }

    /* ---------- Escenas ---------- */
    const ESCENAS = {
        estadios() {
            mapa({
                aparecer: true,
                alElegir: (cod) => { equipoElegido = cod; pista(poner(T.elegiste, { equipo: nombre(cod) })); },
            });
        },
        viajes(paso) {
            const pintar = () => {
                lienzo.innerHTML = "";
                const total = mapa({ conGira: true, alElegir: (cod) => { equipoElegido = cod; limpiar(); pintar(); } });
                contar(paso.querySelector("[data-cifra-km]"), total);
                leyenda(poner(T.gira, { equipo: nombre(equipoElegido) }));
            };
            pintar();
        },
        arbol() {
            const svg = nuevoSvg(640, 330, T.arbol, { ancho_minimo: true });
            arbol(svg, acomodar(padreA(), 20, 600, 40, 110), { aparecer: true });
            boton(T.ver_otra_vez, () => mostrar(actual));
        },
        cruce() {
            const svg = nuevoSvg(640, 470, T.cruce, { ancho_minimo: true });
            const A = acomodar(padreA(), 0, 310, 46, 64);
            const B = acomodar(padreB(), 330, 310, 46, 64);
            texto("text", { class: "h-rotulo", x: 155, y: 16, "text-anchor": "middle" }, T.padre_a, svg);
            texto("text", { class: "h-rotulo", x: 485, y: 16, "text-anchor": "middle" }, T.padre_b, svg);
            arbol(svg, A);
            arbol(svg, B);
            luego(700, () => {
                recorrer(A.h[0]).forEach((n) => n.g.classList.add("marca-a"));
                recorrer(B.h[0]).forEach((n) => n.g.classList.add("marca-b"));
            });
            const hijo = acomodar(N(T.combinar, padreA().h[0], padreB().h[0]), 120, 400, 300, 64);
            texto("text", { class: "h-rotulo", x: 320, y: 272, "text-anchor": "middle" }, T.hijo, svg);
            const marcas = new Map();
            recorrer(hijo.h[0]).forEach((n) => marcas.set(n, "marca-a"));
            recorrer(hijo.h[1]).forEach((n) => marcas.set(n, "marca-b"));
            arbol(svg, hijo, { aparecer: true, retraso: 1500, marcas });
            boton(T.ver_otra_vez, () => mostrar(actual));
        },
        mutacion() {
            const svg = nuevoSvg(640, 330, T.mutacion, { ancho_minimo: true });
            const hijo = acomodar(N(T.combinar, padreA().h[0], padreB().h[0]), 20, 600, 40, 110);
            arbol(svg, hijo);
            const hoja = hijo.h[0].h[0];
            luego(900, () => { hoja.g.classList.add("cambio"); hoja.g.querySelector("text").textContent = "SEA–OAK"; });
            boton(T.ver_otra_vez, () => mostrar(actual));
        },
        generaciones() {
            const svg = nuevoSvg(640, 380, "");
            const X0 = 70, X1 = 390, Y0 = 40, Y1 = 320, G = 20;
            const xg = (g) => X0 + (X1 - X0) * g / G;
            const yv = (v) => Y1 - (Y1 - Y0) * (v - 80) / 50;  // eje de 80 a 130; azar = 100
            [80, 90, 100, 110, 120, 130].forEach((v) => {
                el("line", { class: "h-eje", x1: X0, x2: X1, y1: yv(v), y2: yv(v) }, svg);
                texto("text", { class: "h-eje-texto", x: X0 - 8, y: yv(v) + 4, "text-anchor": "end" }, v, svg);
            });
            [0, 5, 10, 15, 20].forEach((g) => texto("text", { class: "h-eje-texto", x: xg(g), y: Y1 + 20, "text-anchor": "middle" }, g, svg));
            texto("text", { class: "h-rotulo-suave", x: (X0 + X1) / 2, y: Y1 + 42, "text-anchor": "middle" }, T.generacion, svg);
            texto("text", { class: "h-rotulo-suave", x: 14, y: 26 }, T.eje_viaje, svg);
            el("line", { class: "h-azar", x1: X0, x2: X1, y1: yv(100), y2: yv(100) }, svg);
            texto("text", { class: "h-rotulo-suave", x: X1 + 6, y: yv(100) + 4 }, T.azar, svg);
            const curva = el("path", { class: "h-curva" }, svg);
            const etiquetaFin = el("text", { class: "h-rotulo", "text-anchor": "end" }, svg);
            const celdas = [];
            for (let f = 0; f < 8; f++) for (let c = 0; c < 6; c++) {
                celdas.push(el("rect", { class: "h-celda", x: 450 + c * 28, y: 52 + f * 30, width: 22, height: 22, rx: 4 }, svg));
            }
            texto("text", { class: "h-rotulo-suave", x: 450, y: 36 }, T.poblacion, svg);
            texto("text", { class: "h-rotulo-suave", x: 450, y: 312 }, T.mas_color, svg);

            const motores = {
                tesis: { nombre: T.motor_tesis, fin: DATOS.indice.tesis, resultado: T.fin_tesis, semilla: 11 },
                bloques: { nombre: T.motor_bloques, fin: DATOS.indice.bloques, resultado: T.fin_bloques, semilla: 23 },
            };
            const correr = (clave) => {
                controles.querySelectorAll("button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.motor === clave)));
                const m = motores[clave];
                semilla = m.semilla;
                // Curva de ejemplo: solo el punto final es una cifra real.
                const inicio = 128, vals = [inicio], norma = 1 - Math.exp(-G / 5);
                for (let g = 1; g <= G; g++) {
                    const k = (1 - Math.exp(-g / 5)) / norma;
                    vals.push(inicio + (m.fin - inicio) * k + (g < G ? (azar() - 0.5) * 2 : 0));
                }
                svg.setAttribute("aria-label", poner(T.curva, { motor: m.nombre, inicio, fin: m.fin, resultado: m.resultado }));
                const pintar = (hasta) => {
                    curva.setAttribute("d", vals.slice(0, hasta + 1).map((v, g) => (g ? "L" : "M") + xg(g) + " " + yv(v)).join(" "));
                    const v = vals[hasta];
                    const bueno = Math.max(0, Math.min(1, (130 - v) / 50));
                    celdas.forEach((c, i) => {
                        const r = ((i * 37) % 48) / 48;
                        c.style.fillOpacity = (0.15 + 0.85 * Math.min(1, bueno * 0.9 + r * 0.5)).toFixed(2);
                    });
                    if (hasta === G) {
                        etiquetaFin.setAttribute("x", X1 - 4);
                        etiquetaFin.setAttribute("y", yv(v) + (v > 100 ? -26 : 30));
                        etiquetaFin.textContent = m.resultado;
                        estadoNodo.textContent = poner(T.termino, { motor: m.nombre, resultado: m.resultado });
                    } else {
                        etiquetaFin.textContent = "";
                        estadoNodo.textContent = poner(T.progreso, { motor: m.nombre, g: hasta, total: G });
                    }
                };
                const id = ++animacion;
                if (quieto) { pintar(G); return; }
                let g = 0;
                const tic = () => {
                    if (id !== animacion) return;
                    pintar(g);
                    if (g++ < G) temporizadores.push(setTimeout(tic, 160));
                };
                tic();
            };
            boton(T.motor_tesis, () => correr("tesis"), { motor: "tesis" });
            boton(T.motor_bloques, () => correr("bloques"), { motor: "bloques" });
            correr("tesis");
        },
        resultado() {
            const svg = nuevoSvg(640, 260, poner(T.barras, { tesis: DATOS.indice.tesis, bloques: DATOS.indice.bloques }));
            const filas = [
                [T.barra_tesis, DATOS.indice.tesis, "h-barra-tesis"],
                [T.barra_azar, 100, "h-barra-azar"],
                [T.barra_bloques, DATOS.indice.bloques, "h-barra-bloques"],
            ];
            const esc = 380 / 125;
            filas.forEach(([etiqueta, v, clase], i) => {
                const y = 30 + i * 74;
                texto("text", { class: "h-rotulo", x: 0, y }, etiqueta, svg);
                const r = el("rect", { class: "h-barra " + clase, x: 0, y: y + 10, height: 28, rx: 4, width: quieto ? v * esc : 0 }, svg);
                texto("text", { class: "h-eje-texto", x: v * esc + 10, y: y + 30 }, v, svg);
                luego(150 + i * 300, () => r.setAttribute("width", v * esc));
            });
            el("line", { class: "h-azar", x1: 100 * esc, x2: 100 * esc, y1: 10, y2: 250 }, svg);
        },
    };

    /* ---------- Navegación ---------- */
    let actual = 0;
    function pista(t) { pistaNodo.textContent = t || ""; }
    function mostrar(i, { enfocar = false } = {}) {
        limpiar();
        actual = Math.max(0, Math.min(pasos.length - 1, i));
        const paso = pasos[actual];
        pasos.forEach((p, k) => p.classList.toggle("actual", k === actual));
        enlaces.forEach((a, k) => (k === actual ? a.setAttribute("aria-current", "step") : a.removeAttribute("aria-current")));
        lienzo.innerHTML = "";
        controles.innerHTML = "";
        leyenda("");
        estadoNodo.textContent = "";
        ESCENAS[paso.dataset.escena](paso);
        anterior.disabled = actual === 0;
        siguiente.disabled = actual === pasos.length - 1;
        pista(actual === 0 ? T.teclado : "");
        try { history.replaceState(null, "", "#" + paso.id); } catch (e) { /* sin historial */ }
        if (enfocar) {
            const titulo = paso.querySelector("h2");
            titulo.setAttribute("tabindex", "-1");
            titulo.focus({ preventScroll: true });
        }
    }

    raiz.classList.add("con-js");
    document.getElementById("historia-escena").hidden = false;
    document.getElementById("historia-navegacion").hidden = false;
    enlaces.forEach((a, k) => a.addEventListener("click", (ev) => { ev.preventDefault(); mostrar(k, { enfocar: true }); }));
    anterior.addEventListener("click", () => mostrar(actual - 1));
    siguiente.addEventListener("click", () => mostrar(actual + 1));
    document.addEventListener("keydown", (ev) => {
        if (ev.target.closest("input, select, textarea, [contenteditable]")) return;
        if (ev.key === "ArrowRight") mostrar(actual + 1);
        if (ev.key === "ArrowLeft") mostrar(actual - 1);
    });
    const pasoDelEnlace = () => pasos.findIndex((p) => "#" + p.id === location.hash);
    window.addEventListener("hashchange", () => { const k = pasoDelEnlace(); if (k >= 0 && k !== actual) mostrar(k); });
    const desdeEnlace = pasoDelEnlace();
    mostrar(desdeEnlace >= 0 ? desdeEnlace : 0);
})();
