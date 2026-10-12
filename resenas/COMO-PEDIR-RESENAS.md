# Reseñas reales para los banners T4

Los banners T4 traen una tarjeta de reseña en blanco. Solo se publican con la reseña real de un
cliente, con sus palabras y con su permiso. No se inventan ni se reescriben.

## 1. Pedir la reseña (WhatsApp)

Entre 3 y 7 días después de la entrega, en el mismo chat donde compró. Mándalo a todos los
compradores, no solo a los que crees contentos.

**Mensaje 1**

> Hola [Nombre], te saluda [tu nombre] de REVO. ¿Qué tal te va con tu [producto]? Si tienes un
> minuto, cuéntanos con tus palabras cómo te fue con la compra, lo bueno y lo que podríamos
> mejorar. Nos ayuda un montón. ¡Gracias por confiar en nosotros!

**Mensaje 2** (solo después de que responda)

> ¡Gracias, [Nombre]! ¿Nos das permiso para publicar tu comentario tal cual lo escribiste (o solo
> una parte, sin cambiar tus palabras) en nuestros anuncios de Facebook e Instagram y en
> revoimport.com? Saldría solo con tu nombre, la inicial de tu apellido y tu distrito (ej.: Carla M.,
> Surco). Puedes pedirnos que lo quitemos cuando quieras escribiéndonos por aquí. Si estás de
> acuerdo, respóndenos: "Sí, autorizo".

Si no contesta "Sí, autorizo", esa reseña no se usa.

## 2. Anotarla en `resenas.csv`

| Columna | Qué va |
|---|---|
| producto_id | El producto que compró (ej.: `iphone-17`, `combo-pro-3-a1`). La reseña va solo en el banner de ese producto. |
| texto | Lo que escribió, tal cual. Puedes recortar con "…" sin cambiar el sentido y corregir tildes o mayúsculas. Nada más. |
| nombre | Nombre e inicial del apellido: "Carla M." |
| ciudad | Distrito o ciudad: "Surco", "Arequipa" |
| estrellas | 1 a 5 si el cliente dio nota. Vacío si no la dio (la tarjeta sale sin estrellas). |
| fecha, pedido, captura | Para tu control: fecha del mensaje, número de pedido y link a la captura del chat. |
| permiso | `sí` solo si respondió "Sí, autorizo". Con `no`, no se procesa. |

No uses una reseña que diga "AirPods", "originales", "garantía Apple", "entrega inmediata" o datos
técnicos que la web no tiene: el anuncio quedaría prometiendo algo que no se puede sostener.

## 3. Ponerla en el banner (0 créditos)

```bash
python3 scripts/poner_resena.py --csv resenas/resenas.csv --carpeta <carpeta con <producto_id>__T4/master.png y v916.png>
```

Sale el Feed, Stories y Reels de ese banner con la reseña escrita en la tarjeta. O pásale las
reseñas a Claude en el chat y él las coloca.

Una reseña de 1 a 2 líneas (hasta unos 140 caracteres) se ve mejor. Si es muy larga, el script avisa
y hay que recortarla con "…".
