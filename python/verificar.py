#!/usr/bin/env python3
"""Verifica que las cifras de index.html coinciden con las que produce el codigo (solo biblioteca estandar).

Recalcula todo desde datos/*.csv con sql/consultas.sql (y el analisis en Python, si existe) y lo compara con el bloque
<script type="application/json" id="datos"> de index.html. Sale con codigo 0 si coinciden y 1 si no.

Uso:  python python/verificar.py
"""
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
sys.path.insert(0, str(AQUI))

import calcular  # noqa: E402


def extraer_bloque(html):
    m = re.search(r'<script type="application/json" id="datos">(.*?)</script>', html, re.S)
    if not m:
        raise ValueError('index.html no trae el bloque <script type="application/json" id="datos">')
    return json.loads(m.group(1))


def recalcular(config):
    resultados = calcular.calcular(config, RAIZ / "datos", RAIZ / "sql" / "consultas.sql")
    analisis = {}
    if config.get("analisis_python"):
        import analisis as modulo  # noqa: E402
        analisis = modulo.calcular_analisis(config, resultados)
    return resultados, analisis


def diferencias(esperado, publicado):
    return sorted(k for k in set(esperado) | set(publicado) if esperado.get(k) != publicado.get(k))


def main():
    try:
        config = calcular.leer_config()
        bloque = extraer_bloque((RAIZ / "index.html").read_text(encoding="utf-8"))
        resultados, analisis = recalcular(config)
        malos = [f"{k}" for k in diferencias(resultados, bloque.get("resultados", {}))]
        malos += [f"{k} (analisis)" for k in diferencias(analisis, bloque.get("analisis", {}))]
    except Exception as e:  # noqa: BLE001 - cualquier fallo de lectura o calculo es "no verificado"
        print(f"NO VERIFICADO: {e}")
        sys.exit(1)
    if malos:
        print("NO VERIFICADO: las cifras del HTML no coinciden con las recalculadas en: " + ", ".join(malos))
        sys.exit(1)
    print(f"VERIFICADO: las {len(resultados) + len(analisis)} cifras del HTML coinciden con las recalculadas desde los datos")


if __name__ == "__main__":
    main()
