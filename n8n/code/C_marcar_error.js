// Higgsfield terminó el master con error.
const now = new Date().toISOString();
return $input.all().map((item) => ({
  json: {
    id: item.json.id,
    estado: 'error',
    qa_problemas: `Higgsfield terminó el master con estado "${item.json.status}"`,
    actualizado: now,
  },
}));
