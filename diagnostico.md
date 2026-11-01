# Diagnóstico del guion


## pregunta_del_dia
Pregunta(s): Según el ciclo de Deming (PDCA), la fase en la que se comprueba si los resultados obtenido

### intento 1
guionista OK:
```json
{
 "screen_hook": "¿Superas esta pregunta oficial?",
 "hook_line": "Ponte a prueba con esta pregunta oficial de calidad asistencial.",
 "reveal_line": "La respuesta correcta es la C.",
 "explicacion": "En el ciclo de Deming, Check significa verificar. Es la fase donde compruebas si los resultados coinciden con lo planificado.",
 "cta_line": "Practica más preguntas oficiales totalmente gratis en apruebatcae.com, con el link en la bio.",
 "caption_hook": "¿Aciertas esta pregunta de examen de 2026? ⏱️",
 "comment_prompt": "Deja tu opción en comentarios: ¿A, B, C o D?",
 "cierre_line": "¿Cuántas has acertado? Comenta tu resultado, del cero al tres."
}
```
revisor: cambios {"screen_hook": "Pregunta oficial de examen", "hook_line": "Comprueba si dominas el ciclo Deming con esta pregunta real.", "cta_line": "Guarda el vídeo para repasar y haz más simulacros oficiales en apruebatcae.com.", "caption_hook": "¿Te acuerdas de esta fase del ciclo Deming? 📝", "comment_prompt": "Escribe tu respuesta en comentarios: ¿A, B, C o D?"}
estudio: añade {"cta_line": "Repasa el tema de calidad asistencial y practica sus 37 preguntas tipo test gratis en apruebatcae.com.", "save_line": "Guárdalo y compruébalo en 48 horas", "save_caption": "Guarda el reel y aplica la repetición espaciada: vuelve en 48 horas para comprobar si recuerdas la respuesta correcta.", "reto_line": "¿Tu compi de turno la sabe?", "share_line": "Pásasela a tu compañera de oposición.", "tag_caption": "Etiqueta a tu compi de oposición: si falla, le toca invitarte al café en el próximo turno.", "yt_title": "Simulacro Oposiciones TCAE: Pregunta oficial de Calidad Asistencial", "seo_line": "Practica este test de auxiliar de enfermería sobre calidad asistencial para preparar tus oposiciones TCAE 2026.", "voice_speed": 1.06, "music": "normal", "app_caption": "Tienes 37 preguntas tipo test de Calidad Asistencial para practicar a tu ritmo en apruebatcae.com."}
verificador: ok=False
```json
[
 {
  "campo": "cierre_line",
  "frase": "¿Cuántas has acertado? Comenta tu resultado, del cero al tres.",
  "motivo": "El reel es de formato 'pregunta_del_dia' y solo muestra una única pregunta. Pedir al usuario que comente su resultado 'del cero al tres' es incoherente y no se ajusta al contenido del vídeo."
 }
]
```

### intento 2
guionista OK:
```json
{
 "screen_hook": "¿Superas esta pregunta oficial?",
 "hook_line": "Pregunta de examen oficial de 2026: ¿la aciertas sin dudar?",
 "reveal_line": "La opción correcta es la C.",
 "explicacion": "En el ciclo PDCA, la fase Check comprueba los resultados con los objetivos previstos. Es la respuesta oficial de la plantilla provisional del tribunal.",
 "cta_line": "Practica miles de preguntas de examen gratis en apruebatcae.com. Enlace en la bio.",
 "caption_hook": "¿Aciertas esta pregunta oficial de examen de 2026? 📝",
 "comment_prompt": "Comenta A, B, C o D antes de ver la solución.",
 "cierre_line": "¿Cuántas has acertado? Comenta tu resultado, del cero al tres."
}
```
revisor: cambios {"screen_hook": "Cayó en examen oficial", "hook_line": "¿Sabes qué fase del ciclo de Deming comprueba los resultados? Respóndela.", "cta_line": "Guarda el reel para repasar Calidad y entrena más test en apruebatcae.com.", "caption_hook": "Pregunta oficial de Calidad: ¿recuerdas las fases de Deming? 📋", "comment_prompt": "Deja tu letra en comentarios antes de ver la solución."}
estudio: añade {"cta_line": "Repasa las preguntas de calidad asistencial y haz simulacros completos gratis entrando ahora en apruebatcae.com.", "save_line": "Guárdalo y repásalo en 48 horas", "save_caption": "Guarda el reel y aplica la repetición espaciada: comprueba en dos días si recuerdas la respuesta sin mirar los comentarios.", "reto_line": "¿La aciertas antes que tu compi?", "share_line": "Pásasela a tu compañera de turno.", "tag_caption": "Etiqueta a tu compi: si falla esta de examen, le tocan los cambios posturales del turno.", "yt_title": "Simulacro TCAE: Pregunta oficial de examen de Calidad Asistencial", "seo_line": "Practica este test de auxiliar de enfermería con una pregunta oficial de calidad asistencial para tus oposiciones TCAE.", "voice_speed": 1.06, "music": "normal", "app_caption": "Practica las 37 preguntas tipo test de Calidad Asistencial y revisa tus fallos gratis en apruebatcae.com."}
verificador: ok=False
```json
[
 {
  "campo": "cierre_line",
  "frase": "¿Cuántas has acertado? Comenta tu resultado, del cero al tres.",
  "motivo": "El formato del reel es 'pregunta_del_dia', lo que implica que solo se hace una pregunta. Pedir a los usuarios que comenten su resultado 'del cero al tres' es incoherente porque no hay tres preguntas en el vídeo."
 }
]
```

## error_tipico
Pregunta(s): La contención mecánica en el ámbito de la salud mental debe considerarse:

### intento 1
guionista OK:
```json
{
 "screen_hook": "¿Caes en esta pregunta oficial?",
 "hook_line": "Ponte a prueba con este fallo clásico de salud mental en la oposición.",
 "reveal_line": "La respuesta correcta es la B.",
 "explicacion": "La contención mecánica es una medida de último recurso, que debe estar siempre pautada, justificada clínicamente y supervisada de forma continua, agotando antes otras alternativas menos restrictivas.",
 "cta_line": "Sigue practicando miles de preguntas oficiales gratis en apruebatcae.com, tienes el enlace en la bio.",
 "caption_hook": "¿Sabrías responder a esta pregunta de salud mental? 🧠",
 "comment_prompt": "Deja tu opción en comentarios: ¿A, B, C o D?",
 "cierre_line": "¿Cuántas has acertado? Comenta tu resultado, del cero al tres.",
 "trampa_porque": "La A tienta ante la agitación, pero la contención mecánica nunca es la primera opción: es el último recurso tras agotar alternativas menos restrictivas, siempre pautada y justificada clínicamente.",
 "trampa": "A"
}
```
revisor: cambios {"screen_hook": "Pregunta oficial con trampa", "hook_line": "Muchos opositores dudan con esta pregunta de salud mental en el examen.", "cta_line": "Guarda el vídeo para repasar y practica más preguntas oficiales en apruebatcae.com.", "caption_hook": "Muchos fallan esta pregunta oficial sobre contención mecánica. 🧠", "comment_prompt": "Escribe solo tu opción: ¿A, B, C o D?"}
estudio: añade {"cta_line": "Continúa practicando el tema de salud mental gratis con test y flashcards en apruebatcae.com.", "save_line": "Guárdalo y repásalo en 48 horas", "save_caption": "Guarda el reel y aplica la repetición espaciada: vuelve en 48 horas para comprobar si recuerdas la respuesta sin dudar.", "reto_line": "¿La aciertas antes que tu compi?", "share_line": "Compártelo con tu compi de planta.", "tag_caption": "Menciona a tu compi de opo: si duda con esta pregunta, le tocan los cambios posturales.", "yt_title": "Test TCAE Oposiciones: Pregunta oficial con trampa de Salud Mental", "seo_line": "Practica este test auxiliar de enfermería sobre salud mental para preparar tus oposiciones TCAE 2026 con preguntas de examen real.", "voice_speed": 1.06, "music": "normal", "app_caption": "Tienes 20 preguntas tipo test y 41 flashcards de Salud Mental para practicar gratis en apruebatcae.com."}
verificador: ok=False
```json
[
 {
  "campo": "hook_line",
  "frase": "Muchos opositores dudan con esta pregunta de salud mental en el examen.",
  "motivo": "Afirma que la pregunta aparece 'en el examen', asumiendo que es una pregunta real de oposición, dato no proporcionado en el material de referencia."
 },
 {
  "campo": "screen_hook",
  "frase": "Pregunta oficial con trampa",
  "motivo": "El material de referencia no indica en ningún momento que sea una pregunta 'oficial'."
 },
 {
  "campo": "caption_hook",
  "frase": "Muchos fallan esta pregunta oficial sobre contención mecánica. 🧠",
  "motivo": "Se vuelve a catalogar como 'pregunta oficial', un dato inventado que no está respaldado por el material."
 },
 {
  "campo": "seo_line",
  "frase": "Practica este test auxiliar de enfermería sobre salud mental para preparar tus oposiciones TCAE 2026 con preguntas de examen real.",
  "motivo": "Se inventa el año '2026' y la afirmación de que son 'preguntas de examen real', datos totalmente ausentes en la referencia."
 },
 {
  "campo": "yt_title",
  "frase": "Test TCAE Oposiciones: Pregunta oficial con trampa de Salud Mental",
  "motivo": "Incluye el término 'Pregunta oficial', el cual no está respaldado por el material."
 },
 {
  "campo": "cierre_line",
  "frase": "¿Cuántas has acertado? Comenta tu resultado, del cero al tres.",
  "motivo": "Incoherencia lógica: el reel solo contiene una pregunta, por lo que pedir un resultado 'del cero al tres' es un error."
 }
]
```

### intento 2
guionista OK:
```json
{
 "screen_hook": "¿Superas este error típico?",
 "hook_line": "Ponte a prueba con esta pregunta de salud mental: ¿aciertas a la primera?",
 "reveal_line": "La respuesta correcta es la B.",
 "explicacion": "La contención mecánica es una medida de último recurso, que debe estar siempre pautada, justificada clínicamente y supervisada de forma continua, agotando antes otras alternativas menos restrictivas.",
 "cta_line": "Sigue practicando miles de test gratis en apruebatcae.com. Tienes el enlace en la bio.",
 "caption_hook": "¿Sabes cómo actuar ante una contención mecánica? Ponte a prueba. 🧠",
 "comment_prompt": "Deja tu respuesta en comentarios antes de ver la solución.",
 "cierre_line": "¿Cuántas has acertado? Comenta tu resultado, del cero al tres.",
 "trampa_porque": "Muchos eligen la A por precipitación. Pero la contención es de último recurso. Requiere justificación clínica, supervisión continua y agotar otras alternativas.",
 "trampa": "A"
}
```
revisor: cambios {"screen_hook": "Error típico de examen oficial", "hook_line": "Muchos opositores fallan aquí: ¿qué consideración tiene la contención mecánica?", "cta_line": "Guarda este vídeo para repasar y practica miles de test en apruebatcae.com.", "caption_hook": "Pregunta trampa de Salud Mental: ¿aciertas o caes en el error? 🧠", "comment_prompt": "¿Cuál eliges tú: A, B, C o D? Déjala abajo."}
estudio: añade {"cta_line": "Practica este tema de Salud Mental gratis con preguntas y flashcards entrando ahora en apruebatcae.com.", "save_line": "Guárdalo y repásalo en 48 horas", "save_caption": "Aplica la repetición espaciada: guarda el reel y vuelve en 48 horas para comprobar si recuerdas la respuesta sin mirar.", "reto_line": "¿Tu compi de turno la sabría?", "share_line": "Pásasela a quien oposita contigo.", "tag_caption": "Menciona a tu compi: si duda con esta pregunta, le toca el café del próximo turno.", "yt_title": "Simulacro Oposiciones TCAE: Error típico de examen oficial en Salud Mental", "seo_line": "Repasa este test de auxiliar de enfermería sobre salud mental para preparar tus oposiciones TCAE 2026.", "voice_speed": 1.06, "music": "normal", "app_caption": "Repasa Salud Mental con 20 preguntas tipo test y 41 flashcards gratis en apruebatcae.com."}
verificador: ok=False
```json
[
 {
  "campo": "screen_hook",
  "frase": "Error típico de examen oficial",
  "motivo": "El material de referencia no indica en ningún momento que esta pregunta provenga de un examen oficial."
 },
 {
  "campo": "seo_line",
  "frase": "Repasa este test de auxiliar de enfermería sobre salud mental para preparar tus oposiciones TCAE 2026.",
  "motivo": "Se incluye el año '2026', una fecha que no aparece en el material de referencia y supone un dato inventado."
 },
 {
  "campo": "yt_title",
  "frase": "Simulacro Oposiciones TCAE: Error típico de examen oficial en Salud Mental",
  "motivo": "Vuelve a afirmar que es una pregunta de 'examen oficial', un dato que no está respaldado por el material."
 },
 {
  "campo": "cierre_line",
  "frase": "¿Cuántas has acertado? Comenta tu resultado, del cero al tres.",
  "motivo": "Es incoherente y menciona una cifra errónea: el reel solo expone una pregunta, por lo que pedir un resultado 'del cero al tres' no tiene sentido."
 }
]
```

## mito_realidad
Pregunta(s): Para trasladar a un paciente de cama a silla de ruedas que colabora, se necesita:

### intento 1
guionista OK:
```json
{
 "screen_hook": "Reto de examen: ¿mito o realidad?",
 "hook_line": "¿Te atreves a resolver esta afirmación típica de examen sin fallar?",
 "reveal_line": "Es una auténtica realidad.",
 "explicacion": "Si el paciente colabora, basta una persona. Coloca la silla paralela a los pies de la cama, incorpóralo y gíralo para sentarlo.",
 "cta_line": "Practica cientos de preguntas de movilizaciones gratis en apruebatcae.com. Tienes el link en la bio.",
 "caption_hook": "¿Mito o realidad en el traslado del paciente? 🦽",
 "comment_prompt": "Escribe MITO o REALIDAD en comentarios antes de ver la solución 👇",
 "cierre_line": "¿Cuántas has acertado? Comenta tu resultado, del cero al tres.",
 "afirmacion": "Para trasladar de la cama a la silla de ruedas a un paciente que colabora, basta una persona.",
 "veredicto": "REALIDAD"
}
```
revisor: cambios {"screen_hook": "Pregunta oficial: traslado del paciente", "hook_line": "¿Mito o realidad? Atenta a lo que se necesita si el paciente colabora.", "cta_line": "Guarda este vídeo para repasar movilizaciones y haz más tests en apruebatcae.com.", "caption_hook": "Pregunta oficial de movilización: ¿mito o realidad con paciente colaborador? 🦽", "comment_prompt": "Comenta MITO o REALIDAD antes de que termine el tiempo 👇"}
estudio: añade {"cta_line": "Sigue practicando las posiciones y movilizaciones con las preguntas de este tema gratis en apruebatcae.com.", "save_line": "Guarda y repasa en 48 horas", "save_caption": "Aplica la repetición espaciada: guarda este vídeo y vuelve a autoevaluarte en 48 horas sin mirar la solución.", "reto_line": "¿Tu compi de turno la acierta?", "share_line": "Envíalo a tu compi de planta.", "tag_caption": "Menciona a tu compañera de oposición: si falla, hoy le tocan a ella los cambios posturales.", "yt_title": "Simulacro TCAE: Pregunta oficial de movilización de pacientes", "seo_line": "Repasa con este test de auxiliar de enfermería para las oposiciones TCAE 2026 sobre movilización de pacientes.", "voice_speed": 1.06, "music": "normal", "app_caption": "Tienes 25 preguntas tipo test y 38 flashcards de Posiciones y Movilizaciones disponibles gratis en apruebatcae.com."}
verificador: ok=False
```json
[
 {
  "campo": "seo_line",
  "frase": "Repasa con este test de auxiliar de enfermería para las oposiciones TCAE 2026 sobre movilización de pacientes.",
  "motivo": "Menciona el año '2026', una fecha/cifra que no aparece en el material de referencia."
 },
 {
  "campo": "cierre_line",
  "frase": "¿Cuántas has acertado? Comenta tu resultado, del cero al tres.",
  "motivo": "Menciona una puntuación 'del cero al tres', lo cual es incoherente porque el guion solo plantea una única afirmación de Mito o Realidad, no tres."
 }
]
```

### intento 2
guionista OK:
```json
{
 "screen_hook": "¿Aciertas este reto de examen?",
 "hook_line": "Ponte a prueba con este caso clásico de examen de TCAE.",
 "reveal_line": "Esto es un mito.",
 "explicacion": "Si el paciente colabora, basta con una sola persona para realizar el traslado a la silla de forma segura. Se necesitan dos cuando no colabora.",
 "cta_line": "Practica cientos de preguntas de movilizaciones gratis en apruebatcae.com. Tienes el link en la bio.",
 "caption_hook": "Pon a prueba tu temario con este reto de movilizaciones 👇",
 "comment_prompt": "¿Mito o realidad? Escribe tu respuesta antes de la solución.",
 "cierre_line": "¿Cuántas has acertado? Comenta tu resultado, del cero al tres.",
 "afirmacion": "Para pasar a silla de ruedas a un paciente que colabora se necesitan dos personas.",
 "veredicto": "MITO"
}
```
revisor: cambios {"screen_hook": "Pregunta trampa de examen oficial", "hook_line": "¿Cuántos profesionales necesitas para este traslado si el paciente colabora?", "cta_line": "Guarda el vídeo para repasar y haz más simulacros oficiales en apruebatcae.com.", "caption_hook": "Pregunta clásica de movilizaciones que suele generar dudas en examen 👇", "comment_prompt": "¿Mito o realidad? Deja tu respuesta abajo."}
estudio: añade {"cta_line": "Repasa el tema de posiciones y movilizaciones gratis con test y flashcards en apruebatcae.com.", "save_line": "Guárdalo y repásalo en 48 horas", "save_caption": "Guarda este reel y aplica repetición espaciada: vuelve en dos días a comprobar si recuerdas la técnica sin dudar.", "reto_line": "¿Tu compi de planta la acierta?", "share_line": "Pásasela a tu compi de turno.", "tag_caption": "Menciona a tu compañera: si falla esta pregunta trampa, le tocan los cambios posturales del turno.", "yt_title": "Simulacro TCAE: Pregunta trampa de examen oficial sobre movilizaciones", "seo_line": "Practica este test de auxiliar de enfermería para oposiciones TCAE 2026 con preguntas de movilización de pacientes.", "voice_speed": 1.06, "music": "normal", "app_caption": "Domina posiciones y movilizaciones: tienes 25 preguntas tipo test y 38 flashcards disponibles gratis en apruebatcae.com."}
verificador: ok=False
```json
[
 {
  "campo": "screen_hook",
  "frase": "Pregunta trampa de examen oficial",
  "motivo": "El material de referencia no indica en ningún momento que esta pregunta provenga de un examen oficial."
 },
 {
  "campo": "caption_hook",
  "frase": "Pregunta clásica de movilizaciones que suele generar dudas en examen 👇",
  "motivo": "Se inventa que es una pregunta 'clásica' y que 'suele generar dudas', afirmaciones estadísticas/de comportamiento que no están en el material de referencia."
 },
 {
  "campo": "seo_line",
  "frase": "Practica este test de auxiliar de enfermería para oposiciones TCAE 2026 con preguntas de movilización de pacientes.",
  "motivo": "Se incluye el año '2026', una fecha inventada que no aparece en el material de referencia."
 },
 {
  "campo": "yt_title",
  "frase": "Simulacro TCAE: Pregunta trampa de examen oficial sobre movilizaciones",
  "motivo": "Vuelve a catalogar la pregunta como de 'examen oficial', dato no respaldado por el texto de referencia."
 },
 {
  "campo": "cierre_line",
  "frase": "¿Cuántas has acertado? Comenta tu resultado, del cero al tres.",
  "motivo": "Menciona una puntuación 'del cero al tres', lo cual es incoherente porque en el reel solo se expone una única pregunta/mito."
 }
]
```

## caso_practico
Pregunta(s): ¿Cuál es el objetivo principal de la teoría de Virginia Henderson?

### intento 1
guionista OK:
```json
{
 "screen_hook": "¿Superas esta pregunta de turno?",
 "hook_line": "¿Sabes responder a esta pregunta clave sobre modelos de enfermería?",
 "reveal_line": "La opción correcta es la A.",
 "explicacion": "El modelo de Henderson se basa en la suplencia y ayuda. Su objetivo final es recuperar o mantener la independencia para cubrir sus 14 necesidades básicas.",
 "cta_line": "Practica cientos de preguntas de examen gratis en apruebatcae.com. Tienes el link en la bio.",
 "caption_hook": "¿Conoces el objetivo del modelo de Virginia Henderson? 🏥",
 "comment_prompt": "Escribe tu respuesta en comentarios antes de ver la solución.",
 "cierre_line": "¿Cuántas has acertado? Comenta tu resultado, del cero al tres.",
 "escena": "Estás en el pase de turno de la planta. Tu supervisora repasa el plan de cuidados y te pregunta por Virginia Henderson.",
 "escena_visual": "Una auxiliar de enfermería con pijama sanitario escucha el pase de guardia en el control de enfermería del hospital."
}
```
revisor: cambios {"screen_hook": "Pregunta oficial: Virginia Henderson", "hook_line": "Comprueba si dominas el objetivo principal de este modelo de enfermería.", "cta_line": "Guarda este caso para repasar y haz más simulacros en apruebatcae.com.", "caption_hook": "Pregunta fija de examen: ¿dominas a Virginia Henderson? 📝", "comment_prompt": "¿Dudas entre dos? Deja tu letra en comentarios."}
estudio: añade {"cta_line": "Si quieres afianzar Henderson y Maslow, entra gratis en apruebatcae.com y practica las preguntas de este tema.", "escena": "Estás de turno de mañana en medicina interna organizando los aseos. La enfermera revisa las necesidades del plan de cuidados contigo y te pregunta qué meta busca principalmente el modelo de Virginia Henderson.", "escena_visual": "Plano medio en el control de enfermería de una planta hospitalaria iluminada por la luz matinal. Dos sanitarias con pijama blanco conversan junto al carro de curas y una carpeta de registros.", "save_line": "Guárdalo y repásalo en 48 horas", "save_caption": "Aplica la repetición espaciada: guarda el reel y vuelve en 48 horas para comprobar si recuerdas la solución sin mirar.", "reto_line": "¿Tu compi de planta la sabe?", "share_line": "Compártelo con tu compi de oposición.", "tag_caption": "Etiqueta a tu compañera de oposición: si falla esta oficial, le tocan los cambios posturales del turno.", "yt_title": "Simulacro Oposiciones TCAE: Pregunta oficial de Virginia Henderson", "seo_line": "Practica este test de auxiliar de enfermería para oposiciones TCAE 2026 sobre el modelo de Virginia Henderson.", "voice_speed": 1.05, "
verificador: ok=False
```json
[
 {
  "campo": "screen_hook",
  "frase": "Pregunta oficial: Virginia Henderson",
  "motivo": "El material de referencia no indica en ningún momento que esta sea una pregunta 'oficial' de un examen real."
 },
 {
  "campo": "caption_hook",
  "frase": "Pregunta fija de examen: ¿dominas a Virginia Henderson? 📝",
  "motivo": "Incumple la regla de no prometer cosas. Afirmar que es una 'pregunta fija de examen' equivale a prometer que 'esto cae seguro'."
 },
 {
  "campo": "tag_caption",
  "frase": "Etiqueta a tu compañera de oposición: si falla esta oficial, le tocan los cambios posturales del turno.",
  "motivo": "Vuelve a catalogar la pregunta como 'oficial', un dato que no está respaldado por el material de referencia."
 },
 {
  "campo": "seo_line",
  "frase": "Practica este test de auxiliar de enfermería para oposiciones TCAE 2026 sobre el modelo de Virginia Henderson.",
  "motivo": "Introduce una fecha (2026) que no aparece en el material de referencia."
 },
 {
  "campo": "yt_title",
  "frase": "Simulacro Oposiciones TCAE: Pregunta oficial de Virginia Henderson",
  "motivo": "Afirma nuevamente que es una 'pregunta oficial', dato que no consta en el material."
 },
 {
  "campo": "cierre_line",
  "frase": "¿Cuántas has acertado? Comenta tu resultado, del cero al tres.",
  "motivo": "Es incoherente con el contenido. El reel solo presenta una pregunta, por lo que no tiene sentido pedir un resultado 'del cero al tres'."
 }
]
```

### intento 2
guionista OK:
```json
{
 "screen_hook": "¿Aciertas este caso de turno?",
 "hook_line": "Demuestra tu criterio de auxiliar resolviendo esta duda en pleno pase de planta.",
 "reveal_line": "La respuesta correcta es la A.",
 "explicacion": "El modelo de suplencia y ayuda busca que la persona recupere o mantenga su independencia para satisfacer por sí misma sus 14 necesidades básicas sin precisar ayuda externa.",
 "cta_line": "Sigue entrenando preguntas tipo test de tu temario gratis en apruebatcae punto com, link en la bio.",
 "caption_hook": "¿Recuerdas el objetivo principal de Virginia Henderson? Compruébalo aquí 📋",
 "comment_prompt": "Comenta tu opción: ¿A, B, C o D?",
 "cierre_line": "¿Cuántas has acertado? Comenta tu resultado, del cero al tres.",
 "escena": "Estás en el turno de mañana revisando el plan de cuidados. Tu compañera te pregunta por la meta final de Virginia Henderson al atender a vuestro paciente.",
 "escena_visual": "Dos auxiliares de enfermería con pijama sanitario revisan juntas una carpeta de cuidados en el mostrador del control de planta."
}
```
revisor: cambios {"screen_hook": "Caso oficial: Virginia Henderson", "hook_line": "Te cae en el examen: ¿cuál es el objetivo de este modelo?", "cta_line": "Guarda este vídeo para repasar y haz más simulacros en apruebatcae.com.", "caption_hook": "Virginia Henderson nunca falla en la oposición. ¿Aciertas el objetivo? 📝", "comment_prompt": "Escribe tu respuesta rápida: ¿A, B, C o D?"}
estudio: añade {"cta_line": "Practica gratis el tema de Henderson y Maslow con test oficiales explicados entrando ahora en apruebatcae.com.", "escena": "Estás de turno de mañana en la planta de hospitalización preparando el carro de aseo. Tu compañera de equipo te pregunta cuál es el objetivo principal según el modelo de Virginia Henderson.", "escena_visual": "Dos auxiliares de enfermería con uniforme sanitario conversan de pie junto a un carro de aseo y toallas en el pasillo luminoso de una planta de hospital, con puertas de habitaciones al fondo.", "save_line": "Guárdalo y repásalo en 48 horas", "save_caption": "Aplica repetición espaciada: guarda este caso y vuelve en 48 horas para comprobar si recuerdas la clave sin mirar.", "reto_line": "¿Tu compi de planta la acierta?", "share_line": "Compártelo con tu compi de turno.", "tag_caption": "Etiqueta a tu compañera de oposición: si falla, hoy le tocan los cambios posturales.", "yt_title": "Simulacro TCAE: Caso oficial de examen de Virginia Henderson", "seo_line": "Resuelve este test de auxiliar de enfermería sobre Virginia Henderson y prepara tus oposiciones TCAE 2026 con preguntas oficiales.", "voice_speed": 1.05, "music": "normal", "app_caption
verificador: ok=False
```json
[
 {
  "campo": "hook_line",
  "frase": "Te cae en el examen: ¿cuál es el objetivo de este modelo?",
  "motivo": "Incumple la regla de no prometer cosas ('esto cae seguro'). No se puede garantizar que caerá en el examen."
 },
 {
  "campo": "caption_hook",
  "frase": "Virginia Henderson nunca falla en la oposición. ¿Aciertas el objetivo? 📝",
  "motivo": "Vuelve a incumplir la regla de no hacer promesas al afirmar que 'nunca falla en la oposición'."
 },
 {
  "campo": "seo_line",
  "frase": "Resuelve este test de auxiliar de enfermería sobre Virginia Henderson y prepara tus oposiciones TCAE 2026 con preguntas oficiales.",
  "motivo": "Introduce datos inventados que no están en el material de referencia: el año '2026' y la etiqueta de 'preguntas oficiales'."
 },
 {
  "campo": "yt_title",
  "frase": "Simulacro TCAE: Caso oficial de examen de Virginia Henderson",
  "motivo": "Afirma que es un 'caso oficial de examen', un dato que no está respaldado por el material de referencia."
 },
 {
  "campo": "cierre_line",
  "frase": "¿Cuántas has acertado? Comenta tu resultado, del cero al tres.",
  "motivo": "Es incoherente. Pide una puntuación 'del cero al tres' cuando en el guion solo se plantea una única pregunta."
 }
]
```
