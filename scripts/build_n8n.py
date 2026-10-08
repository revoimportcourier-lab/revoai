#!/usr/bin/env python3
"""Arma n8n/revo-meta-ads-workflow.json a partir del código de n8n/code/.

Tres flujos en un solo workflow:
  A · Actualizar biblioteca  (revoimport.com → Claude → Google Sheets, estado "pendiente")
  B · Generar aprobados      (Google Sheets "aprobado" → Higgsfield master 3:4)
  C · Revisar pendientes     (estado en Higgsfield → QA con GPT-6 Astra → formatos 1:1 y 9:16 → hoja)

Uso:  python3 scripts/build_n8n.py
"""
import json
import re
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CODE = ROOT / "n8n" / "code"
ROWS = json.loads((ROOT / "prompts" / "banners.json").read_text(encoding="utf-8"))

TEMPLATE_NAMES = {
    "T1": "Diagrama de partes (callouts numerados)",
    "T2": "Flat lay con 3 llamadas",
    "T3": "Ficha técnica",
    "T4": "Oferta + plantilla de reseña",
    "T5": "Knolling: problema → solución",
}

CLAUDE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["filas", "meta", "notas"],
    "properties": {
        "filas": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["plantilla", "refs", "textos_imagen", "prompt_master_3x4", "prompt_1x1", "prompt_9x16"],
                "properties": {
                    "plantilla": {"type": "string", "enum": ["T1", "T2", "T3", "T4", "T5"]},
                    "refs": {"type": "array", "items": {"type": "string"}},
                    "textos_imagen": {"type": "array", "items": {"type": "string"}},
                    "prompt_master_3x4": {"type": "string"},
                    "prompt_1x1": {"type": "string"},
                    "prompt_9x16": {"type": "string"},
                },
            },
        },
        "meta": {
            "type": "object",
            "additionalProperties": False,
            "required": ["textos", "titulos", "descripcion"],
            "properties": {
                "textos": {"type": "array", "items": {"type": "string"}},
                "titulos": {"type": "array", "items": {"type": "string"}},
                "descripcion": {"type": "string"},
            },
        },
        "notas": {"type": "string"},
    },
}

QA_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["aprobado", "texto_correcto", "sin_logos", "producto_fiel", "layout_ok", "problemas"],
    "properties": {
        "aprobado": {"type": "boolean"},
        "texto_correcto": {"type": "boolean"},
        "sin_logos": {"type": "boolean"},
        "producto_fiel": {"type": "boolean"},
        "layout_ok": {"type": "boolean"},
        "problemas": {"type": "array", "items": {"type": "string"}},
    },
}


def canonical_example():
    rows = [r for r in ROWS if r["producto_id"] == "iphone-17-pro-max"]
    parts = []
    for r in rows:
        parts.append(
            f"### {r['plantilla']} · {r['plantilla_nombre']}\n"
            f"refs: {json.dumps([u.strip() for u in r['refs'].split('|')])}\n"
            f"textos_imagen: {r['textos_imagen']}\n"
            f"prompt_master_3x4:\n{r['prompt_master_3x4']}\n"
        )
    t1 = rows[0]
    parts.append(f"### Redimensión de T1\nprompt_1x1:\n{t1['prompt_1x1']}\n\nprompt_9x16:\n{t1['prompt_9x16']}\n")
    parts.append(
        "### meta\n"
        + json.dumps({"textos": [t1["meta_texto_1"], t1["meta_texto_2"], t1["meta_texto_3"]],
                      "titulos": [t1["meta_titulo_1"], t1["meta_titulo_2"], t1["meta_titulo_3"]],
                      "descripcion": t1["meta_descripcion"]}, ensure_ascii=False)
    )
    return "\n".join(parts)


def code(name, **subs):
    src = (CODE / name).read_text(encoding="utf-8")
    for key, value in subs.items():
        token = f"__{key}__"
        assert token in src, (name, token)
        src = src.replace(token, json.dumps(value, ensure_ascii=False, indent=2) if not isinstance(value, str)
                          else json.dumps(value, ensure_ascii=False))
    assert not re.search(r"__[A-Z_]+__", src), name
    return src


NODES, CONN = [], {}


def node(name, ntype, version, params, pos, **extra):
    n = {"parameters": params, "id": str(uuid.uuid5(uuid.NAMESPACE_URL, "revo/" + name)), "name": name,
         "type": ntype, "typeVersion": version, "position": pos}
    n.update(extra)
    NODES.append(n)
    return name


def link(src, dst, out=0):
    outs = CONN.setdefault(src, {"main": []})["main"]
    while len(outs) <= out:
        outs.append([])
    outs[out].append({"node": dst, "type": "main", "index": 0})


def code_node(name, src, pos):
    return node(name, "n8n-nodes-base.code", 2, {"jsCode": src}, pos)


def sheet_rl(cfg_node):
    return {"__rl": True, "value": f"={{{{ $('{cfg_node}').first().json.sheet_url }}}}", "mode": "url"}


SHEET_NAME = {"__rl": True, "value": "banners", "mode": "name"}


def sheets_read(name, cfg_node, pos, filtro=None):
    params = {"operation": "read", "documentId": sheet_rl(cfg_node), "sheetName": SHEET_NAME, "options": {}}
    if filtro:
        params["filtersUI"] = {"values": [{"lookupColumn": filtro[0], "lookupValue": filtro[1]}]}
    return node(name, "n8n-nodes-base.googleSheets", 4.5, params, pos, executeOnce=True)


def sheets_write(name, cfg_node, pos, op):
    params = {
        "operation": op,
        "documentId": sheet_rl(cfg_node),
        "sheetName": SHEET_NAME,
        "columns": {"mappingMode": "autoMapInputData", "value": {}, "matchingColumns": ["id"], "schema": [],
                    "attemptToConvertTypes": False, "convertFieldsToString": False},
        "options": {},
    }
    return node(name, "n8n-nodes-base.googleSheets", 4.5, params, pos)


def http(name, pos, method, url, cred_name, body_expr=None, headers=(), timeout=120000, batch=None, **extra):
    params = {"method": method, "url": url}
    if cred_name:
        params.update({"authentication": "genericCredentialType", "genericAuthType": "httpHeaderAuth"})
    if headers:
        params["sendHeaders"] = True
        params["headerParameters"] = {"parameters": [{"name": k, "value": v} for k, v in headers]}
    if body_expr:
        params.update({"sendBody": True, "specifyBody": "json", "jsonBody": body_expr})
    options = {"timeout": timeout}
    if batch:
        options["batching"] = {"batch": {"batchSize": 1, "batchInterval": batch}}
    params["options"] = options
    kw = {"onError": "continueRegularOutput"}
    if cred_name:
        kw["notes"] = f"Credencial: Header Auth \"{cred_name}\" (ver README)"
        kw["notesInFlow"] = True
    kw.update(extra)
    return node(name, "n8n-nodes-base.httpRequest", 4.2, params, pos, **kw)


def if_node(name, pos, left, op_type, operation, right=None):
    cond = {"id": str(uuid.uuid5(uuid.NAMESPACE_URL, "revo/if/" + name)), "leftValue": left,
            "operator": {"type": op_type, "operation": operation}}
    if right is None:
        cond["operator"]["singleValue"] = True
        cond["rightValue"] = ""
    else:
        cond["rightValue"] = right
    params = {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"},
                             "conditions": [cond], "combinator": "and"}, "options": {}}
    return node(name, "n8n-nodes-base.if", 2, params, pos)


def sticky(text, pos, w, h, color):
    NODES.append({"parameters": {"content": text, "width": w, "height": h, "color": color},
                  "id": str(uuid.uuid5(uuid.NAMESPACE_URL, "revo/sticky/" + text[:40])),
                  "name": f"Nota {len(NODES)}", "type": "n8n-nodes-base.stickyNote", "typeVersion": 1,
                  "position": pos})


HF_FLARE = "https://api.higgsfield.ai/marketing-studio/image/flare"
HF_CRED = "Higgsfield API"
OPENAI_CRED = "OpenAI API"
ANTHROPIC_CRED = "Anthropic API"


def build():
    X = lambda i: 240 * i  # noqa: E731

    # ---------------- Flujo A ----------------
    y = 0
    sticky("## A · Actualizar biblioteca con Claude\nLee los productos y precios de revoimport.com. Si un producto es "
           "nuevo o cambió (precio, colores, contenido, fotos), Claude reescribe sus 5 banners y textos de Meta y los "
           "deja en la hoja con estado **pendiente**. No gasta créditos de Higgsfield.",
           [X(0) - 40, y - 200], 900, 160, 5)
    t1 = node("A ▶ Actualizar biblioteca", "n8n-nodes-base.manualTrigger", 1, {}, [X(0), y])
    t2 = node("A ⏰ Lunes 8:00", "n8n-nodes-base.scheduleTrigger", 1.2,
              {"rule": {"interval": [{"field": "weeks", "weeksInterval": 1, "triggerAtDay": [1], "triggerAtHour": 8}]}},
              [X(0), y + 160])
    cfg = code_node("A · Config", (CODE / "A_config.js").read_text(), [X(1), y + 80])
    link(t1, cfg)
    link(t2, cfg)
    web = http("A · Leer config.js de la web", [X(2), y + 80], "GET",
               "=https://revoimport.com/config.js?nocache={{ Date.now() }}", None,
               timeout=60000, executeOnce=True)
    NODES[-1]["parameters"]["options"]["response"] = {"response": {"responseFormat": "text", "outputPropertyName": "data"}}
    NODES[-1].pop("onError")
    link(cfg, web)
    ext = code_node("A · Extraer catálogo", (CODE / "A_extraer.js").read_text(), [X(3), y + 80])
    link(web, ext)
    hoja = sheets_read("A · Leer hoja", "A · Config", [X(4), y + 80])
    NODES[-1]["alwaysOutputData"] = True
    link(ext, hoja)
    det = code_node("A · Detectar cambios", code(
        "A_detectar.js",
        CLAUDE_SYSTEM=(CODE / "claude_system.md").read_text(encoding="utf-8").replace("__EJEMPLO__", canonical_example()),
        CLAUDE_SCHEMA=CLAUDE_SCHEMA), [X(5), y + 80])
    link(hoja, det)
    cl = http("A · Claude reescribe banners", [X(6), y + 80], "POST", "https://api.anthropic.com/v1/messages",
              ANTHROPIC_CRED, body_expr="={{ JSON.stringify($json.claude_body) }}",
              headers=[("anthropic-version", "2023-06-01"), ("anthropic-beta", "server-side-fallback-2026-07-01")],
              timeout=600000, batch=2000)
    link(det, cl)
    par = code_node("A · Filas para la hoja", code("A_parsear.js", TEMPLATE_NAMES=TEMPLATE_NAMES), [X(7), y + 80])
    link(cl, par)
    gua = sheets_write("A · Guardar en hoja", "A · Config", [X(8), y + 80], "appendOrUpdate")
    link(par, gua)

    # ---------------- Flujo B ----------------
    y = 560
    sticky("## B · Generar aprobados en Higgsfield\nTú apruebas en la hoja (estado = **aprobado**). Este flujo manda a "
           "Higgsfield el master 3:4 de esas filas, hasta `max_por_corrida` por clic (en *B · Config*). "
           "**Gasta créditos.** Solo se ejecuta a mano.",
           [X(0) - 40, y - 200], 900, 160, 3)
    tb = node("B ▶ Generar aprobados", "n8n-nodes-base.manualTrigger", 1, {}, [X(0), y])
    bc = code_node("B · Config", (CODE / "B_config.js").read_text(), [X(1), y])
    link(tb, bc)
    br = sheets_read("B · Leer aprobados", "B · Config", [X(2), y], filtro=("estado", "aprobado"))
    link(bc, br)
    bp = code_node("B · Preparar solicitudes", (CODE / "B_preparar.js").read_text(), [X(3), y])
    link(br, bp)
    bh = http("B · Higgsfield master 3:4", [X(4), y], "POST", HF_FLARE, HF_CRED,
              body_expr="={{ JSON.stringify($json.hf_body) }}",
              headers=[("Idempotency-Key", "={{ $json.idempotency_key }}")], batch=1000)
    link(bp, bh)
    bu = code_node("B · Unir respuesta", (CODE / "B_unir.js").read_text(), [X(5), y])
    link(bh, bu)
    bg = sheets_write("B · Guardar en hoja", "B · Config", [X(6), y], "update")
    link(bu, bg)

    # ---------------- Flujo C ----------------
    y = 1100
    sticky("## C · Revisar pendientes (cada 5 min)\nConsulta en Higgsfield los trabajos en curso. Cuando el master "
           "termina, **GPT-6 Astra** lo revisa (textos exactos, sin logos, producto fiel, nada cortado). Si aprueba, "
           "pide las versiones **1:1 (Feed)** y **9:16 (Stories/Reels)**; si no, la fila queda en **revisar** con los "
           "problemas anotados. Cuando ambas versiones terminan, la fila pasa a **listo**.",
           [X(0) - 40, y - 220], 1300, 180, 4)
    tc1 = node("C ▶ Revisar ahora", "n8n-nodes-base.manualTrigger", 1, {}, [X(0), y])
    tc2 = node("C ⏰ Cada 5 minutos", "n8n-nodes-base.scheduleTrigger", 1.2,
               {"rule": {"interval": [{"field": "minutes", "minutesInterval": 5}]}}, [X(0), y + 160])
    cc = code_node("C · Config", (CODE / "C_config.js").read_text(), [X(1), y + 80])
    link(tc1, cc)
    link(tc2, cc)
    ch = sheets_read("C · Leer hoja", "C · Config", [X(2), y + 80])
    link(cc, ch)
    cf = code_node("C · Trabajos en curso", (CODE / "C_filtrar.js").read_text(), [X(3), y + 80])
    link(ch, cf)
    ism = if_node("C · ¿Es master?", [X(4), y + 80], "={{ $json.tipo }}", "string", "equals", "master")
    link(cf, ism)

    em = http("C · Estado master", [X(5), y], "GET", "={{ $json.status_url }}", HF_CRED, timeout=60000)
    link(ism, em, 0)
    um = code_node("C · Unir estado master", code("C_unir_master.js",
                                                   QA_PROMPT=(CODE / "qa_prompt.md").read_text(encoding="utf-8"),
                                                   QA_SCHEMA=QA_SCHEMA), [X(6), y])
    link(em, um)
    ml = if_node("C · ¿Master listo?", [X(7), y], "={{ $json.fase }}", "string", "equals", "completado")
    link(um, ml)
    qa = http("C · QA con GPT-6 Astra", [X(8), y - 120], "POST", "https://api.openai.com/v1/responses", OPENAI_CRED,
              body_expr="={{ JSON.stringify($json.qa_body) }}", timeout=300000, batch=1000)
    link(ml, qa, 0)
    lq = code_node("C · Leer QA", (CODE / "C_leer_qa.js").read_text(), [X(9), y - 120])
    link(qa, lq)
    qok = if_node("C · ¿QA aprobado?", [X(10), y - 120], "={{ $json.qa_aprobado }}", "boolean", "true")
    link(lq, qok)
    pf = code_node("C · Preparar formatos", (CODE / "C_preparar_formatos.js").read_text(), [X(11), y - 200])
    link(qok, pf, 0)
    hf = http("C · Higgsfield 1:1 y 9:16", [X(12), y - 200], "POST", HF_FLARE, HF_CRED,
              body_expr="={{ JSON.stringify($json.hf_body) }}",
              headers=[("Idempotency-Key", "={{ $json.idempotency_key }}")], batch=1000)
    link(pf, hf)
    uf = code_node("C · Unir formatos", (CODE / "C_unir_formatos.js").read_text(), [X(13), y - 200])
    link(hf, uf)
    mr = code_node("C · Marcar revisar", (CODE / "C_marcar_revisar.js").read_text(), [X(11), y - 40])
    link(qok, mr, 1)
    fa = if_node("C · ¿Falló?", [X(8), y + 120], "={{ $json.fase }}", "string", "equals", "fallido")
    link(ml, fa, 1)
    me = code_node("C · Marcar error", (CODE / "C_marcar_error.js").read_text(), [X(9), y + 120])
    link(fa, me, 0)

    ef = http("C · Estado formatos", [X(5), y + 280], "GET", "={{ $json.status_url }}", HF_CRED, timeout=60000)
    link(ism, ef, 1)
    af = code_node("C · Agrupar formatos", (CODE / "C_agrupar_formatos.js").read_text(), [X(6), y + 280])
    link(ef, af)

    cg = sheets_write("C · Guardar en hoja", "C · Config", [X(14), y + 80], "update")
    for src in (uf, mr, me, af):
        link(src, cg)

    wf = {
        "name": "REVO · Banners Meta Ads (Claude + GPT-6 Astra + Higgsfield)",
        "nodes": NODES,
        "connections": CONN,
        "pinData": {},
        "active": False,
        "settings": {"executionOrder": "v1", "timezone": "America/Lima", "saveManualExecutions": True},
        "meta": {"templateCredsSetupCompleted": False},
        "tags": [],
    }
    out = ROOT / "n8n" / "revo-meta-ads-workflow.json"
    out.write_text(json.dumps(wf, ensure_ascii=False, indent=2), encoding="utf-8")
    names = {n["name"] for n in NODES}
    for src, d in CONN.items():
        assert src in names, src
        for branch in d["main"]:
            for c in branch:
                assert c["node"] in names, c["node"]
    print(f"{len(NODES)} nodos -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    build()
