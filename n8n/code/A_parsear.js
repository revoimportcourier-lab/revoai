// Convierte la respuesta de Claude en filas de la hoja (estado "pendiente" para que las apruebes).
const prev = $('A · Detectar cambios').all().map((i) => i.json);
const now = new Date().toISOString();
const NOMBRES = __TEMPLATE_NAMES__;
const VACIO = {
  request_master: '', status_url_master: '', url_master: '', qa_resultado: '', qa_problemas: '',
  request_1x1: '', status_url_1x1: '', url_1x1: '', request_9x16: '', status_url_9x16: '', url_9x16: '',
};

const out = [];
$input.all().forEach((item, idx) => {
  const ctx = prev[idx];
  const r = item.json;
  let data = null;
  let error = '';
  if (r.error) error = `Error de la API de Claude: ${JSON.stringify(r.error).slice(0, 300)}`;
  else if (r.stop_reason === 'refusal') error = 'Claude rechazó la solicitud.';
  else if (r.stop_reason === 'max_tokens') error = 'La respuesta de Claude quedó cortada (max_tokens).';
  else {
    try {
      data = JSON.parse((r.content || []).filter((b) => b.type === 'text').map((b) => b.text).join(''));
    } catch (e) {
      error = 'La respuesta de Claude no es JSON válido.';
    }
  }
  if (!data) {
    for (const a of ctx.actuales) {
      out.push({ json: { id: a.id, estado: 'error_claude', qa_problemas: error, actualizado: now } });
    }
    return;
  }
  const f = ctx.ficha;
  const meta = data.meta || {};
  for (const fila of data.filas || []) {
    const id = `${f.id}__${fila.plantilla}`;
    const anterior = ctx.actuales.find((a) => a.id === id);
    out.push({
      json: {
        id,
        producto_id: f.id,
        producto: f.nombre,
        categoria: f.categoria,
        plantilla: fila.plantilla,
        plantilla_nombre: NOMBRES[fila.plantilla] || fila.plantilla,
        precio: f.precio,
        link: f.link,
        refs: (fila.refs || []).join(' | '),
        textos_imagen: JSON.stringify(fila.textos_imagen || []),
        prompt_master_3x4: fila.prompt_master_3x4,
        prompt_1x1: fila.prompt_1x1,
        prompt_9x16: fila.prompt_9x16,
        meta_texto_1: (meta.textos || [])[0] || '',
        meta_texto_2: (meta.textos || [])[1] || '',
        meta_texto_3: (meta.textos || [])[2] || '',
        meta_titulo_1: (meta.titulos || [])[0] || '',
        meta_titulo_2: (meta.titulos || [])[1] || '',
        meta_titulo_3: (meta.titulos || [])[2] || '',
        meta_descripcion: meta.descripcion || '',
        meta_boton: 'Enviar mensaje',
        requiere_resena_real: fila.plantilla === 'T4' ? 'sí' : 'no',
        huella: f.huella,
        estado: 'pendiente',
        version: (Number(anterior && anterior.version) || 0) + 1,
        ...VACIO,
        actualizado: now,
        notas_claude: data.notas || '',
      },
    });
  }
});
return out;
