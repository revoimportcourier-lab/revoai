// Toma las filas con trabajos en curso: masters por revisar y formatos por terminar.
const out = [];
for (const r of $input.all().map((i) => i.json)) {
  if (!r.id) continue;
  if (r.estado === 'generando_master' && r.status_url_master) {
    out.push({ json: { tipo: 'master', id: r.id, status_url: r.status_url_master, fila: r } });
  }
  if (r.estado === 'generando_formatos') {
    for (const ratio of ['1x1', '9x16']) {
      if (r[`status_url_${ratio}`]) {
        out.push({ json: { tipo: 'formato', ratio, id: r.id, status_url: r[`status_url_${ratio}`], fila: r } });
      }
    }
  }
}
return out;
