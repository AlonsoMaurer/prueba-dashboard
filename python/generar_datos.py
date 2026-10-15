#!/usr/bin/env python3
"""Genera los datos SINTETICOS del dashboard (solo biblioteca estandar de Python).

Lee python/config.json (esquema, reglas de generacion y semilla) y escribe un CSV por tabla en datos/.
Con la misma semilla produce siempre los mismos datos. Ningun dato corresponde a una persona o empresa real.

Uso:  python python/generar_datos.py [--semilla N]
"""
import argparse
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent


def fecha(texto):
    return date.fromisoformat(texto)


class Generador:
    def __init__(self, config, semilla):
        self.rng = random.Random(semilla)
        self.parametros = config.get("parametros", {})
        self.tablas = {t["nombre"]: t for t in config["tablas"]}
        self.filas = {}      # nombre de tabla -> lista de dicts ya generados
        self._indices = {}   # (tabla, columna) -> {valor: fila}

    def indice(self, tabla, columna):
        clave = (tabla, columna)
        if clave not in self._indices:
            self._indices[clave] = {f[columna]: f for f in self.filas[tabla]}
        return self._indices[clave]

    def valor(self, tabla, columna, fila, posicion):
        g = columna["gen"]
        t = g["t"]
        rng = self.rng
        if t == "id":
            return posicion + 1
        if t == "categoria":
            return rng.choices(g["valores"], weights=g.get("pesos"))[0]
        if t == "entero":
            return rng.randint(g["min"], g["max"])
        if t == "real":
            return round(rng.uniform(g["min"], g["max"]), g.get("decimales", 2))
        if t == "real_lineal":
            v = g["base"] + g["paso"] * fila[g["desde"]] + rng.gauss(0, g["sd"])
            ajuste = g.get("ajuste")
            if ajuste:
                factor = ajuste["factores"].get(fila[ajuste["columna"]], 1.0)
                if isinstance(factor, dict):  # el factor depende de otra columna (por ejemplo, del nivel)
                    factor = factor.get(str(fila[ajuste["por"]]), 1.0)
                v *= factor
            return round(v, 0)
        if t == "fecha":
            inicio, fin = fecha(g["desde"]), fecha(g["hasta"])
            return (inicio + timedelta(days=rng.randint(0, (fin - inicio).days))).isoformat()
        if t == "fecha_despues":
            d = fecha(fila[g["de"]]) + timedelta(days=rng.randint(g["dias_min"], g["dias_max"]))
            if rng.random() < g["prob_nulo"] or d > fecha(g["tope"]):
                return None
            return d.isoformat()
        if t == "ref":
            return rng.choice([f[g["columna"]] for f in self.filas[g["tabla"]]])
        if t == "copia":
            via = next(c for c in self.tablas[tabla]["columnas"] if c["nombre"] == g["via"])
            origen = self.indice(g["tabla"], via["gen"]["columna"])[fila[g["via"]]]
            return origen[g["columna"]]
        if t == "relativo":
            v = fila[g["de"]] * rng.uniform(g["factor_min"], g["factor_max"])
            return max(g.get("min", 0), round(v)) if g.get("entero") else round(v, 2)
        if t == "bool":
            return 1 if rng.random() < g["prob"] else 0
        raise ValueError(f"Tipo de generacion desconocido: {t}")

    # ---- tablas derivadas de los empleados (spec 005, RF-9): reglas deterministas, sin azar ----

    def areas(self):
        return self.tablas["empleados"]["columnas"][1]["gen"]["valores"]

    def activos_en(self, fecha, area=None):
        """Empleados activos en una fecha ISO: ya ingresaron y no tienen baja, o su baja es posterior."""
        return [
            e for e in self.filas["empleados"]
            if e["fecha_ingreso"] <= fecha and (e["fecha_baja"] is None or e["fecha_baja"] > fecha)
            and (area is None or e["departamento"] == area)
        ]

    def fin_de_mes(self, anio, mes):
        primero_del_siguiente = date(anio + (mes == 12), mes % 12 + 1, 1)
        return (primero_del_siguiente - timedelta(days=1)).isoformat()

    def derivar(self, tabla):
        d = tabla["derivada"]
        regla = {"cupos": self.regla_cupos, "presupuesto": self.regla_presupuesto, "fuentes": self.regla_fuentes}.get(d["regla"])
        if regla is None:
            raise ValueError(f"Regla derivada desconocida: {d['regla']}")
        filas = regla(d)
        if len(filas) != tabla["filas"]:
            raise ValueError(f"{tabla['nombre']}: la regla produjo {len(filas)} filas y la tabla declara {tabla['filas']}")
        return filas

    def regla_cupos(self, d):
        corte = self.parametros["corte"]
        filas = []
        for area, factor in zip(self.areas(), d["factores"]):
            activos = len(self.activos_en(corte, area))
            pct = round(factor * 100)
            filas.append({"departamento": area, "cupos": (activos * pct + 99) // 100})  # activos × factor, hacia arriba, en enteros
        return filas

    def regla_presupuesto(self, d):
        corte, anio = self.parametros["corte"], int(self.parametros["inicio_anio"][:4])
        cupos = {f["departamento"]: f["cupos"] for f in self.filas[d["cupos"]]}
        presupuesto = {}
        for area in self.areas():
            salarios = [e["salario_base"] for e in self.activos_en(corte, area)]
            promedio = sum(salarios) / len(salarios) if salarios else 0
            presupuesto[area] = int(cupos[area] * promedio / 1000 + 0.5) * 1000
        filas = []
        for m in range(1, 13):
            for i, area in enumerate(self.areas()):
                gasto = None
                if m <= d["meses_con_gasto"]:
                    planilla = sum(e["salario_base"] for e in self.activos_en(self.fin_de_mes(anio, m), area))
                    desvio = (((m * 31 + i * 17 + m * i * 7) % 7) - 3) / 100 * (d["desvio_pct"] / 3) + m * d["deriva_mensual_pct"] / 100
                    gasto = int(planilla * (1 + desvio) / 1000 + 0.5) * 1000
                filas.append({"mes": f"{anio}-{m:02d}", "departamento": area, "presupuestado": presupuesto[area], "gasto_real": gasto})
        return filas

    def regla_fuentes(self, d):
        corte, anio = self.parametros["corte"], int(self.parametros["inicio_anio"][:4])
        activos = len(self.activos_en(corte))
        nomina = sum(len(self.activos_en(self.fin_de_mes(anio, m))) for m in range(1, d["meses_nomina"] + 1))
        filas = []
        for f in d["fuentes"]:
            base = f["registros"]["base"]
            if base == "empleados":
                registros = len(self.filas["empleados"])
            elif base == "nomina":
                registros = nomina
            else:
                registros = activos * f["registros"]["multiplo"]
            filas.append({
                "sistema": f["nombre"], "registros": registros,
                "incompletos": int(registros * f["tasa_incompletos"] + 0.5), "con_error": int(registros * f["tasa_error"] + 0.5),
                "ultima_carga": (fecha(corte) - timedelta(days=f["desfase_dias"])).isoformat(),
            })
        return filas

    def generar(self, tabla):
        if "derivada" in tabla:
            return self.derivar(tabla)
        nombres = [c["nombre"] for c in tabla["columnas"]]
        if "filas_fijas" in tabla:
            return [dict(zip(nombres, f)) for f in tabla["filas_fijas"]]
        filas = []
        for i in range(tabla["filas"]):
            fila = {}
            for col in tabla["columnas"]:
                fila[col["nombre"]] = self.valor(tabla["nombre"], col, fila, i)
            filas.append(fila)
        return filas

    def todo(self, config):
        for tabla in config["tablas"]:
            self.filas[tabla["nombre"]] = self.generar(tabla)
        return self.filas


def escribir_csv(destino, tabla, filas):
    nombres = [c["nombre"] for c in tabla["columnas"]]
    with open(destino, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(nombres)
        for fila in filas:
            w.writerow(["" if fila[n] is None else fila[n] for n in nombres])


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--semilla", type=int, help="semilla de los datos (por defecto, la de config.json)")
    args = ap.parse_args()
    config = json.loads((AQUI / "config.json").read_text(encoding="utf-8"))
    semilla = args.semilla if args.semilla is not None else config["semilla"]
    filas = Generador(config, semilla).todo(config)
    (RAIZ / "datos").mkdir(exist_ok=True)
    for tabla in config["tablas"]:
        escribir_csv(RAIZ / "datos" / f"{tabla['nombre']}.csv", tabla, filas[tabla["nombre"]])
    print(f"Datos sinteticos generados con la semilla {semilla}: " + ", ".join(f"{n} ({len(f)})" for n, f in filas.items()))


if __name__ == "__main__":
    main()
