// Arma la solicitud a Higgsfield (Marketing Studio Image 2.5 Flare) para el master 3:4 de cada fila aprobada.
const cfg = $('B · Config').first().json;
const filas = $input.all().map((i) => i.json).filter((r) => r.id && r.estado === 'aprobado');
const lote = Date.now();
return filas.slice(0, cfg.max_por_corrida).map((r) => ({
  json: {
    id: r.id,
    // Misma clave en reintentos de esta corrida; nueva clave si vuelves a aprobar la fila más tarde.
    idempotency_key: `${r.id}-v${r.version || 1}-master-${lote}`,
    hf_body: {
      prompt: r.prompt_master_3x4,
      image_urls: String(r.refs || '').split('|').map((u) => u.trim()).filter(Boolean).slice(0, 16),
      aspect_ratio: '3:4',
      resolution: cfg.resolucion,
      quality: cfg.calidad,
      enhance_prompt: false,
    },
  },
}));
