#!/usr/bin/env python3
"""Analisis adicional en Python (solo biblioteca estandar): medias moviles sobre las series calculadas con SQL.

Lee datos/resultados.json y agrega la seccion "analisis". Solo existe en paquetes cuya oferta pide Python.

Uso:  python python/analisis.py   (despues de python/calcular.py)
"""
import json
import statistics
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent


def media_movil(filas, ventana):
    salida = []
    for i, fila in enumerate(filas):
        tramo = [f["valor"] for f in filas[max(0, i - ventana + 1): i + 1]]
        salida.append({"periodo": fila["periodo"], "valor": round(statistics.mean(tramo), 1)})
    return salida


def calcular_analisis(config, resultados):
    analisis = {}
    for a in config.get("analisis_python", []):
        base = resultados[a["base"]]["filas"]
        analisis[a["id"]] = {"forma": "serie", "filas": media_movil(base, a["ventana"])}
    return analisis


def main():
    config = json.loads((AQUI / "config.json").read_text(encoding="utf-8"))
    ruta = RAIZ / "datos" / "resultados.json"
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    datos["analisis"] = calcular_analisis(config, datos["resultados"])
    ruta.write_text(json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Analisis en Python: {len(datos['analisis'])} series -> datos/resultados.json")


if __name__ == "__main__":
    main()
