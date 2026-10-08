// El QA encontró problemas: queda para que lo revises (vuelve a poner "aprobado" para regenerar).
const now = new Date().toISOString();
return $input.all().map((item) => ({
  json: {
    id: item.json.id,
    estado: 'revisar',
    url_master: item.json.url_master,
    qa_resultado: 'observado',
    qa_problemas: item.json.qa_problemas,
    actualizado: now,
  },
}));
