// Interpreta el veredicto de GPT-6 Astra.
const prev = $('C · ¿Master listo?').all(0).map((i) => i.json);
return $input.all().map((item, i) => {
  const r = item.json;
  let text = r.output_text || '';
  if (!text && Array.isArray(r.output)) {
    for (const o of r.output) {
      if (o.type !== 'message') continue;
      for (const c of o.content || []) if (c.type === 'output_text') text += c.text;
    }
  }
  let qa = null;
  try { qa = JSON.parse(text); } catch (e) { qa = null; }
  const problemas = qa
    ? (qa.problemas || []).join(' | ')
    : `QA sin respuesta válida${r.error ? `: ${JSON.stringify(r.error).slice(0, 200)}` : ''}`;
  return { json: { ...prev[i], qa_aprobado: !!(qa && qa.aprobado), qa_problemas: problemas } };
});
