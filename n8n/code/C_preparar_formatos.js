// Con el master aprobado, pide a Higgsfield las versiones 1:1 (Feed) y 9:16 (Stories y Reels).
const cfg = $('C · Config').first().json;
const out = [];
for (const item of $input.all()) {
  const p = item.json;
  const r = p.fila;
  for (const [ratio, aspect, prompt] of [['1x1', '1:1', r.prompt_1x1], ['9x16', '9:16', r.prompt_9x16]]) {
    out.push({
      json: {
        id: r.id,
        ratio,
        url_master: p.url_master,
        qa_problemas: p.qa_problemas,
        idempotency_key: `${r.id}-v${r.version || 1}-${ratio}-${r.request_master}`,
        hf_body: {
          prompt,
          image_urls: [p.url_master],
          aspect_ratio: aspect,
          resolution: cfg.resolucion,
          quality: cfg.calidad,
          enhance_prompt: false,
        },
      },
    });
  }
}
return out;
