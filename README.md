# TP Final — Pipeline ETL de exportaciones del NEA

**Unidad II · Fundamentos de la Programación**
Diplomatura en Data Analytics e IA Aplicada — UNNE / Extender

---

## Qué vas a construir

Un pipeline **ETL** que se conecta a una API pública, transforma los datos
y produce un dataset analítico listo para usar.

```
   API datos.gob.ar          data/raw/*.json         data/processed/
   (INDEC, 8 llamadas)  -->  (crudo, sin tocar) -->  exportaciones_nea.csv
                                                     resumen.json
        EXTRACT                  TRANSFORM              CHEQUEAR + LOAD
```

**Los datos:** exportaciones de Chaco, Corrientes, Formosa y Misiones por
país de destino y por rubro, 1993–2024, en millones de dólares.
Fuente: INDEC vía la [API de Series de Tiempo](https://apis.datos.gob.ar/series/api/)
de datos.gob.ar (datasets 357.1 y 350.1).

**El resultado esperado:** un CSV de **1.408 filas × 13 columnas**.

Ese CSV no se termina acá: lo vas a volver a usar en el módulo de
**estadística descriptiva**. Por eso importa que quede bien.

---

## Instalación

Necesitás **Python 3.8 o superior**. Nada más: el proyecto usa solo la
biblioteca estándar.

En la **terminal de VS Code**, parado en la carpeta del proyecto:

```bash
python --version          # verificá que sea 3.8+
python src/main.py        # corré el pipeline
```

La primera corrida descarga los datos de la API (necesitás internet) y los
deja en `data/raw/`. A partir de ahí podés trabajar sin conexión:

```bash
python src/main.py --sin-internet    # reutiliza lo que ya bajaste
```

Correr los tests:

```bash
python tests/test_transform.py
```

---

## Estructura del proyecto

```
├── config.py              Configuración: IDs de series, rutas, mapeos.
│                          El código dice CÓMO; esto dice CON QUÉ.
├── src/
│   ├── extract.py         [RESUELTO]  Descarga de la API -> data/raw/
│   ├── transform.py       [TU TRABAJO] TODOs 1 a 8
│   ├── load.py            [PARCIAL]    TODOs 9 a 12
│   └── main.py            [RESUELTO]  Orquesta E -> T -> L
├── tests/
│   └── test_transform.py  17 tests que definen qué se espera de vos
│                          (+ 2 en blanco para que escribas vos)
├── data/
│   ├── raw/               Datos crudos (no se versionan)
│   └── processed/         Salidas finales (no se versionan)
└── logs/                  Historial de corridas
```

---

## Lo que tenés que completar

Hay **13 TODOs**. Hacelos **en orden**: cada uno se apoya en el anterior.
Después de cada uno, corré los tests para ver si vas bien.

### `src/transform.py` — el corazón del TP

| TODO | Función | Qué aplica de la cursada |
|:---:|---|---|
| 1 | `ancho_a_largo()` | Bucles anidados sobre listas y diccionarios |
| 2 | `clasificar_region()` | Diccionario de mapeo + `.get()` con default |
| 3 | `calcular_decada()` | División entera `//` y f-strings |
| 4 | `calcular_participacion()` | Función con `return` + evitar división por cero |
| 5 | `calcular_variacion()` | Función con `return` + manejo de `None` |
| 6 | `agregar_variacion_interanual()` | Diccionario como índice de búsqueda |
| 7 | `agregar_ranking()` | `sorted()`, `enumerate()`, booleanos |
| 8 | `construir_indice_rubros()` y `unir_con_rubros()` | JOIN por clave compuesta |

### `src/load.py` — validar y guardar

| TODO | Función | Qué aplica |
|:---:|---|---|
| 9 | `chequear_unicidad()` | Sets para detectar duplicados |
| 10 | `chequear_rangos()` | Comprensión de listas con filtro |
| 11 | `construir_resumen()` | Diccionarios anidados, `min`/`max`/`sum` |
| 12 | `guardar_resumen()` y `escribir_log_corrida()` | `json.dump`, modos `"w"` vs `"a"` |

### `tests/test_transform.py`

| TODO | Qué hacer |
|:---:|---|
| 13 | **(Bonus)** Escribí dos tests propios |

---

## El dataset que tenés que producir

`data/processed/exportaciones_nea.csv` — **13 columnas, en este orden exacto**:

| # | Columna | Tipo | Descripción |
|:---:|---|---|---|
| 1 | `anio` | int | Año de la observación (1993–2024) |
| 2 | `provincia` | str | Chaco, Corrientes, Formosa o Misiones |
| 3 | `destino` | str | País de destino (o "Resto") |
| 4 | `region_destino` | str | Región geoeconómica del destino |
| 5 | `valor_musd` | float | Exportado a ese destino, en millones de USD |
| 6 | `total_provincia_musd` | float | Total exportado por la provincia ese año |
| 7 | `participacion_pct` | float | `valor / total * 100` |
| 8 | `var_interanual_pct` | float | Variación vs. el año anterior (nulo el 1er año) |
| 9 | `decada` | str | 1990s, 2000s, 2010s o 2020s |
| 10 | `ranking_destino` | int | Posición del destino ese año (1 = el mayor) |
| 11 | `es_top3` | bool | Si está entre los 3 principales |
| 12 | `rubro_principal` | str | Rubro más exportado ese año (del join) |
| 13 | `pp_participacion_pct` | float | % de productos primarios ese año (del join) |

Dos filas de ejemplo (valores reales de la API):

```csv
anio,provincia,destino,region_destino,valor_musd,total_provincia_musd,participacion_pct,var_interanual_pct,decada,ranking_destino,es_top3,rubro_principal,pp_participacion_pct
2024,Chaco,China,Asia,110.93,401.74,27.61,46.36,2020s,1,True,Productos primarios,81.3
2024,Chaco,Brasil,Mercosur,18.12,401.74,4.51,30.45,2020s,6,False,Productos primarios,81.3
```

---

## Cómo saber si terminaste

1. `python tests/test_transform.py` → los 17 tests en verde
   (los 2 del TODO 13 quedan en *skipped* hasta que los escribas).
2. `python src/main.py` → corre sin errores de punta a punta.
3. `data/processed/exportaciones_nea.csv` existe y tiene **1.408 filas**
   (más la de encabezado) y **13 columnas**.
4. `data/processed/resumen.json` y `logs/pipeline.log` existen.
5. Corré el pipeline **dos veces**: el CSV tiene que quedar igual
   (idempotencia) y el log tiene que tener **dos** líneas.

Para contar las filas rápido:

```bash
wc -l data/processed/exportaciones_nea.csv     # debería dar 1409
```

---

## Consejos

- **Leé los contratos.** Cada función tiene un docstring que dice qué
  recibe y qué devuelve. El resto del pipeline cuenta con eso.
- **Un TODO por vez.** Implementá, corré los tests, y recién ahí seguí.
- **Los errores son información.** Leé el traceback de abajo hacia arriba:
  la última línea dice qué pasó, las de arriba dónde.
- **No toques `COLUMNAS`** en `transform.py`: es el contrato de salida.
- **Commiteá seguido.** Un commit por TODO resuelto es un buen ritmo, y
  se evalúa. `version_final_v3_DEFINITIVA.py` no es control de versiones.
- **Si algo del enunciado no se entiende, preguntá** en el foro de la
  materia antes de asumir.

---

## Entrega

1. Creá tu **propio repositorio** en GitHub con este proyecto.
2. Completá los TODOs, commiteando a medida que avanzás.
3. Actualizá este README: sacá las secciones de TODOs y contá **vos** qué
   hace tu pipeline, cómo se corre y qué encontraste en los datos.
4. Entregá el **link a tu repositorio**.

La guía paso a paso está en `docs/guia-git.md`, dentro de la carpeta
`tp-final/` del repositorio de la materia.

---

*Fuente de datos: INDEC, vía el portal de datos abiertos del Estado
argentino (datos.gob.ar). IDs de series verificados el 2026-08-02.*
