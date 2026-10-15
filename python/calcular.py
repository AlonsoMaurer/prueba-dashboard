#!/usr/bin/env python3
"""Calcula las cifras del dashboard con SQL (SQLite en memoria; solo biblioteca estandar).

Carga los CSV de datos/ en SQLite, ejecuta cada consulta de sql/consultas.sql y escribe datos/resultados.json.

Uso:  python python/calcular.py
"""
import csv
import json
import re
import sqlite3
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent


def leer_config():
    return json.loads((AQUI / "config.json").read_text(encoding="utf-8"))


def convertir(valor, tipo):
    if valor == "":
        return None
    if tipo == "INTEGER":
        return int(valor)
    if tipo == "REAL":
        return float(valor)
    return valor


def cargar_base(config, carpeta_datos):
    con = sqlite3.connect(":memory:")
    for tabla in config["tablas"]:
        columnas = tabla["columnas"]
        con.execute(f"CREATE TABLE {tabla['nombre']} ({', '.join(c['nombre'] + ' ' + c['tipo'] for c in columnas)})")
        with open(carpeta_datos / f"{tabla['nombre']}.csv", newline="", encoding="utf-8") as f:
            lector = csv.reader(f)
            encabezado = next(lector)
            esperado = [c["nombre"] for c in columnas]
            if encabezado != esperado:
                raise ValueError(f"{tabla['nombre']}.csv: encabezado {encabezado} distinto de {esperado}")
            filas = [[convertir(v, c["tipo"]) for v, c in zip(fila, columnas)] for fila in lector]
        con.executemany(f"INSERT INTO {tabla['nombre']} VALUES ({','.join('?' * len(columnas))})", filas)
    return con


def leer_consultas(ruta):
    """sql/consultas.sql: cada consulta va precedida de una linea '-- kpi: <id>' y termina en ';'."""
    consultas = {}
    for bloque in re.split(r"^-- kpi: ", ruta.read_text(encoding="utf-8"), flags=re.M)[1:]:
        id_kpi, _, sql = bloque.partition("\n")
        consultas[id_kpi.strip()] = sql.strip().rstrip(";")
    return consultas


def calcular(config, carpeta_datos, ruta_sql):
    con = cargar_base(config, carpeta_datos)
    consultas = leer_consultas(ruta_sql)
    resultados = {}
    for kpi in config["kpis"]:
        cur = con.execute(consultas[kpi["id"]], config["parametros"])
        filas = cur.fetchall()
        if kpi["forma"] == "escalar":
            resultados[kpi["id"]] = {"forma": "escalar", "valor": filas[0][0]}
        else:
            clave = "periodo" if kpi["forma"] == "serie" else "categoria"
            resultados[kpi["id"]] = {"forma": kpi["forma"], "filas": [{clave: etiqueta, "valor": valor} for etiqueta, valor in filas]}
    return resultados


def main():
    config = leer_config()
    resultados = calcular(config, RAIZ / "datos", RAIZ / "sql" / "consultas.sql")
    salida = {"resultados": resultados, "analisis": {}}
    (RAIZ / "datos" / "resultados.json").write_text(json.dumps(salida, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Cifras calculadas con SQL: {len(resultados)} KPIs -> datos/resultados.json")


if __name__ == "__main__":
    main()
