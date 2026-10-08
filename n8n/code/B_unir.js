// Guarda en la hoja el request_id que devolvió Higgsfield.
const prev = $('B · Preparar solicitudes').all().map((i) => i.json);
const now = new Date().toISOString();
return $input.all().map((item, i) => {
  const r = item.json;
  const fila = prev[i];
  if (r.error || !r.request_id) {
    return {
      json: {
        id: fila.id,
        estado: 'error',
        qa_problemas: `Higgsfield no aceptó el master: ${JSON.stringify(r.error || r).slice(0, 300)}`,
        actualizado: now,
      },
    };
  }
  return {
    json: {
      id: fila.id,
      estado: 'generando_master',
      request_master: r.request_id,
      status_url_master: r.status_url,
      url_master: '', qa_resultado: '', qa_problemas: '',
      request_1x1: '', status_url_1x1: '', url_1x1: '', request_9x16: '', status_url_9x16: '', url_9x16: '',
      actualizado: now,
    },
  };
});
