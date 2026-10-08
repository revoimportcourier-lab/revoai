// Cuando las dos versiones terminan, guarda sus links y marca la fila como lista.
const prev = $('C · ¿Es master?').all(1).map((i) => i.json);
const now = new Date().toISOString();
const FIN_MAL = ['failed', 'nsfw', 'canceled'];
const grupos = {};
$input.all().forEach((item, i) => {
  const s = item.json;
  const p = prev[i];
  const g = grupos[p.id] || (grupos[p.id] = { fila: p.fila, res: {} });
  g.res[p.ratio] = {
    status: s.status || (s.error ? 'error_consulta' : ''),
    url: (s.images && s.images[0] && s.images[0].url) || '',
  };
});
const out = [];
for (const [id, g] of Object.entries(grupos)) {
  const estados = Object.values(g.res).map((x) => x.status);
  if (estados.some((x) => FIN_MAL.includes(x))) {
    out.push({ json: { id, estado: 'error_formatos', qa_problemas: `Formato con estado ${estados.join('/')}`, actualizado: now } });
  } else if (estados.length === 2 && estados.every((x) => x === 'completed')) {
    out.push({
      json: {
        id,
        estado: g.fila.requiere_resena_real === 'sí' ? 'listo_falta_resena' : 'listo',
        url_1x1: g.res['1x1'].url,
        url_9x16: g.res['9x16'].url,
        actualizado: now,
      },
    });
  }
}
return out;
