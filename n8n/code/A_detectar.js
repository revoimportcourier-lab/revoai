// Compara la web con la hoja: solo los productos nuevos o con huella distinta van a Claude.
const cfg = $('A · Config').first().json;
const fichas = $('A · Extraer catálogo').all().map((i) => i.json);
const filas = $('A · Leer hoja').all().map((i) => i.json).filter((r) => r && r.id);

const SYSTEM = __CLAUDE_SYSTEM__;
const SCHEMA = __CLAUDE_SCHEMA__;
const PLANTILLAS = ['T1', 'T2', 'T3', 'T4', 'T5'];

const out = [];
for (const f of fichas) {
  const actuales = filas.filter((r) => r.producto_id === f.id);
  const cambio = actuales.length === 0 || actuales.some((r) => String(r.huella) !== f.huella);
  if (!cambio) continue;
  const pedido = {
    tarea: actuales.length ? 'actualizar' : 'crear',
    plantillas: PLANTILLAS,
    producto: f,
    filas_actuales: actuales.map((r) => ({
      plantilla: r.plantilla,
      refs: String(r.refs || '').split('|').map((u) => u.trim()).filter(Boolean),
      textos_imagen: r.textos_imagen,
      prompt_master_3x4: r.prompt_master_3x4,
      prompt_1x1: r.prompt_1x1,
      prompt_9x16: r.prompt_9x16,
    })),
    meta_actual: actuales[0]
      ? {
          textos: [actuales[0].meta_texto_1, actuales[0].meta_texto_2, actuales[0].meta_texto_3],
          titulos: [actuales[0].meta_titulo_1, actuales[0].meta_titulo_2, actuales[0].meta_titulo_3],
          descripcion: actuales[0].meta_descripcion,
        }
      : null,
  };
  out.push({
    json: {
      producto_id: f.id,
      ficha: f,
      actuales: actuales.map((r) => ({ id: r.id, version: r.version })),
      claude_body: {
        model: cfg.claude_model,
        max_tokens: 32000,
        fallbacks: 'default',
        output_config: { effort: cfg.claude_effort, format: { type: 'json_schema', schema: SCHEMA } },
        system: [{ type: 'text', text: SYSTEM, cache_control: { type: 'ephemeral' } }],
        messages: [{ role: 'user', content: JSON.stringify(pedido) }],
      },
    },
  });
}
return out;
