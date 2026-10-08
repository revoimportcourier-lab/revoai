// Lee el estado del master y, si terminó, prepara la revisión de calidad con GPT-6 Astra.
const prev = $('C · ¿Es master?').all(0).map((i) => i.json);
const cfg = $('C · Config').first().json;
const QA_PROMPT = __QA_PROMPT__;
const QA_SCHEMA = __QA_SCHEMA__;

return $input.all().map((item, i) => {
  const s = item.json;
  const r = prev[i].fila;
  const status = s.status || (s.error ? 'error_consulta' : '');
  const fase = status === 'completed' ? 'completado' : ['failed', 'nsfw', 'canceled'].includes(status) ? 'fallido' : 'en_proceso';
  const url = (s.images && s.images[0] && s.images[0].url) || '';
  let textos = [];
  try { textos = JSON.parse(r.textos_imagen || '[]'); } catch (e) { textos = []; }
  const refs = String(r.refs || '').split('|').map((u) => u.trim()).filter(Boolean).slice(0, 3);
  const qa_body = fase !== 'completado' ? null : {
    model: cfg.openai_model,
    input: [{
      role: 'user',
      content: [
        {
          type: 'input_text',
          text: QA_PROMPT.replace('{PRODUCTO}', r.producto).replace('{TEXTOS}', textos.map((t) => `- "${t}"`).join('\n')),
        },
        { type: 'input_image', image_url: url },
        ...refs.map((u) => ({ type: 'input_image', image_url: u })),
      ],
    }],
    text: { format: { type: 'json_schema', name: 'qa_banner', strict: true, schema: QA_SCHEMA } },
  };
  return { json: { id: r.id, fila: r, fase, status, url_master: url, qa_body } };
});
