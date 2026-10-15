# Panel de ejemplo — Jefe Compensaciones & Control Gestión RRHH

> **Datos sintéticos.** Este panel se construyó con datos ficticios generados por código; no corresponde a ninguna empresa ni persona real. Sirve para mostrar cómo se resuelve este tipo de problema, no resultados reales.

## Qué es

Un panel web de People Analytics / RR.HH., hecho a la medida de los requisitos de una oferta de trabajo. Se abre con un doble clic en `index.html` (no necesita instalar nada ni conexión a internet).

## Contexto

Datos sintéticos de People Analytics / RR.HH., sector Q · Actividades de atención de la salud humana y de asistencia social, empresa Grande (250 o más trabajadores).

La categoría de tamaño se define por la dotación de trabajadores dependientes (tramos del SII), no por las ventas anuales con que la Ley 20.416 define la micro, pequeña y mediana empresa. Los datos de este panel son sintéticos y no corresponden a una empresa real de ese sector y tamaño.

## Cómo verlo en línea (GitHub Pages)

1. Sube el contenido de esta carpeta a un repositorio nuevo de tu cuenta de GitHub.
2. En el repositorio: Settings → Pages → Build and deployment → Deploy from a branch → rama `main`, carpeta `/ (root)`.
3. Espera un minuto y abre la dirección que GitHub Pages muestra en esa pantalla: ese es el link que compartes.

## Cómo volver a generar y verificar las cifras

Requiere Python 3.9 o superior; no usa librerías externas. Desde esta carpeta:

```
python python/generar_datos.py
python python/calcular.py
python python/analisis.py
python python/verificar.py
```

## Tecnologías

- Demostradas en este panel: SQL (SQLite), Python, SQL.
- Tecnologías de la oferta no demostradas aquí: Power BI, Excel.

## Cifras

Verificadas con SQL (SQLite) y Python 3.12.10 el 2026-10-15: las cifras de `index.html` coinciden con las que recalcula el código.

Semilla de los datos: 1261389412.

## Contenido

- `index.html` — el panel (un solo archivo)
- `datos/*.csv` — datos sintéticos de ejemplo
- `datos/resultados.json` — cifras calculadas con SQL
- `sql/consultas.sql` — la consulta de cada cifra
- `python/generar_datos.py` — genera los datos con una semilla fija
- `python/calcular.py` — calcula las cifras con SQL (SQLite)
- `python/analisis.py` — análisis adicional en Python (solo si la oferta lo pide)
- `python/verificar.py` — comprueba que el panel muestra las cifras del código

## Criterios de los datos sintéticos

Son supuestos del autor, pendientes de validación; no son estadísticas reales ni estándares oficiales.

- Cupos autorizados: los empleados activos de cada área al corte, por un factor fijo por área (1,06 a 1,18), redondeado hacia arriba; ningún área queda con más gente que cupos.
- Presupuesto mensual: los cupos de cada área por el salario base promedio de sus empleados activos; es igual en los 12 meses.
- Gasto real de enero a septiembre: la suma del salario base de los empleados activos de cada mes, con una desviación determinística de −3 % a +3 % y una deriva leve al alza; octubre a diciembre solo tienen presupuesto.
- Brecha de género: el salario de las mujeres es entre 1 % y 7 % menor que el de los hombres según el nivel (antes del ruido aleatorio de cada salario).

## Definición de cada cifra

- **Dotación activa:** Empleados sin fecha de baja al corte.
- **Rotación anual:** Bajas del año divididas por la dotación promedio (inicio y fin de año).
- **Bajas por mes:** Cantidad de bajas en cada mes del año de corte.
- **Dotación por área:** Empleados activos por departamento.
- **Antigüedad promedio:** Años promedio desde el ingreso hasta el corte, empleados activos.
- **Salario promedio por nivel:** Salario base promedio de los empleados activos de cada nivel.
- **Compa-ratio promedio:** Salario base dividido por el punto medio de la banda de su nivel; 1,00 es el punto medio.
- **Empleados fuera de banda:** Porcentaje de activos con salario bajo el mínimo o sobre el máximo de su banda.
- **Brecha salarial de género:** Promedio simple de las brechas por nivel.
- **Brecha salarial de género por nivel:** (Salario promedio hombres − mujeres) / hombres, dentro de cada nivel. Es una brecha descriptiva, no un análisis de equidad ajustado.
- **Gasto real vs. presupuesto:** Gasto salarial real dividido por el presupuestado, en los meses con gasto cerrado.
- **Presupuesto anual:** Suma del presupuesto de los 12 meses de todas las áreas.
- **Desviación del gasto por área:** (Gasto real − presupuestado) / presupuestado, por área, en los meses con gasto cerrado; positivo es sobregasto.
- **Gasto salarial por mes:** Gasto salarial real de cada mes cerrado, sumando todas las áreas.
- **Proyección de cierre del año:** Gasto real acumulado más el promedio de los últimos 3 meses cerrados por cada mes que falta. Es una proyección simple, no un modelo estadístico.
- **Ocupación de la dotación autorizada:** Empleados activos divididos por los cupos autorizados.
- **Ocupación por área:** Empleados activos divididos por los cupos autorizados de cada área.
- **Vacantes por área:** Cupos autorizados menos empleados activos de cada área (mínimo cero).
- **Bajas: media móvil de 3 meses:** Promedio de bajas de los últimos 3 meses, calculado con Python estándar.
