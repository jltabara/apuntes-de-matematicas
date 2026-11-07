# Apuntes de Matemáticas

Biblioteca estática preparada para GitHub Pages. La carpeta `docs` contiene la web completa: HTML, CSS, JavaScript, los ZIP de fuentes y los PDF asociados por nombre. Los originales no se modifican. Las versiones permanecen como entradas separadas.

## Ver la web

Abre `docs/index.html` en tu navegador, o ejecuta desde esta carpeta:

```sh
python3 -m http.server 8765 --directory docs
```

Visita http://localhost:8765. El visor usa el lector PDF del navegador; se ofrece también apertura independiente y descarga. En móvil el lector aparece debajo del catálogo.

## Publicar en GitHub Pages

1. En la cuenta `jltabara`, crea el repositorio `apuntes-de-matematicas`.
2. Sube el contenido de esta carpeta `web` conservando `docs` como subcarpeta. Para subir todos los archivos cómodamente puedes utilizar GitHub Desktop.
3. En el repositorio, abre Settings → Pages. Selecciona Deploy from a branch, rama `main`, carpeta `/docs`, y guarda.
4. La dirección prevista es https://jltabara.github.io/apuntes-de-matematicas/ una vez publicado. Todavía no se ha creado el repositorio ni publicado la web.

Referencia: https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site

## Actualizar el catálogo

En la organización actual, con `web` junto a las carpetas de libros:

```sh
python3 web/scripts/generar.py
```

El script requiere `pdfinfo` (Poppler) para contar las páginas de los PDF y regenera el catálogo y las descargas. Si se retiran obras, elimina también sus antiguos ZIP/PDF de `docs/fuentes` y `docs/pdf` antes de publicar. El script necesita las carpetas originales para regenerar, pero la web publicada funciona de manera independiente.

## Fuentes y recursos

Los ZIP conservan la estructura original e incluyen recursos locales y compartidos, y un LEEME. Los archivos .tex, .bib, .sty y .cls se convierten a UTF-8 y sus declaraciones inputenc se actualizan. Los originales permanecen intactos. En Overleaf, sube el ZIP como proyecto y selecciona el documento principal indicado en LEEME.txt. El informe-codificacion.json registra caracteres dañados y controles preexistentes; los ZIP afectados incluyen AVISOS-CODIFICACION.txt. Se han compilado con MacTeX las 67 fuentes que inicialmente carecían de PDF; consulta compilacion/INFORME.md para las advertencias. Algunas fuentes antiguas pueden necesitar ajustes de rutas, paquetes o codificación. `informe-recursos.json` recoge las referencias no encontradas durante el análisis. El catálogo se actualiza con los PDF existentes. Para compilar nuevas fuentes sin PDF utiliza `python3 web/scripts/compilar.py` desde la carpeta raíz y después regenera el catálogo.

No se ha aplicado una licencia general a los documentos; se conservan sus autores y contenido original.

## Obras retiradas

`excluidos.json` impide que las obras retiradas reaparezcan al regenerar el catálogo. Sus descargas se conservan fuera de la web pública, en `retirados/`; los originales no se modifican.
