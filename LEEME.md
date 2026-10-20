# Aprueba TCAE – Reels automáticos

Publica sola **2 reels al día**, a la vez en **Instagram, TikTok y YouTube Shorts**, con su **Story** en Instagram y
TikTok, para llevar opositores de TCAE de **toda España** a **apruebatcae.com**.

| Hora (España) | Hueco | Instagram | TikTok | YouTube |
|---|---|---|---|---|
| 8:00 | `manana` | Story (el reel completo) | Reel | Short |
| 14:30 | `mediodia` | Reel + story | Reel | Short |
| 18:00 | chuleta | Carrusel | Carrusel de fotos | — |
| 21:30 | `noche` | Reel + story | Reel | Short |

El reel de las 8:00 no va al feed de Instagram (un cuarto post diario quitaría alcance a los otros en una cuenta que
empieza); en TikTok y YouTube publicar más a menudo sí suma. El carrusel de TikTok con los fotogramas del reel se ha
quitado porque duplicaba el vídeo: el carrusel de TikTok es ahora la chuleta (se puede reactivar con `TIKTOK_CARRUSEL`).

El workflow arranca ~30 min antes (generar, verificar y revisar lleva 15-25 min) y publica en cuanto el reel está listo
(normalmente entre las 14:10 y las 14:30, y entre las 21:10 y las 21:30). Esperar a la hora exacta gasta minutos; si lo
prefieres, pon la variable `PUBLISH_MAX_WAIT_MIN` (p. ej. 15). El cambio de horario verano/invierno se gestiona solo. Si alguien relanza
el workflow de un hueco ya publicado, no se publica dos veces (salvo `FORCE=true`).

## Qué se publica en cada hueco (todo a la vez; si un destino falla, los demás siguen)
| Red | Qué |
|---|---|
| Instagram | **Reel** (portada = fotograma del gancho, ubicación opcional) + **Story** propia de 12 s |
| TikTok | **El mismo vídeo**, publicado a la vez (vía Zernio) |
| TikTok | **Story**: la API de TikTok no permite publicar Stories directamente; la story se envía a tu **buzón de TikTok como borrador** y desde la notificación la publicas como Story con un toque |
| YouTube | **Short** (no "made for kids") |

La **Story** (12 s) muestra la pregunta del reel como una vista previa con esquinas redondeadas, cuenta atrás, "¿A, B, C o
D?" y "La solución, en el reel de hoy" (sin desvelar la respuesta): lleva tráfico al reel y se entiende sin sonido.
Interruptores en **Variables**: `IG_STORY`, `TIKTOK`, `TIKTOK_CARRUSEL` (por defecto `false`), `TIKTOK_STORY_BORRADOR`,
`YOUTUBE` → `true`, `false`, `mediodia` o `noche`. En TikTok la web se nombra tal cual (el enlace de la bio de TikTok no
es clicable hasta tener seguidores suficientes).

## La solución, al día siguiente (más comentarios)
Los reels **no enseñan la respuesta**: tras la cuenta atrás sale "¿Cuál es la tuya? · COMENTA · SOLUCIÓN MAÑANA" y la
voz invita a dejar la letra en comentarios. Al día siguiente a las **13:00** el workflow *Soluciones* (`soluciones.py`)
publica la solución de cada reel de ayer:
- **Instagram:** comentario en el reel con la solución y su explicación (texto ya verificado al crear el reel) y una
  respuesta a cada persona que dejó su letra ("✅ ¡Correcta! Era la B" / "Esta vez no 😉 Era la B"). Los comentarios
  que no son una respuesta no se contestan.
- **Instagram stories:** una story "SOLUCIÓN DE AYER" por reel (la pregunta con la correcta marcada y el porqué).
- **TikTok:** un carrusel de fotos "Soluciones del reto de ayer" (la API de TikTok no permite comentar).
Las imágenes de solución se guardan en `soluciones/` del repositorio (público) y el registro en `soluciones_hechas.json`.
Interruptores (Variables): `SOLUCION_MANANA=false` vuelve a los reels con la solución dentro; `SOLUCIONES_TIKTOK`,
`SOLUCIONES_STORIES`, `SOLUCIONES_RESPUESTAS` = `false` desactivan cada parte. El repaso exprés con fichas y el truco para
memorizar siguen enseñando la respuesta (son reels para estudiar y dan variedad): el piloto automático los alterna con
los de reto.

## Qué sale en cada reel
Sin mascota: tarjeta de test con la marca (teal + ámbar) y voz en off en español de España.
**Gancho → pregunta (la voz la lee y las palabras se iluminan) → cuenta atrás → respuesta correcta en verde →
explicación breve con su referencia → cierre con apruebatcae.com.** Formatos que rota el piloto automático:

| Formato | Qué es |
|---|---|
| `pregunta_del_dia` | Una pregunta del banco con su explicación |
| `examen_real` | Pregunta de los exámenes oficiales (15/03/2026 y 14/05/2026) con su fecha |
| `error_tipico` | Marca en rojo la opción trampa y explica por qué engaña |
| `truco_memorizar` | Pregunta + regla mnemotécnica sacada solo del material |
| `mito_realidad` | Afirmación, cuenta atrás y sello MITO / REALIDAD |
| `simulacro_3` | 3 preguntas cortas seguidas; "¿cuántas has acertado?" |
| `legislacion_30s` | 3 ideas clave de una norma + pregunta rápida |
| `caso_practico` | Escena de turno ilustrada ("Estás de turno en Medicina Interna…") que lleva a la pregunta |
| `flashcards_express` | 4 fichas de la app del mismo tema que se giran; "¿cuántas sabías?" |

### Series fijas (hueco de las 14:30)
Cada día tiene su cita, con número de capítulo en pantalla y el avance de mañana en la tarjeta final (motivo para seguir la cuenta):
lunes **legislación** · martes **trampas** · miércoles **simulacro** · jueves **casos prácticos** · viernes **mitos** ·
sábado **repaso exprés** · domingo **examen real**. El reel de las 21:30 lo elige el piloto automático.

### Estilos visuales
`clasico` (marca teal) · `cuaderno` (libreta con subrayador) · `examen` (hoja de respuestas con aspa de boli) ·
`noche` (estudiando de noche, neón) · `minimal` (editorial) · `ilustrado` (ilustración original de fondo).
El piloto automático los prueba y se queda con los que más guardan/comparten. Se puede forzar uno al lanzar el workflow.

## Estudio creativo: 10 agentes (estudio.py)
| Agente | Qué hace |
|---|---|
| Directora creativa | Concepto visual del reel e idea de la ilustración, sin repetir las recientes |
| Ilustradora | Genera la imagen ORIGINAL (Gemini) para el gancho, el caso práctico y el estilo ilustrado |
| Revisora visual | Rechaza imágenes con texto, errores de higiene/EPI, manos o caras deformes o algo sensible (1 redibujo) |
| Narradora de casos | Convierte la pregunta en una escena de turno, sin añadir datos |
| Memoria | "Guárdalo y repásalo mañana" + técnica de estudio en la descripción (más guardados) |
| Viralidad | Reto en pantalla durante la cuenta atrás ("¿Tu compi la acierta?"), línea para compartir y para etiquetar |
| Series | Nombre y número de la serie del día y avance real de mañana |
| Embudo a la app | Cierre con el número REAL de preguntas/fichas de ese tema en la app (se comprueba en código) |
| SEO | Título de YouTube y frase con lo que busca un opositor (TikTok/YouTube/Instagram) |
| Ritmo | Velocidad de voz y energía de la música según la retención real |

Se suman a la sala de 5 agentes (gancho, guion, diseño, crecimiento, comunidad) y cada uno tiene su cuaderno diario en
`agents/estudio_*.md`. Todo lo que escriben pasa por el verificador antes de publicarse. Las imágenes aprobadas se
guardan junto al vídeo (`*_ilustracion.jpg`) y el registro en `image_log.jsonl`.

## Chuleta visual diaria (carrusel, 18:00)
Además de los 2 reels, cada día a las 18:00 se publica una **chuleta**: carrusel de 6-8 imágenes estilo "apuntes
bonitos" en Instagram y en TikTok (modo foto). Workflow *Chuleta diaria* (`chuleta.py`).
- **Portada** con titular burbuja ("NO TE LÍES CON LAS LESIONES") + pegatina → **3-5 diapositivas** con los términos
  clave en tarjetas, palabras resaltadas con rotulador y un "TRUCO" → **¿Te atreves?** (una pregunta verificada del
  banco) → **Solución** + guárdala / envíasela / apruebatcae.com.
- Estilo propio de la marca (menta, teal y dorado, tipografías Fredoka y Nunito) y **pegatinas kawaii originales** de
  objetos y órganos generadas por IA (nunca personas; una segunda IA revisa que no tengan texto ni nada raro; si
  falla, se usa una pegatina dibujada en código).
- **Rigor:** todo sale solo de las fichas y preguntas de la app de ese tema y el verificador lo revisa frase a frase
  (incluida la descripción). Si no pasa, se reescribe una vez y, si no, se prueba otro tema; si nada pasa, ese día no hay
  chuleta. Solo temas sanitarios (no legislación). Rota por los 49 temas sanitarios sin repetir subtema
  (`chuletas.json`).
- **Probar:** *Actions → Chuleta diaria → Run workflow* con "Solo generar las imágenes" marcado y, si quieres, un tema
  (`upp`, `piel`, `constantesVitales`...). Las imágenes se descargan en *Artifacts*.
- **Apagar:** variable `CHULETA` = `false`. Coste de IA: 4 pegatinas + textos al día (unos céntimos).
- Las imágenes se alojan en Zernio para que Instagram las descargue (sin Zernio, en el propio repositorio público).

## Cuenta generalista (toda España)
Los textos, la voz, los hashtags y las descripciones hablan a opositores de TCAE de cualquier comunidad, sin nombrar
ninguna. **Primero salen todas las preguntas generales** (temario sanitario y legislación estatal); las del temario
específico de Aragón (SALUD, Estatuto, geografía, leyes aragonesas y cualquier pregunta que nombre Aragón) quedan **al
final de la cola** y solo se usan cuando ya no quedan generales sin publicar. El verificador (lunes y jueves) también revisa
antes las generales. Lista de temas en `questions.py` (`REGIONAL_TOPICS`).

## La voz solo dice el guion
Las pistas de interpretación son muy cortas y en inglés (nunca se mezclan con el texto en español), y cada toma se
transcribe: si la voz dice algo que no está en el guion ("tono amable, como si fueras una compañera..."), esa toma se
descarta y se graba otra. Las letras de las opciones se le pasan a la voz escritas como se dicen en español ("be,
Fowler"; "la correcta es la ce"), así nunca las lee en inglés aunque la opción sea un término inglés o latino; si aun
así dice "bi" o "si", la toma se repite. Lo mismo si **repite** algo (p. ej. lee dos veces la opción B) o dice palabras de más:
se comprueba cada toma al grabarla y otra vez cada frase del reel terminado; si una frase sigue mal, se vuelve a grabar
sola (hasta 4 veces) y, si aun así falla, ese reel no se publica (se pasa a otro formato). La solución solo dice la letra ("La correcta
es la B"): no vuelve a leer la opción, que ya se ve en verde. Además, cualquier campo del guion con indicaciones de tono o de voz se cambia por la
plantilla antes de grabar.

## Cómo se evita publicar un error (lo más importante)
1. **Solo preguntas propias**: el banco sale del `index.html` de tu web app (1.822 preguntas, 220 de examen oficial, 2.718 fichas). El enunciado y las opciones salen tal cual; la IA nunca los reescribe.
2. **Verificador** (`verifier.py`): antes de usar una pregunta comprueba que la respuesta marcada es la correcta y la única. En **legislación y plazos** exige una **cita literal** del texto real de la norma (`fuentes/`, descargado del BOE) y el código comprueba que esa cita existe de verdad; sin cita, esa pregunta no sale.
3. **Verificación del guion**: todo lo que escriben los agentes (explicación, trampa, truco, mito, puntos) se contrasta con la pregunta, la explicación de la app, las fichas y la cita. Si no pasa, se reescribe una vez; si sigue sin pasar, se cambia de formato.
4. Si no hay nada verificado, **ese día no se publica** (mejor no publicar que publicar un error).

El informe `banco/informe_verificacion.md` lista las preguntas dudosas y los posibles errores del banco; sirve también para corregir la web app.

## Puesta en marcha (una vez)
1. Crea un repositorio **privado** en GitHub y sube todo el contenido de esta carpeta.
2. **Settings → Secrets and variables → Actions → Secrets**:
   - `GEMINI_API_KEY` (obligatorio: guion, verificador, voz).
   - `IG_TOKEN`: token de **página** de Facebook (empieza por `EAA`) de la página vinculada a @apruebatcae (cuenta profesional), con `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`, `instagram_manage_insights`, `instagram_manage_comments`. Generado desde un token de usuario de larga duración, no caduca (igual que en StreakChess).
   - `ZERNIO_API_KEY`: conecta en Zernio la cuenta de TikTok @apruebatcae y el canal de YouTube (sin ella solo se publica en Instagram).
3. **Actions → Descargar fuentes → Run workflow.** Mira `fuentes/estado.md`. Tres normas solo están en el BOA (Decreto Legislativo 2/2004, Decreto 174/2010 y Decreto 39/2024): pega su texto en el archivo que indica. Mientras falten, las preguntas de esos temas no se publican.
4. **Actions → Verificar banco → Run workflow** (pon 200). Después se verifica una tanda los lunes y jueves de madrugada (si no queda nada pendiente, termina en segundos).
5. **Actions → Muestras de voz**: descarga las muestras, elige una y ponla en **Variables → `GEMINI_VOICE`** (por defecto `Sulafat`).
6. **Actions → Reels diarios → Run workflow** con "Solo generar el vídeo" marcado: descarga el vídeo en *Artifacts* y revísalo.
7. **Actions → Comprobar conexiones**: debe salir todo en verde (tokens, cuentas, Gemini, reserva de preguntas). Se repite cada lunes y, si algo crítico falla, GitHub te avisa por correo.
8. Desde ese momento publica solo a las 14:30 y 21:30. Para pausar: *Reels diarios → … → Disable workflow*.

## Minutos de GitHub (repositorio privado)
El plan gratuito incluye 2.000 min/mes. Estimación con esta versión: reels ~1.000-1.300 min/mes (2 al día, sin esperas
ni segundo render salvo diseño flojo), verificación ~100, comprobación semanal ~10 → **~1.100-1.400 min/mes**.
Cada prueba manual de *Reels diarios* gasta 15-25 min: márcala con "Solo generar el vídeo" y no abuses.
Ahorros aplicados: sin bot de comentarios; sin espera hasta la hora exacta; los crons de verano/invierno solo corren en
su temporada; el director de arte solo vuelve a renderizar si puntúa por debajo de 7,5 (`ART_RERENDER_BELOW`);
verificación 2 veces por semana y se salta si no queda nada; tope de 45 min por reel.

## Actualizar las preguntas
Sube la nueva versión de la web app a `webapp/index.html`: el workflow **Importar banco** la lee sola. Las preguntas ya verificadas o publicadas se recuerdan (cada una tiene un id estable).

## Voz
Por defecto, voz femenina de Gemini (`Sulafat`), grabada por bloques de una sola toma (pregunta + opciones,
solución + explicación) para que la entonación fluya como una persona real, con acento de España.
- **Elegir otra voz de Gemini**: *Actions → Muestras de voz* y pon la elegida en la variable `GEMINI_VOICE`.
- **La voz más humana (opcional, de pago)**: crea una cuenta en **elevenlabs.io**, elige en la *Voice Library* una voz
  femenina en español de España y copia su *Voice ID*. Guarda el secreto `ELEVENLABS_API_KEY` y la variable
  `ELEVENLABS_VOICE_ID`. Con eso se usa ElevenLabs y, si falla, Gemini. Para comparar varias, pon varias IDs separadas por
  comas en `ELEVENLABS_VOICE_IDS` y lanza *Muestras de voz*. Un reel son ~700-900 caracteres → ~50.000 al mes con 2 al día.

## Marca
Colores del CSS de apruebatcae.com (teal #1a9e8f, teal oscuro #0f7a6d, teal claro, dorado #e8c93d, verde y rojo de la
app). Estilo por defecto `marca` (claro, como la web) y la web en pequeño arriba en todos los fotogramas y stories.
La cifra que se anuncia ("más de 10.000 preguntas") se cambia con la variable `APP_PREGUNTAS`. "Comprobar conexiones"
avisa si esa cifra es mayor que el banco importado (sube el `index.html` actual a `webapp/`).

## Lo demás
- **Guardado sin choques**: todos los workflows guardan su estado con `sincronizar.py`, que descarga la última versión
  y FUSIONA verificaciones, preguntas usadas y registros antes de subir (aunque dos workflows terminen a la vez).
- **Aprendizaje**: `performance.json` (views, guardados, compartidos, comentarios, visitas al perfil), `strategy_report.md` (qué formato y gancho ganan), `playbook.md` (estratega semanal) y `agents/*.md` (cuadernos diarios de los 5 agentes).
- **Ubicación**: `locations.json` trae España y grandes ciudades; rellena el `id` (página de Facebook del lugar) de las que quieras usar. Vacío = sin ubicación.
- **Hechos de la app**: `assets/app/facts.md`. Los agentes solo afirman lo que pone ahí (edítalo si algo cambia, p. ej. si deja de ser gratis).
- **Portada**: el reel usa como portada el fotograma del gancho (`thumb_offset`).
- **Prueba local sin red**: `QUIZ_MOCK=1 VOICE_ENGINE=mock python make_quiz.py simulacro_3 out/prueba.mp4 cuaderno`.

### Control de la voz (cómo se decide si una toma vale)
Cada frase grabada se transcribe con Whisper y se compara con el texto: palabras de más, trozos repetidos, letras en
inglés o indicaciones leídas. Si algo falla, se confirma con una segunda transcripción más cuidadosa (para no tirar una
toma buena por un error del reconocedor) y solo entonces se graba de nuevo. En el registro del workflow verás
`voice: toma descartada (...) · texto ... · se oye ...` con lo que se oyó exactamente.
