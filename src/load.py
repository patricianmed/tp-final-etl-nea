"""
LOAD — Quality checks y persistencia   *** PARCIALMENTE RESUELTO ***
=====================================================================

Dos responsabilidades, en este orden:

  1. CHEQUEAR: validar el dataset antes de publicarlo. Si algo crítico
     falla, cortamos: mejor no entregar nada que entregar un reporte roto.
  2. GUARDAR: escribir el CSV (para personas), el resumen JSON (para
     programas) y el log (para auditar).

Te dejamos resuelto el guardado del CSV y dos de los quality checks.
Faltan 4 TODOs (9 a 12), todos cortos.

Idempotencia: el CSV y el JSON van en modo "w", así que correr el pipeline
dos veces deja el mismo resultado. El log va en modo "a" porque un log ES
un historial: ahí sí queremos que crezca.
"""

import csv
import json
import logging
import os
from datetime import datetime

import config
from transform import COLUMNAS


# ======================================================================
# QUALITY CHECKS
# ======================================================================
def chequear_cantidad(filas, minimo=None):
    """¿Tenemos todas las filas que esperábamos?  [RESUELTO — de ejemplo]

    Fijate el patrón: devuelve una tupla (bool, mensaje). Todos los
    checks tienen que devolver lo mismo para que validar() los trate igual.
    """
    if minimo is None:
        minimo = config.MINIMO_FILAS_ESPERADAS
    ok = len(filas) >= minimo
    return ok, f"cantidad: {len(filas)} filas (mínimo esperado {minimo})"


def chequear_columnas(filas):
    """¿Todas las filas tienen exactamente las columnas del contrato?
    [RESUELTO — de ejemplo]
    """
    esperadas = set(COLUMNAS)
    for fila in filas:
        if set(fila.keys()) != esperadas:
            faltan = esperadas - set(fila.keys())
            return False, f"columnas: una fila no cumple el esquema (faltan {faltan})"
    return True, f"columnas: las {len(COLUMNAS)} del contrato en todas las filas"


def chequear_unicidad(filas):
    """¿Hay duplicados? La clave del dataset es (provincia, anio, destino).

    Debe devolver (bool, mensaje), igual que los checks de arriba.
    """
    # TODO 9 --------------------------------------------------------------
    # Pista: es el patrón del set que viste en la Clase 3. Armá la lista de
    # claves (una tupla por fila) y compará len(lista) con len(set(lista)).
        # Armamos la lista de claves como tuplas (provincia, anio, destino)
    claves = [(fila["provincia"], fila["anio"], fila["destino"]) for fila in filas]
    
    # Si coinciden los tamaños, no hay duplicados
    es_unico = len(claves) == len(set(claves))
    
    if es_unico:
        return True, "Chequeo de unicidad exitoso: No se encontraron registros duplicados."
    else:
        return False, "Error de unicidad: Se detectaron registros duplicados en el dataset."

    # ---------------------------------------------------------------------


def chequear_rangos(filas):
    """¿Los valores son plausibles?

    Un valor negativo o mayor a config.VALOR_MAXIMO_RAZONABLE es
    sospechoso: no existen exportaciones negativas.
    """
    # TODO 10 -------------------------------------------------------------
    # Pista: una comprensión de lista con la condición al final te da
    # directamente las filas fuera de rango; después mirás cuántas son.
    import config
    
    # Filtramos las filas fuera de rango usando comprensión de lista
    fuera_de_rango = [
        f for f in filas 
        if f["valor_musd"] < 0 or f["valor_musd"] > config.VALOR_MAXIMO_RAZONABLE
    ]
    
    # Si no hay ninguna fila fuera de rango, el chequeo pasa
    if len(fuera_de_rango) == 0:
        return True, "Chequeo de rangos exitoso: Todos los valores son plausibles."
    else:
        cant = len(fuera_de_rango)
        return False, f"Error de rangos: Se encontraron {cant} registros con valores fuera de rango."

    # ---------------------------------------------------------------------


def chequear_cobertura(filas):
    """Advertencia (no crítica): ¿cuántos nulos quedaron en las derivadas?
    [RESUELTO]
    """
    sin_variacion = sum(1 for f in filas if f["var_interanual_pct"] is None)
    sin_rubro = sum(1 for f in filas if f["rubro_principal"] is None)
    ok = sin_rubro == 0
    return ok, (f"cobertura: {sin_variacion} filas sin variación interanual "
                f"(esperable en el primer año), {sin_rubro} sin rubro")


def validar(filas):
    """Corre todos los checks.  [RESUELTO]

    Los CRÍTICOS cortan el pipeline lanzando una excepción ("fallar
    temprano y ruidosamente"). La cobertura solo deja una advertencia.

    Retorna una lista de dicts con el detalle, para el resumen JSON.
    """
    criticos = [
        chequear_cantidad(filas),
        chequear_columnas(filas),
        chequear_unicidad(filas),
        chequear_rangos(filas),
    ]

    detalle = []
    for ok, mensaje in criticos:
        detalle.append({"check": mensaje, "estado": "OK" if ok else "FALLO"})
        if ok:
            logging.info("  check OK    | %s", mensaje)
        else:
            logging.error("  check FALLO | %s", mensaje)
            raise ValueError(f"Quality check crítico falló -> {mensaje}")

    ok, mensaje = chequear_cobertura(filas)
    detalle.append({"check": mensaje, "estado": "OK" if ok else "AVISO"})
    if ok:
        logging.info("  check OK    | %s", mensaje)
    else:
        logging.warning("  check AVISO | %s", mensaje)

    return detalle


# ======================================================================
# PERSISTENCIA
# ======================================================================
def guardar_csv(filas, carpeta=None, nombre=None):
    """Escribe el dataset final. Modo 'w': cada corrida lo reemplaza.
    [RESUELTO — usalo de modelo para el resto]
    """
    carpeta = carpeta or config.DIR_PROCESSED
    nombre = nombre or config.ARCHIVO_SALIDA_CSV
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, nombre)

    with open(ruta, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUMNAS)
        escritor.writeheader()
        escritor.writerows(filas)

    logging.info("  CSV: %s (%s filas)", ruta, len(filas))
    return ruta


def construir_resumen(filas, detalle_checks):
    """Arma el resumen del proceso: metadatos + estadísticas descriptivas.

    Este JSON es la "ficha técnica" del dataset: quien lo reciba tiene que
    poder saber de dónde salió, cuándo y qué contiene, SIN abrir el CSV.

    CONTRATO: devolvé un dict que incluya al menos estas claves:

        dataset            (str)  nombre descriptivo
        fuente             (str)  de dónde salieron los datos
        unidad             (str)  "millones de dólares FOB"
        generado           (str)  fecha y hora de esta corrida
        filas              (int)
        columnas           (int)
        periodo            (dict) {"desde": anio_min, "hasta": anio_max}
        provincias         (list) ordenada
        valor_musd         (dict) {"minimo":…, "maximo":…, "promedio":…}
        quality_checks     (list) el detalle_checks que recibís
    """
    # TODO 11 -------------------------------------------------------------
    # Pistas:
    #   - Para la lista de valores: [f["valor_musd"] for f in filas]
    #   - min(), max() y sum()/len() ya los conocés.
    #   - Para provincias únicas y ordenadas: sorted({f["provincia"] for f in filas})
    #   - Para la fecha: datetime.now().strftime("%Y-%m-%d %H:%M")
    #   - Podés agregar más claves si querés (suma puntos en la rúbrica).
    from datetime import datetime
    
    # Extraemos las listas de valores y años usando comprensión de listas
    valores = [f["valor_musd"] for f in filas]
    anios = [f["anio"] for f in filas]
    
    # Calculamos los extremos del periodo de años
    anio_min = min(anios) if anios else None
    anio_max = max(anios) if anios else None
    
    # Calculamos las métricas descriptivas redondeadas a 2 decimales
    val_min = round(min(valores), 2) if valores else 0.0
    val_max = round(max(valores), 2) if valores else 0.0
    val_prom = round(sum(valores) / len(valores), 2) if valores else 0.0
    
    # Obtenemos la lista ordenada de provincias únicas
    provincias_lista = sorted({f["provincia"] for f in filas})
    
    # Tomamos la fecha y hora actual formateada
    fecha_gen = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Cantidad de columnas (usamos la variable COLUMNAS que ya está definida en tu archivo)
    cant_columnas = len(COLUMNAS) if 'COLUMNAS' in globals() else (len(filas[0]) if filas else 0)
    
    # Construimos el diccionario final respetando exactamente las claves del contrato
    resumen = {
        "dataset": "Dataset de Exportaciones Provinciales Argentinas",
        "fuente": "INDEC / Agencia Argentina de Inversiones y Comercio Internacional",
        "unidad": "millones de dólares FOB",
        "generado": fecha_gen,
        "filas": len(filas),
        "columnas": cant_columnas,
        "periodo": {
            "desde": anio_min,
            "hasta": anio_max
        },
        "provincias": provincias_lista,
        "valor_musd": {
            "minimo": val_min,
            "maximo": val_max,
            "promedio": val_prom
        },
        "quality_checks": detalle_checks
    }
    
    return resumen

    # ---------------------------------------------------------------------


def guardar_resumen(resumen, carpeta=None, nombre=None):
    """Escribe el resumen en JSON, legible por humanos y por programas.

    Acordate de los dos argumentos que vimos: ensure_ascii=False para que
    las tildes se guarden bien, e indent=2 para que sea legible.
    """
    # TODO 12a ------------------------------------------------------------
    # Muy parecido a guardar_csv(), pero con json.dump().
    import json
    
    carpeta = carpeta or config.DIR_PROCESSED
    nombre = nombre or config.ARCHIVO_SALIDA_JSON
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, nombre)
    
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(resumen, f, ensure_ascii=False, indent=2)
        
    logging.info(" JSON resumen: %s", ruta)
    return ruta

    # ---------------------------------------------------------------------


def escribir_log_corrida(resumen, carpeta=None, nombre=None):
    """Agrega UNA línea al historial del pipeline.

    Modo "a" (append): nunca borra lo anterior. Cada corrida deja su rastro.
    Sugerencia de formato:

        2026-08-02 14:30 | OK | 1408 filas | 1993-2024
    """
    # TODO 12b ------------------------------------------------------------
    carpeta = carpeta or "logs"
    nombre = nombre or getattr(config, "ARCHIVO_LOG_CORRIDA", "pipeline.log")
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, nombre)
    
    # Extraemos los datos del resumen para armar la línea de log
    fecha = resumen["generado"]
    filas_cant = resumen["filas"]
    desde = resumen["periodo"]["desde"]
    hasta = resumen["periodo"]["hasta"]
    
    # Armamos la línea de texto con el formato sugerido
    linea_log = f"{fecha} | OK | {filas_cant} filas | {desde}-{hasta}\n"
    
    # Abrimos en modo "a" (append) para no borrar lo anterior
    with open(ruta, "a", encoding="utf-8") as f:
        f.write(linea_log)
        
    logging.info(" Log guardado: %s", ruta)
    return ruta

    # ---------------------------------------------------------------------


def cargar(filas):
    """CONTRATO: recibe las filas finales; valida y persiste las 3 salidas.
    [RESUELTO]
    """
    logging.info("LOAD: validando")
    detalle = validar(filas)

    logging.info("LOAD: guardando")
    guardar_csv(filas)
    resumen = construir_resumen(filas, detalle)
    guardar_resumen(resumen)
    escribir_log_corrida(resumen)

    logging.info("LOAD OK")
    return resumen
