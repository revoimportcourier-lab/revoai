# Insumos de los banners inteligentes

`scripts/banners_inteligentes.py <carpeta_insumos> <carpeta_salida>` necesita en la carpeta de insumos:

| Archivo | De dónde sale |
|---|---|
| `escena_pedestal_onix.png`, `escena_pedestal_marfil.png`, `escena_mesa_onix.png` | Escenarios vacíos hechos en Higgsfield (GPT Image 2.5, 9:16, 2k, high; 2.75 créditos c/u). Se reutilizan para todos los productos. |
| `iphone17pm_sin_logo.png` | Foto de revoimport.com (`iphone-17-pro-max/orange/1-orange.webp`) con el logo de la espalda borrado en local. |
| `pro3_caja.png` | Foto de revoimport.com (`cutouts/01-pro3-en-caja.webp`) sin el sticker de la caja. |
| `case.png`, `cable_usbc.png` | Fotos de revoimport.com (`accessories/case-iphone.webp`, `accessories/cable-usbc-usbc.webp`). |
| `escenas.json` | Dónde está la tapa de cada pedestal (`top`, fracción del alto) y su ancho (`w`). |

Escenarios generados el 12/10/2026:
- `escena_pedestal_onix`: https://d8j0ntlcm91z4.cloudfront.net/user_3KMPU3cllWDs0kddxRt2XH7vQOr/hf_20261012_162131_7fd53d8a-0f8a-4f2b-9ebc-8fd43454de6e.png
- `escena_pedestal_marfil`: https://d8j0ntlcm91z4.cloudfront.net/user_3KMPU3cllWDs0kddxRt2XH7vQOr/hf_20261012_162132_26224dbf-0b87-403a-a8e2-4d2bca2a99f2.png
- `escena_mesa_onix`: https://d8j0ntlcm91z4.cloudfront.net/user_3KMPU3cllWDs0kddxRt2XH7vQOr/hf_20261012_162131_7c626dbd-67d4-4f9f-8792-baa082cf1e75.png

Prueba descartada: la foto "Lujo ónix" de Marketing Studio redibuja el producto (el iPhone salió con otro
diseño y con el logo de Apple), así que no sirve para mostrar el producto real.
