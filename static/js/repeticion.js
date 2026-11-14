/* Repetición de la temporada 2023 (/demo/2023/).
   1) Gráfica: kilómetros del mejor calendario en cada generación del motor,
      con líneas del calendario oficial y del mejor al azar.
   2) Mapa: un círculo por equipo, del tamaño de sus kilómetros (oficial o motor).
   Sin JavaScript la página se lee igual: las tablas tienen todas las cifras.
   Con "reducir movimiento" activado, la repetición salta al final sin animar. */
(() => {
    "use strict";
    const nodo = document.getElementById("repeticion-datos");
    if (!nodo) return;
    const D = JSON.parse(nodo.textContent);
    const T = D.textos;
    const NS = "http://www.w3.org/2000/svg";
    const quieto = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const idioma = document.documentElement.lang || "es-MX";
    const fmt = (n) => Math.round(n).toLocaleString(idioma);
    const millones = (n) => (n / 1e6).toLocaleString(idioma, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    const poner = (p, v) => p.replace(/\{(\w+)\}/g, (_, k) => v[k] ?? "");

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

    /* ---------- 1. Gráfica de generaciones ---------- */
    const gens = D.motor.generaciones;
    const total = gens.length;
    const figura = document.getElementById("repeticion-figura");
    const estado = document.getElementById("repeticion-estado");
    const rango = document.getElementById("repeticion-generacion");
    const boton = document.getElementById("repeticion-reproducir");
    figura.hidden = false;

    const W = 640, H = 320, x0 = 70, x1 = 620, y0 = 30, y1 = 270;
    const valores = [D.oficial.km, D.azar.km, ...gens];
    const minimo = Math.min(...valores) * 0.97, maximoKm = Math.max(...valores) * 1.02;
    const X = (g) => x0 + (g / (total - 1)) * (x1 - x0);
    const Y = (km) => y1 - ((km - minimo) / (maximoKm - minimo)) * (y1 - y0);

    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": T.grafica });
    document.getElementById("repeticion-grafica").appendChild(svg);
    el("line", { x1: x0, y1: y1, x2: x1, y2: y1, class: "r-eje" }, svg);
    el("line", { x1: x0, y1: y0, x2: x0, y2: y1, class: "r-eje" }, svg);

    // Las etiquetas van en una leyenda de HTML, no dentro del SVG: así se leen
    // con letra de tamaño normal también en el teléfono.
    el("line", { x1: x0, y1: Y(D.azar.km), x2: x1, y2: Y(D.azar.km), class: "r-azar" }, svg);
    el("line", { x1: x0, y1: Y(D.oficial.km), x2: x1, y2: Y(D.oficial.km), class: "r-oficial" }, svg);
    const curva = el("polyline", { class: "r-motor", points: "" }, svg);
    const punto = el("circle", { r: 8, class: "r-punto" }, svg);

    const leyendaNodo = document.getElementById("repeticion-leyenda");
    function itemLeyenda(clase, contenido) {
        const li = document.createElement("li");
        const muestra = document.createElement("span");
        muestra.className = `muestra ${clase}`;
        muestra.setAttribute("aria-hidden", "true");
        const t = document.createElement("span");
        t.textContent = contenido;
        li.append(muestra, t);
        leyendaNodo.appendChild(li);
        return t;
    }
    const textoMotor = itemLeyenda("m-motor", "");
    itemLeyenda("m-oficial", `${T.oficial}: ${millones(D.oficial.km)} ${T.millones}`);
    itemLeyenda("m-azar", `${T.azar}: ${millones(D.azar.km)} ${T.millones}`);
    itemLeyenda("m-eje", poner(T.ejes, { min: millones(minimo), max: millones(maximoKm), ultima: total - 1 }));

    function dibujar(g) {
        curva.setAttribute("points", gens.slice(0, g + 1).map((km, i) => `${X(i).toFixed(1)},${Y(km).toFixed(1)}`).join(" "));
        punto.setAttribute("cx", X(g));
        punto.setAttribute("cy", Y(gens[g]));
        textoMotor.textContent = `${T.motor}: ${millones(gens[g])} ${T.millones}`;
        rango.value = g;
        estado.textContent = poner(T.estado, { gen: g, total: total - 1, km: fmt(gens[g]) }) +
            (D.motor.cumple[g] ? "" : ` ${T.incumple}`);
        punto.classList.toggle("r-incumple", !D.motor.cumple[g]);
    }

    let temporizador = null;
    function parar() {
        clearInterval(temporizador);
        temporizador = null;
        boton.textContent = T.reproducir;
    }
    boton.addEventListener("click", () => {
        if (temporizador) { parar(); return; }
        if (quieto) { dibujar(total - 1); return; }
        let g = Number(rango.value) >= total - 1 ? 0 : Number(rango.value);
        dibujar(g);
        boton.textContent = T.pausar;
        temporizador = setInterval(() => {
            g += 1;
            dibujar(g);
            if (g >= total - 1) parar();
        }, 120);
    });
    rango.addEventListener("input", () => { parar(); dibujar(Number(rango.value)); });
    dibujar(total - 1);

    /* ---------- 2. Mapa por equipo ---------- */
    const figMapa = document.getElementById("repeticion-mapa-figura");
    const estadoMapa = document.getElementById("repeticion-mapa-estado");
    figMapa.hidden = false;
    const px = (lon) => 30 + ((lon + 125) / 59) * 580;
    const py = (lat) => 20 + ((49.5 - lat) / 25) * 330;
    const mapa = el("svg", { viewBox: "0 0 640 380", role: "img", "aria-label": T.mapa });
    document.getElementById("repeticion-mapa").appendChild(mapa);
    if (window.KOZA_MAPA) {
        el("path", { d: window.KOZA_MAPA.tierra, class: "r-tierra" }, mapa);
        el("path", { d: window.KOZA_MAPA.estados, class: "r-estados" }, mapa);
    }
    const kmMax = Math.max(...D.estadios.map((e) => Math.max(D.oficial.equipos[e.codigo].km, D.motor.equipos[e.codigo].km)));
    const kmMin = Math.min(...D.estadios.map((e) => Math.min(D.oficial.equipos[e.codigo].km, D.motor.equipos[e.codigo].km)));
    const radio = (km) => 4 + 16 * (km - kmMin) / (kmMax - kmMin);
    const circulos = D.estadios.map((e) => {
        const c = el("circle", { cx: px(e.lon), cy: py(e.lat), class: "r-equipo", tabindex: 0 }, mapa);
        const t = el("title", {}, c);
        return { e, c, t };
    });
    let actual = "oficial";
    function pintar(cal) {
        actual = cal;
        circulos.forEach(({ e, c, t }) => {
            const km = D[cal].equipos[e.codigo].km;
            c.setAttribute("r", radio(km).toFixed(1));
            t.textContent = poner(T.equipo_km, { equipo: e.equipo, km: fmt(km) });
        });
        const orden = D.estadios.slice().sort((a, b) => D[cal].equipos[b.codigo].km - D[cal].equipos[a.codigo].km);
        const mas = orden[0], menos = orden[orden.length - 1];
        estadoMapa.textContent = `${cal === "oficial" ? T.oficial : T.motor}. ` +
            `${poner(T.equipo_km, { equipo: mas.equipo, km: fmt(D[cal].equipos[mas.codigo].km) })} · ` +
            `${poner(T.equipo_km, { equipo: menos.equipo, km: fmt(D[cal].equipos[menos.codigo].km) })}`;
        figMapa.querySelectorAll("[data-calendario]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.calendario === cal)));
    }
    circulos.forEach(({ c, t }) => {
        c.addEventListener("focus", () => { estadoMapa.textContent = t.textContent; });
        c.addEventListener("mouseenter", () => { estadoMapa.textContent = t.textContent; });
        c.addEventListener("blur", () => pintar(actual));
    });
    figMapa.querySelectorAll("[data-calendario]").forEach((b) => b.addEventListener("click", () => pintar(b.dataset.calendario)));
    pintar("oficial");
})();
