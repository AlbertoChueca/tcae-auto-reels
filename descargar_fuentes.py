"""Descarga del BOE (API de datos abiertos, legislación consolidada) el texto vigente de las normas de fuentes/fuentes.json.

    python descargar_fuentes.py            # descarga las que falten
    python descargar_fuentes.py --todas    # vuelve a descargarlas todas (p. ej. tras una reforma)

Cada texto se guarda en fuentes/<archivo> con una cabecera "# Título · id · fecha". Antes de guardar se comprueba que el
título descargado contiene las palabras 'clave' (así un id equivocado nunca se cuela como fuente). Las normas 'manual'
(solo en el BOA) hay que pegarlas a mano. Escribe fuentes/estado.md con el resultado.
"""
import datetime, json, os, re, sys, xml.etree.ElementTree as ET
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(HERE, "fuentes")
API = "https://www.boe.es/datosabiertos/api/legislacion-consolidada"
HDR = {"Accept": "application/xml", "User-Agent": "apruebatcae-reels/1.0"}


def _get(url, **kw):
    r = requests.get(url, headers=HDR, timeout=120, **kw)
    r.raise_for_status()
    return r


def titulo(boe_id):
    root = ET.fromstring(_get(f"{API}/id/{boe_id}/metadatos").content)
    t = root.find(".//titulo")
    return (t.text or "").strip() if t is not None else ""


def buscar(q):
    """Busca por título en la API del BOE y devuelve [(id, título)]. Si la búsqueda no está disponible devuelve []."""
    try:
        query = json.dumps({"query": {"query_string": {"query": f'titulo:({q})'}}})
        root = ET.fromstring(_get(API, params={"query": query, "limit": 10}).content)
        out = []
        for it in root.iter("item"):
            i, t = it.find("identificador"), it.find("titulo")
            if i is not None and t is not None:
                out.append((i.text.strip(), (t.text or "").strip()))
        return out
    except Exception as e:
        print("  búsqueda no disponible:", str(e)[:120]); return []


def texto(boe_id):
    """Texto vigente: para cada bloque, la última versión; párrafos separados por saltos de línea."""
    root = ET.fromstring(_get(f"{API}/id/{boe_id}/texto").content)
    parts = []
    bloques = list(root.iter("bloque")) or [root]
    for b in bloques:
        vers = b.findall("version") or [b]
        v = vers[-1]
        for el in v.iter():
            if el.tag in ("p", "titulo") and "".join(el.itertext()).strip():
                parts.append(re.sub(r"\s+", " ", "".join(el.itertext())).strip())
    return "\n".join(parts)


def main(todas=False):
    cfg = json.load(open(os.path.join(DIR, "fuentes.json")))
    rows = [f"# Estado de las fuentes ({datetime.date.today()})\n", "| norma | estado |", "|---|---|"]
    for k, n in cfg["normas"].items():
        path = os.path.join(DIR, n["archivo"])
        if os.path.exists(path) and not todas:
            rows.append(f"| {n['titulo']} | ✅ ya estaba |"); continue
        if n.get("manual"):
            rows.append(f"| {n['titulo']} | {'✅ pegada a mano' if os.path.exists(path) else '✋ solo BOA: pega su texto en fuentes/' + n['archivo']} |")
            continue
        print("•", n["titulo"], flush=True)
        try:
            cands = [(n["boe"], None)] if n.get("boe") else buscar(n["buscar"])
            ok = None
            for bid, t in cands:
                t = t or titulo(bid)
                if all(c.lower() in t.lower() for c in n.get("clave", [])):
                    ok = (bid, t); break
                print(f"  {bid}: el título no coincide ({t[:90]})")
            if not ok:
                rows.append(f"| {n['titulo']} | ❌ no encontrada en el BOE: revisa el id en fuentes.json o pégala a mano |"); continue
            txt = texto(ok[0])
            if len(txt) < 2000:
                raise RuntimeError("texto demasiado corto")
            open(path, "w").write(f"# {ok[1]} · {ok[0]} · descargado {datetime.date.today()}\n\n{txt}\n")
            rows.append(f"| {n['titulo']} | ✅ {ok[0]} ({len(txt) // 1000} mil caracteres) |")
        except Exception as e:
            rows.append(f"| {n['titulo']} | ❌ error: {str(e)[:120]} |")
    open(os.path.join(DIR, "estado.md"), "w").write("\n".join(rows) + "\n")
    print("\n".join(rows))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        open(os.environ["GITHUB_STEP_SUMMARY"], "a").write("\n".join(rows) + "\n")


if __name__ == "__main__":
    main("--todas" in sys.argv)
