/* Calendario dinámico: muestra los juegos de un calendario mes por mes.
   Lee los datos de <script type="application/json" id="calendario-datos">:
     {juegos: [["2026-11-07", "ATL", "MIA"], ...]  (fecha, en casa, visita),
      equipos: {"ATL": "Atlanta Braves", ...}, textos: {...}}
   - Botones de mes anterior y siguiente, y una lista para ir a cualquier mes.
   - Filtro por equipo: marca si juega en casa o de visita, con palabras y color.
   - En pantallas angostas se ve como agenda (lista por día) en lugar de cuadrícula.
   Sin JavaScript, la página muestra la tabla completa de juegos. */
(function () {
    "use strict";
    const nodo = document.getElementById("calendario-datos");
    const raiz = document.getElementById("calendario-dinamico");
    if (!nodo || !raiz) return;
    const D = JSON.parse(nodo.textContent);
    const T = D.textos;
    const idioma = document.documentElement.lang || "es";
    if (!D.juegos.length) return;

    // Juegos por día: {"2026-11-07": [[casa, visita], ...]}
    const porDia = {};
    for (const [f, h, v] of D.juegos) (porDia[f] = porDia[f] || []).push([h, v]);
    const dias = Object.keys(porDia).sort();
    const meses = [...new Set(dias.map((d) => d.slice(0, 7)))];
    const nombre = (c) => D.equipos[c] || c;
    const fechaDe = (iso) => new Date(iso + "T12:00:00");
    const fmtMes = new Intl.DateTimeFormat(idioma, { month: "long", year: "numeric" });
    const fmtDia = new Intl.DateTimeFormat(idioma, { weekday: "long", day: "numeric", month: "long" });
    const fmtSemana = new Intl.DateTimeFormat(idioma, { weekday: "short" });
    const poner = (t, v) => t.replace(/\{(\w+)\}/g, (_m, k) => v[k]);
    const crear = (tag, clase, texto) => {
        const e = document.createElement(tag);
        if (clase) e.className = clase;
        if (texto !== undefined) e.textContent = texto;
        return e;
    };

    let mes = 0;
    let equipo = "";

    /* ---------- Controles ---------- */
    raiz.hidden = false;
    const controles = crear("div", "cal-controles");
    const anterior = crear("button", "boton-secundario", "← " + T.anterior);
    const siguiente = crear("button", "boton-secundario", T.siguiente + " →");
    anterior.type = siguiente.type = "button";
    const etiquetaMes = crear("label", "cal-campo");
    etiquetaMes.append(T.mes + " ");
    const selectMes = crear("select");
    meses.forEach((m, i) => {
        const o = crear("option", "", fmtMes.format(fechaDe(m + "-01")));
        o.value = i;
        selectMes.appendChild(o);
    });
    etiquetaMes.appendChild(selectMes);
    const etiquetaEquipo = crear("label", "cal-campo");
    etiquetaEquipo.append(T.equipo + " ");
    const selectEquipo = crear("select");
    const todos = crear("option", "", T.todos);
    todos.value = "";
    selectEquipo.appendChild(todos);
    Object.keys(D.equipos).sort((a, b) => nombre(a).localeCompare(nombre(b), idioma)).forEach((c) => {
        const o = crear("option", "", nombre(c));
        o.value = c;
        selectEquipo.appendChild(o);
    });
    etiquetaEquipo.appendChild(selectEquipo);
    controles.append(anterior, etiquetaMes, siguiente, etiquetaEquipo);

    const titulo = crear("h3", "cal-titulo");
    titulo.id = "cal-titulo";
    const estado = crear("p", "nota cal-estado");
    estado.setAttribute("aria-live", "polite");
    const leyenda = crear("p", "nota cal-leyenda");
    const cuerpo = crear("div", "cal-cuerpo");
    raiz.append(controles, titulo, estado, leyenda, cuerpo);

    /* ---------- Un juego ---------- */
    function juego([h, v]) {
        const li = crear("li", "cal-juego");
        if (!equipo) {
            li.append(crear("span", "cal-casa", h), " – ", crear("span", "", v));
            li.title = poner(T.juego, { casa: nombre(h), visita: nombre(v) });
            li.appendChild(crear("span", "visualmente-oculto", " (" + li.title + ")"));
            return li;
        }
        const enCasa = h === equipo;
        li.classList.add(enCasa ? "cal-en-casa" : "cal-de-visita");
        li.append(crear("span", "cal-lugar", enCasa ? T.casa : T.visita), " ",
            crear("span", "", poner(enCasa ? T.contra : T.en, { rival: enCasa ? v : h })));
        li.title = poner(T.juego, { casa: nombre(h), visita: nombre(v) });
        return li;
    }
    function juegosDelDia(iso) {
        const lista = porDia[iso] || [];
        return equipo ? lista.filter(([h, v]) => h === equipo || v === equipo) : lista;
    }

    /* ---------- Dibujar el mes ---------- */
    function dibujar() {
        const m = meses[mes];
        const [anio, numMes] = m.split("-").map(Number);
        const primero = new Date(anio, numMes - 1, 1);
        const totalDias = new Date(anio, numMes, 0).getDate();
        const desplazar = (primero.getDay() + 6) % 7; // la semana empieza en lunes
        const textoMes = fmtMes.format(primero);
        titulo.textContent = textoMes.charAt(0).toLocaleUpperCase(idioma) + textoMes.slice(1);
        selectMes.value = mes;
        anterior.disabled = mes === 0;
        siguiente.disabled = mes === meses.length - 1;

        let juegosMes = 0, enCasa = 0;
        const iso = (d) => `${m}-${String(d).padStart(2, "0")}`;
        for (let d = 1; d <= totalDias; d++) {
            for (const [h] of juegosDelDia(iso(d))) {
                juegosMes++;
                if (equipo && h === equipo) enCasa++;
            }
        }
        estado.textContent = equipo
            ? poner(T.resumen_equipo, { equipo: nombre(equipo), n: juegosMes, casa: enCasa, visita: juegosMes - enCasa, mes: fmtMes.format(primero) })
            : poner(T.resumen, { n: juegosMes, mes: fmtMes.format(primero) });
        leyenda.textContent = equipo ? T.leyenda_equipo : T.leyenda;

        // Cuadrícula (pantallas anchas)
        const tabla = crear("table", "cal-mes");
        tabla.setAttribute("aria-labelledby", "cal-titulo");
        const filaCab = crear("tr");
        for (let i = 0; i < 7; i++) {
            const th = crear("th", "", fmtSemana.format(new Date(2024, 0, 1 + i))); // 1 ene 2024 fue lunes
            th.scope = "col";
            filaCab.appendChild(th);
        }
        const thead = crear("thead");
        thead.appendChild(filaCab);
        const tbody = crear("tbody");
        let fila = crear("tr");
        for (let i = 0; i < desplazar; i++) fila.appendChild(crear("td", "cal-vacio"));
        for (let d = 1; d <= totalDias; d++) {
            const td = crear("td");
            const lista = juegosDelDia(iso(d));
            td.appendChild(crear("span", "cal-numero", String(d)));
            if (lista.length) {
                td.classList.add("cal-con-juegos");
                const ul = crear("ul", "cal-lista");
                lista.forEach((j) => ul.appendChild(juego(j)));
                td.appendChild(ul);
            }
            fila.appendChild(td);
            if ((desplazar + d) % 7 === 0) { tbody.appendChild(fila); fila = crear("tr"); }
        }
        if (fila.children.length) {
            while (fila.children.length < 7) fila.appendChild(crear("td", "cal-vacio"));
            tbody.appendChild(fila);
        }
        tabla.append(thead, tbody);

        // Agenda (pantallas angostas): solo los días con juego
        const agenda = crear("ol", "cal-agenda");
        for (let d = 1; d <= totalDias; d++) {
            const lista = juegosDelDia(iso(d));
            if (!lista.length) continue;
            const li = crear("li");
            li.appendChild(crear("h4", "cal-dia", fmtDia.format(fechaDe(iso(d)))));
            const ul = crear("ul", "cal-lista");
            lista.forEach((j) => ul.appendChild(juego(j)));
            li.appendChild(ul);
            agenda.appendChild(li);
        }
        if (!agenda.children.length) agenda.appendChild(crear("li", "nota", T.sin_juegos));

        const envoltura = crear("div", "cal-desliza");
        envoltura.appendChild(tabla);
        cuerpo.replaceChildren(envoltura, agenda);
    }

    anterior.addEventListener("click", () => { mes = Math.max(0, mes - 1); dibujar(); });
    siguiente.addEventListener("click", () => { mes = Math.min(meses.length - 1, mes + 1); dibujar(); });
    selectMes.addEventListener("change", () => { mes = Number(selectMes.value); dibujar(); });
    selectEquipo.addEventListener("change", () => { equipo = selectEquipo.value; dibujar(); });
    dibujar();
})();
