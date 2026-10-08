// Agrupa por fila los request_id de los dos formatos.
const prev = $('C · Preparar formatos').all().map((i) => i.json);
const now = new Date().toISOString();
const porFila = {};
$input.all().forEach((item, i) => {
  const s = item.json;
  const p = prev[i];
  const row = porFila[p.id] || (porFila[p.id] = {
    id: p.id, estado: 'generando_formatos', url_master: p.url_master,
    qa_resultado: 'aprobado', qa_problemas: p.qa_problemas || '', actualizado: now,
  });
  if (s.error || !s.request_id) {
    row.estado = 'error_formatos';
    row.qa_problemas = `${row.qa_problemas} | Higgsfield no aceptó el formato ${p.ratio}`.replace(/^ \| /, '');
    return;
  }
  row[`request_${p.ratio}`] = s.request_id;
  row[`status_url_${p.ratio}`] = s.status_url;
});
return Object.values(porFila).map((json) => ({ json }));
