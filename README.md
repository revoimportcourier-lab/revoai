# REVO · Banners para Meta Ads (Claude + GPT-6 Astra + Higgsfield + n8n)

Biblioteca de banners para todos los productos y servicios de **revoimport.com** y un workflow de n8n
que la mantiene al día y genera las imágenes con aprobación previa.

```
revoimport.com ──► Claude (copy y prompts) ──► Google Sheet ──► tú apruebas
                                                                   │
           listo ◄── 1:1 y 9:16 ◄── GPT-6 Astra (control) ◄── Higgsfield (master 3:4)
```

## Qué hay

| Archivo | Para qué |
|---|---|
| `prompts/BANNERS.md` | Los 81 banners listos para copiar: referencias, prompt master 3:4, redimensión 1:1 y 9:16, y textos de Meta |
| `prompts/banners.csv` | La misma biblioteca como tabla, para importar en Google Sheets (la usa n8n) |
| `prompts/PLANTILLAS.md` | Cómo se adaptaron tus 6 prompts y qué reglas siguen |
| `catalogo/revo-catalogo.json` | Productos, precios, afirmaciones permitidas/prohibidas y fotos de revoimport.com |
| `brief/meta-ads-brief-revo.md` | El brief de Meta Ads completado con lo que dice tu web + investigación del comprador |
| `n8n/revo-meta-ads-workflow.json` | Workflow para importar en n8n |
| `n8n/code/` | Código de cada nodo (para revisarlo o cambiarlo) |
| `scripts/` | Regeneran la biblioteca y el workflow |

## Opción 1 · Usar los prompts directo en Higgsfield

1. Abre `prompts/BANNERS.md` y elige un banner.
2. En Higgsfield, Marketing Studio Image (2.5 Flare), sube o importa las fotos de "Referencias" en el
   mismo orden (todas son links de revoimport.com), pega el **prompt master** y elige **3:4**.
3. Con la imagen lista, úsala como referencia, pega el prompt **1:1** (Feed) y luego el **9:16**
   (Stories y Reels).

## Opción 2 · Automatizar con n8n

### Preparación (una vez)

1. **Google Sheet**: crea una hoja nueva, *Archivo → Importar →* `prompts/banners.csv`, y nombra la
   pestaña `banners`.
2. **n8n**: *Workflows → Import from file →* `n8n/revo-meta-ads-workflow.json`.
3. **Credenciales** (en n8n, tipo *Header Auth*), y asígnalas a los nodos HTTP que indica cada nota:
   - `Anthropic API`: nombre `x-api-key`, valor tu API key de Anthropic.
   - `OpenAI API`: nombre `Authorization`, valor `Bearer TU_API_KEY`. Tu cuenta necesita acceso a
     `gpt-6-astra` (OpenAI lo está abriendo por etapas). Si aún no lo tienes, cambia
     `openai_model` en *C · Config* por otro modelo de OpenAI con visión que sí tengas.
   - `Higgsfield API`: nombre `Authorization`, valor `Key TU_KEY_ID:TU_KEY_SECRET` (se crean en
     console.higgsfield.ai).
   - *Google Sheets OAuth2* en los nodos de hoja.
4. Pega el link de tu Google Sheet en `sheet_url` dentro de **A · Config**, **B · Config** y **C · Config**.
5. Activa el workflow para que corran las tareas programadas (C cada 5 minutos, A los lunes 8:00).

### Uso diario

| Paso | Quién | Qué pasa |
|---|---|---|
| **A ▶ Actualizar biblioteca** | n8n + Claude (`claude-opus-5-5`) | Lee precios y productos de revoimport.com. Si algo cambió o hay un producto nuevo, Claude reescribe sus 5 banners y textos. Quedan en estado `pendiente`. No gasta créditos de Higgsfield. |
| Aprobar | Tú | En la hoja, cambia `estado` a `aprobado` en los banners que quieras generar. |
| **B ▶ Generar aprobados** | n8n + Higgsfield | Manda el master 3:4 de hasta `max_por_corrida` filas (por defecto 2). **Gasta créditos.** Solo corre a mano. |
| C (cada 5 min) | n8n + GPT-6 Astra + Higgsfield | Cuando el master termina, GPT-6 Astra revisa textos, logos, fidelidad del producto y encuadre. Si aprueba, pide las versiones 1:1 y 9:16; si no, deja la fila en `revisar` con los problemas anotados. |

Estados de la hoja: `pendiente` → `aprobado` → `generando_master` → `generando_formatos` → `listo`
(o `listo_falta_resena` en la plantilla T4). Si algo sale mal: `revisar`, `error`, `error_formatos`
o `error_claude`, con el detalle en `qa_problemas`. Para regenerar una fila, vuelve a ponerla en `aprobado`.

### Antes de publicar en Meta

- Usa la versión 4:5 (o 1:1) para Feed, la 9:16 para Stories y la versión Reels para Reels, en el mismo anuncio.
  La versión Reels sale de la 9:16 con `python3 scripts/reels_safe.py entrada.png salida.png`: aleja la
  imagen para que titular, producto, precio y botón queden fuera del 14 % superior y el 35 % inferior,
  que tapa la interfaz de Reels.
- Sube los 3 textos principales y los 3 títulos como opciones del mismo anuncio. Botón: *Enviar mensaje* (WhatsApp).
- Las T4 llevan la tarjeta de reseña en blanco: complétala con una reseña real (con permiso del cliente) o no publiques esa versión.
- Revisa que el precio siga igual en la web.

## Cosas que debes confirmar o saber

- **Audífonos Pro 3**: las fotos de tu web los muestran en cajas con el logo de Apple, aunque la web
  aclara que no son originales. Los prompts usan esas fotos solo para la forma, quitan todo logo y
  agregan "Audífonos compatibles, no originales de Apple." Aun así, Meta puede rechazar anuncios de
  productos que imitan a una marca; conviene tener fotos propias sin logos.
- Afirmaciones tomadas de tu web que conviene que confirmes antes de pautar: "nuevo y sellado",
  "1 año de garantía por fallas de fábrica", "original" (cargador de 40 W y cubo de los combos) y los
  4 regalos del iPhone.
- La web no publica razón social, RUC ni dirección. Publicarlos ayuda con la confianza que buscan
  estos anuncios.
- Ningún banner usa el logo de Apple ni la palabra AirPods.

## Regenerar

```bash
python3 scripts/build_banners.py   # catálogo → prompts/banners.{json,csv}, BANNERS.md
python3 scripts/build_n8n.py       # código de n8n/code → n8n/revo-meta-ads-workflow.json
```
