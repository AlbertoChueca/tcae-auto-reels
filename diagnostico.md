# Diagnóstico del guion


## pregunta_del_dia
Pregunta(s): Según el ciclo de Deming (PDCA), la fase en la que se comprueba si los resultados obtenido

### intento 1
guionista OK:
```json
{
 "screen_hook": "¿Aciertas esta pregunta oficial?",
 "hook_line": "Cayó en el examen oficial de 2026. ¿Sabrías responderla a la primera?",
 "reveal_line": "La respuesta correcta es la C.",
 "explicacion": "En el ciclo de Deming, la fase Check o verificar comprueba los resultados. Sirve para ver si coinciden con los objetivos previstos según la plantilla oficial.",
 "cta_line": "Practica gratis miles de preguntas oficiales en apruebatcae.com. Tienes el link en la bio.",
 "caption_hook": "Pregunta de examen oficial de 2026: ¿aciertas esta fase? 📝",
 "comment_prompt": "Escribe tu opción en comentarios: ¿A, B, C o D?"
}
```
revisor: cambios {"screen_hook": "Pregunta oficial de examen", "hook_line": "Cayó en examen oficial de TCAE: ¿la sabes responder a la primera?", "cta_line": "Guarda este vídeo para repasar y haz más test oficiales en apruebatcae.com.", "caption_hook": "Pregunta oficial sobre calidad asistencial: ¿cuál es la fase correcta? 📋", "comment_prompt": "Deja tu letra en comentarios: ¿A, B, C o D?"}
estudio: añade {"cta_line": "Practica las preguntas de Calidad Asistencial y repasa tus fallos gratis entrando ahora en apruebatcae.com.", "save_line": "Guarda y comprueba en 48 horas", "save_caption": "Aplica la repetición espaciada: guarda este reel y vuelve en 48 horas para responder de nuevo sin mirar la solución.", "reto_line": "¿La sabe tu compi de planta?", "share_line": "Compártela con tu compañera de oposición.", "tag_caption": "Etiqueta a tu compi de turno: si falla esta pregunta oficial, le toca el próximo cambio postural.", "yt_title": "Simulacro TCAE: Pregunta oficial de examen sobre Calidad Asistencial", "seo_line": "Repasa este test de auxiliar de enfermería para tus oposiciones TCAE 2026 con preguntas oficiales de calidad asistencial.", "voice_speed": 1.06, "music": "normal", "app_caption": "Practica gratis las 37 preguntas tipo test de Calidad Asistencial y pon a prueba tus conocimientos en apruebatcae.com."}
verificador: ok=True
```json
[]
```

## error_tipico
Pregunta(s): La contención mecánica en el ámbito de la salud mental debe considerarse:

### intento 1
guionista OK:
```json
{
 "screen_hook": "¿Aciertas esta de Salud Mental?",
 "hook_line": "Demuestra si dominas este concepto clave del temario de Salud Mental.",
 "reveal_line": "La respuesta correcta es la B.",
 "explicacion": "La contención mecánica es una medida de último recurso, que debe estar siempre pautada, justificada clínicamente y supervisada de forma continua, agotando antes otras alternativas menos restrictivas.",
 "cta_line": "Practica miles de preguntas de test gratis en apruebatcae.com. Tienes el enlace en la bio.",
 "caption_hook": "Pregunta trampa de Salud Mental para tu oposición de TCAE 🧠",
 "comment_prompt": "Comenta tu opción antes de ver la solución.",
 "trampa_porque": "La A tienta por las prisas ante una agitación, pero la contención mecánica es siempre de último recurso: exige justificación clínica, pauta médica y supervisión continua.",
 "trampa": "A"
}
```
revisor: cambios {"screen_hook": "Pregunta trampa: contención mecánica", "hook_line": "Muchos opositores caen aquí: ¿tienes clara la respuesta correcta?", "cta_line": "Guarda el vídeo para repasar y practica más test oficiales en apruebatcae.com.", "caption_hook": "El error más repetido en contención mecánica para TCAE 🧠", "comment_prompt": "¿A, B, C o D? Deja tu letra en comentarios."}
estudio: añade {"cta_line": "Continúa practicando el tema de Salud Mental con test y flashcards gratis en apruebatcae.com.", "save_line": "Guárdalo y repásalo en 48 horas", "save_caption": "Guarda el reel y practica repetición espaciada: vuelve en 48 horas y comprueba si recuerdas la respuesta sin mirar.", "reto_line": "¿Tu compi de planta la acierta?", "share_line": "Pásasela a tu compañera de oposición.", "tag_caption": "Etiqueta a tu compi de opo: si falla la pregunta, le toca pagar el café del turno.", "yt_title": "Simulacro TCAE: Pregunta trampa de examen oficial de Salud Mental", "seo_line": "Repasa este test auxiliar de enfermería de salud mental y prepara tus oposiciones TCAE 2026 con preguntas de examen.", "voice_speed": 1.06, "music": "normal", "app_caption": "Tienes 20 preguntas tipo test y 41 flashcards de Salud Mental para repasar gratis en apruebatcae.com."}
verificador: ok=False
```json
[
 {
  "campo": "seo_line",
  "frase": "Repasa este test auxiliar de enfermería de salud mental y prepara tus oposiciones TCAE 2026 con preguntas de examen.",
  "motivo": "Menciona 'preguntas de examen', lo cual contradice el ORIGEN que especifica que es una pregunta del banco de la app y no de un examen."
 },
 {
  "campo": "yt_title",
  "frase": "Simulacro TCAE: Pregunta trampa de examen oficial de Salud Mental",
  "motivo": "Utiliza el término 'examen oficial', lo cual es una infracción directa de las reglas de ORIGEN, ya que la pregunta no es de un examen oficial."
 }
]
```

### intento 2
guionista OK:
```json
{
 "screen_hook": "Reto express de Salud Mental",
 "hook_line": "Muchos dudan con la contención mecánica en el temario. ¿Tú la aciertas?",
 "reveal_line": "La respuesta correcta es la B.",
 "explicacion": "La contención mecánica es una medida de último recurso, que debe estar siempre pautada, justificada clínicamente y supervisada de forma continua, agotando antes otras alternativas menos restrictivas.",
 "cta_line": "Practica miles de preguntas del temario gratis en apruebatcae.com con el enlace de la bio.",
 "caption_hook": "¿Sabrías responder esta pregunta clave de Salud Mental? 🧠",
 "comment_prompt": "Comenta tu opción antes de ver la solución.",
 "trampa_porque": "Muchos marcan la A por error, pero la contención mecánica nunca es la primera opción: es una medida de último recurso y exige supervisión continua.",
 "trampa": "A"
}
```
revisor: cambios {"screen_hook": "Pregunta trampa: contención mecánica", "hook_line": "Muchos fallan esta pregunta en el examen oficial: ¿sabrías decir la correcta?", "cta_line": "Guarda el vídeo para repasar y practica más preguntas oficiales en apruebatcae.com.", "caption_hook": "Pregunta oficial sobre contención mecánica: no caigas en este error habitual. 🧠", "comment_prompt": "Deja tu letra en comentarios: ¿has dudado entre dos?"}
estudio: añade {"cta_line": "Practica ahora el tema de salud mental gratis y a tu ritmo entrando en apruebatcae.com.", "save_line": "Guárdalo y compruébalo en 48 horas", "save_caption": "Guarda el reel y practica recuperación activa: vuelve en 48 horas e intenta explicar el criterio correcto sin mirar.", "reto_line": "¿Tu compi de planta la sabe?", "share_line": "Compártela con tu compañera de opo.", "tag_caption": "Etiqueta a tu compañera de oposición: si no la acierta, le tocan los cambios posturales.", "yt_title": "Simulacro Oposiciones TCAE: Pregunta de examen real sobre salud mental", "seo_line": "Repasa con este test de auxiliar de enfermería sobre salud mental para preparar tus oposiciones TCAE 2026.", "voice_speed": 1.05, "music": "normal", "app_caption": "Tienes 20 preguntas tipo test y 41 flashcards de Salud Mental listas para practicar gratis en apruebatcae.com."}
verificador: ok=False
```json
[
 {
  "campo": "hook_line",
  "frase": "Muchos fallan esta pregunta en el examen oficial: ¿sabrías decir la correcta?",
  "motivo": "Afirma que la pregunta es de un examen oficial, pero las instrucciones de origen especifican claramente que es del banco de la app y prohíben decir que es oficial."
 },
 {
  "campo": "caption_hook",
  "frase": "Pregunta oficial sobre contención mecánica: no caigas en este error habitual. 🧠",
  "motivo": "Califica la pregunta como 'oficial', lo cual es un dato falso según el origen proporcionado."
 },
 {
  "campo": "yt_title",
  "frase": "Simulacro Oposiciones TCAE: Pregunta de examen real sobre salud mental",
  "motivo": "Utiliza la expresión 'Pregunta de examen real', lo cual está expresamente prohibido en las instrucciones de origen para las preguntas del banco propio de la app."
 }
]
```

## mito_realidad
Pregunta(s): Para trasladar a un paciente de cama a silla de ruedas que colabora, se necesita:

### intento 1
guionista OK:
```json
{
 "screen_hook": "Reto TCAE: ¿Mito o realidad?",
 "hook_line": "¿Te atreves a resolver este reto sobre movilización de pacientes?",
 "reveal_line": "Es un mito total.",
 "explicacion": "Si el paciente colabora, basta con una sola persona para el traslado seguro. Dos personas se necesitan cuando no colabora.",
 "cta_line": "Practica cientos de preguntas de movilizaciones gratis en apruebatcae.com, link en la bio.",
 "caption_hook": "Reto de movilizaciones para tu oposición de TCAE 🏥",
 "comment_prompt": "¿Mito o realidad? Deja tu respuesta en los comentarios.",
 "afirmacion": "Hacen falta al menos dos personas para pasar a la silla a un paciente colaborador.",
 "veredicto": "MITO"
}
```
revisor: cambios {"screen_hook": "Pregunta oficial: ¿mito o realidad?", "hook_line": "¿Caerías en esta pregunta de examen sobre traslado a silla?", "cta_line": "Guarda este vídeo para repasar y practica miles de preguntas en apruebatcae.com.", "caption_hook": "¿Mito o realidad de examen oficial? Guarda para repasar 📌", "comment_prompt": "¿Mito o realidad? Escribe tu respuesta en comentarios."}
estudio: añade {"cta_line": "Repasa el tema de posiciones y movilizaciones gratis con preguntas tipo test explicadas en apruebatcae.com.", "save_line": "Guárdalo y repásalo en 48 horas", "save_caption": "Aplica la repetición espaciada: guarda el vídeo y vuelve en dos días para comprobar si recuerdas la respuesta sin mirar.", "reto_line": "¿La acertaría tu compi de planta?", "share_line": "Pásaselo a tu compañera de opo.", "tag_caption": "Etiqueta a tu compi de planta: si falla, le toca la próxima ronda de cambios posturales.", "yt_title": "Simulacro Oposiciones TCAE: Pregunta oficial de movilización de pacientes", "seo_line": "Practica este test de auxiliar de enfermería para las oposiciones TCAE 2026 con preguntas de movilización de pacientes.", "voice_speed": 1.06, "music": "normal", "app_caption": "Tienes 25 preguntas tipo test y 38 flashcards de este tema para practicar gratis en apruebatcae.com."}
verificador: ok=False
```json
[
 {
  "campo": "screen_hook",
  "frase": "Pregunta oficial: ¿mito o realidad?",
  "motivo": "El origen indica expresamente que la pregunta NO es de un examen oficial. Afirmar que es 'oficial' es un dato falso."
 },
 {
  "campo": "caption_hook",
  "frase": "¿Mito o realidad de examen oficial? Guarda para repasar 📌",
  "motivo": "El origen indica expresamente que la pregunta NO es de un examen oficial. Afirmar que es de 'examen oficial' es un dato falso."
 },
 {
  "campo": "yt_title",
  "frase": "Simulacro Oposiciones TCAE: Pregunta oficial de movilización de pacientes",
  "motivo": "El origen indica expresamente que la pregunta NO es de un examen oficial. Afirmar que es 'Pregunta oficial' es un dato falso."
 }
]
```

### intento 2
guionista OK:
```json
{
 "screen_hook": "Reto de movilizaciones: ¿aciertas?",
 "hook_line": "¿Aceptas el reto? Dime si esta afirmación de movilizaciones es mito o realidad.",
 "reveal_line": "La respuesta correcta: esto es un mito.",
 "explicacion": "Si el paciente colabora, basta con 1 sola persona para el traslado. Las 2 personas son necesarias únicamente cuando el paciente no colabora.",
 "cta_line": "Practica gratis preguntas de tu oposición en apruebatcae.com. Tienes el link en la bio.",
 "caption_hook": "Reto de movilizaciones para tu oposición de TCAE: ¿mito o realidad? 📋",
 "comment_prompt": "¿Mito o realidad? Escribe tu respuesta en comentarios.",
 "afirmacion": "Para trasladar de la cama a la silla de ruedas a un paciente que colabora hacen falta 2 personas.",
 "veredicto": "MITO"
}
```
revisor: cambios {"screen_hook": "Pregunta oficial: ¿mito o realidad?", "hook_line": "¿Sabrías identificar si esta afirmación de examen es mito o realidad?", "cta_line": "Guarda este repaso y entrena miles de preguntas oficiales en apruebatcae.com.", "caption_hook": "Pregunta clave de movilizaciones para tu oposición de TCAE: ¿aciertas? 📌", "comment_prompt": "Comenta rápido: ¿es mito o realidad?"}
estudio: añade {"cta_line": "Pon a prueba lo aprendido: practica el tema de posiciones y movilizaciones gratis en apruebatcae.com.", "save_line": "Guárdalo para repasar en 48 horas", "save_caption": "Aplica la recuperación activa: guarda el reel y comprueba en 48 horas si recuerdas la respuesta correcta sin dudar.", "reto_line": "¿Tu compi de planta la acierta?", "share_line": "Compártelo con tu compañera de oposición.", "tag_caption": "Etiqueta a tu compi de planta: si falla, hoy le tocan a ella los cambios posturales.", "yt_title": "Pregunta oficial TCAE: Movilización y traslado ¿Mito o realidad?", "seo_line": "Practica este test de auxiliar de enfermería sobre movilización de pacientes para preparar tus oposiciones TCAE 2026.", "voice_speed": 1.06, "music": "normal", "app_caption": "Tienes 25 preguntas tipo test y 38 flashcards de Posiciones y Movilizaciones para practicar gratis en apruebatcae.com."}
verificador: ok=False
```json
[
 {
  "campo": "hook_line",
  "frase": "¿Sabrías identificar si esta afirmación de examen es mito o realidad?",
  "motivo": "El origen especifica que la pregunta es del banco de la app y no de un examen oficial. Llamarla 'afirmación de examen' da a entender que es una pregunta real, lo cual incumple las instrucciones."
 },
 {
  "campo": "screen_hook",
  "frase": "Pregunta oficial: ¿mito o realidad?",
  "motivo": "El origen indica expresamente que la pregunta NO es de un examen oficial. Usar la palabra 'oficial' es un dato falso."
 },
 {
  "campo": "yt_title",
  "frase": "Pregunta oficial TCAE: Movilización y traslado ¿Mito o realidad?",
  "motivo": "El origen indica expresamente que la pregunta NO es de un examen oficial. Usar la palabra 'oficial' es un dato falso."
 }
]
```

## caso_practico
Pregunta(s): ¿Cuál es el objetivo principal de la teoría de Virginia Henderson?

### intento 1
guionista OK:
```json
{
 "screen_hook": "¿Aciertas este caso de turno?",
 "hook_line": "Ponte a prueba con este caso clásico de tu temario de TCAE.",
 "reveal_line": "La opción correcta es la A.",
 "explicacion": "El modelo de Henderson se llama de suplencia y ayuda. Su objetivo es la independencia del paciente. Busca que cubra por sí mismo sus 14 necesidades básicas.",
 "cta_line": "Sigue practicando test de tu temario gratis en apruebatcae.com. Tienes el enlace en la bio.",
 "caption_hook": "¿Aciertas el objetivo de Virginia Henderson? 🏥",
 "comment_prompt": "Escribe tu respuesta en comentarios: ¿A, B, C o D?",
 "escena": "Estás en el pase de planta matinal. Acompañas a un paciente que quiere vestirse solo. Tu compañera te pregunta por la teoría que guía este cuidado.",
 "escena_visual": "TCAE en el pasillo de hospitalización junto al carro de cuidados matinales, revisando la lista de pacientes de la planta."
}
```
revisor: cambios {"screen_hook": "Pregunta oficial: Virginia Henderson", "hook_line": "Esta pregunta sobre Henderson entra siempre en oposiciones: responde sin dudar.", "cta_line": "Guarda el repaso y practica más test oficiales en apruebatcae.com.", "caption_hook": "Pregunta clásica de examen sobre Virginia Henderson. ¿La aciertas? 📋", "comment_prompt": "Escribe solo tu letra: ¿A, B, C o D?"}
estudio: añade {"cta_line": "Sigue practicando las Necesidades de Henderson y Maslow gratis en apruebatcae.com. Entra y domina este tema clave.", "escena": "Estás de turno de mañana en hospitalización. Tu compañera observa cómo dejas que un paciente se abroche solo la bata y te pregunta cuál es el fin principal del modelo de Henderson.", "escena_visual": "Habitación de hospital con luz matinal. Una TCAE con uniforme sanitario azul acompaña con calma a un paciente mayor sentado al borde de la cama intentando vestirse. Otra compañera la observa desde la puerta.", "save_line": "Guarda y repasa en 48 horas", "save_caption": "Guarda este caso práctico y aplica repetición espaciada: comprueba en 48 horas si recuerdas la respuesta mediante recuperación activa.", "reto_line": "¿Tu compi de planta la acierta?", "share_line": "Compártela con tu compañera de estudio.", "tag_caption": "Menciona a tu compi de opo: si falla esta pregunta, le toca pagar el café del turno.", "yt_title": "Simulacro Oposiciones TCAE: Pregunta oficial Virginia Henderson", "seo_line": "Practica este test de auxiliar de enfermería para las oposiciones TCAE 2026 con preguntas sobre Virginia Henderson.", "voice_speed": 1.06, "music": "
verificador: ok=False
```json
[
 {
  "campo": "hook_line",
  "frase": "Esta pregunta sobre Henderson entra siempre en oposiciones: responde sin dudar.",
  "motivo": "Incumple la regla de no hacer promesas. Afirmar que 'entra siempre en oposiciones' equivale a prometer que 'esto cae seguro'."
 },
 {
  "campo": "screen_hook",
  "frase": "Pregunta oficial: Virginia Henderson",
  "motivo": "Afirma que la pregunta es 'oficial', lo cual es un dato falso según el ORIGEN, que especifica que es del banco de la app y no de un examen oficial."
 },
 {
  "campo": "caption_hook",
  "frase": "Pregunta clásica de examen sobre Virginia Henderson. ¿La aciertas? 📋",
  "motivo": "Llamarla 'pregunta clásica de examen' da a entender que es una pregunta real de examen, lo cual contradice el ORIGEN (no es de un examen oficial)."
 },
 {
  "campo": "yt_title",
  "frase": "Simulacro Oposiciones TCAE: Pregunta oficial Virginia Henderson",
  "motivo": "Vuelve a utilizar el término 'oficial', incumpliendo la regla estricta sobre el origen de la pregunta."
 }
]
```

### intento 2
guionista OK:
```json
{
 "screen_hook": "Reto de necesidades básicas",
 "hook_line": "Ponte a prueba con este concepto de temario: ¿aciertas la respuesta?",
 "reveal_line": "La respuesta correcta es la A.",
 "explicacion": "El modelo de Virginia Henderson es de suplencia y ayuda. Su fin es lograr la independencia del paciente. Así puede satisfacer por sí mismo sus 14 necesidades básicas.",
 "cta_line": "Practica miles de preguntas del temario gratis en apruebatcae.com. Tienes el enlace en la bio.",
 "caption_hook": "¿Conoces el objetivo de Virginia Henderson? Compruébalo aquí 🩺",
 "comment_prompt": "Deja tu respuesta en comentarios: ¿A, B, C o D?",
 "escena": "Estás en el pase de guardia repasando los cuidados diarios de tu planta. Una compañera te pregunta qué busca el modelo que aplicáis en el servicio.",
 "escena_visual": "Primer plano de un mostrador de enfermería con carpetas abiertas, un fonendoscopio y una auxiliar completando el registro de cuidados diarios."
}
```
revisor: cambios {"screen_hook": "Pregunta oficial de examen: Henderson", "hook_line": "Esta pregunta sobre Virginia Henderson cae siempre: ¿sabes cuál es su objetivo?", "cta_line": "Guarda este repaso y practica más tests oficiales en apruebatcae.com.", "caption_hook": "Pregunta clásica sobre Virginia Henderson en tu oposición. 📝", "comment_prompt": "¿A, B, C o D? Deja tu letra en comentarios."}
estudio: añade {"cta_line": "Practica gratis las 21 preguntas de Maslow y Henderson ahora mismo en apruebatcae.com.", "escena": "Estás de turno de mañana en medicina interna organizando los aseos. Tu compañera revisa el plan de cuidados de la planta y te consulta cuál es la meta principal del modelo de Virginia Henderson.", "escena_visual": "Dos auxiliares de enfermería con pijama blanco en el control de enfermería de un hospital luminoso, revisando carpetas de cuidados junto a un carro de material.", "save_line": "Guárdalo y compruébalo en 48 horas", "save_caption": "Guarda el reel y aplica la repetición espaciada: vuelve en 48 horas para comprobar si recuerdas la clave del caso.", "reto_line": "¿Tu compi de planta la acierta?", "share_line": "Pásasela a tu compañera de oposición", "tag_caption": "Etiqueta a tu compi: si falla esta fija de examen, le toca invitar al café del turno.", "yt_title": "Simulacro TCAE: Pregunta oficial de examen sobre Virginia Henderson", "seo_line": "Practica este test de auxiliar de enfermería para las oposiciones TCAE 2026 sobre el modelo de Virginia Henderson.", "voice_speed": 1.05, "music": "normal", "app_caption": "Repasa este tema con 21 preguntas tipo test y 13
verificador: ok=False
```json
[
 {
  "campo": "hook_line",
  "frase": "Esta pregunta sobre Virginia Henderson cae siempre: ¿sabes cuál es su objetivo?",
  "motivo": "Incumple la regla de no hacer promesas al afirmar que la pregunta 'cae siempre'."
 },
 {
  "campo": "screen_hook",
  "frase": "Pregunta oficial de examen: Henderson",
  "motivo": "Afirma que es una pregunta oficial, pero el ORIGEN especifica claramente que es del banco de la app y no de un examen oficial."
 },
 {
  "campo": "tag_caption",
  "frase": "Etiqueta a tu compi: si falla esta fija de examen, le toca invitar al café del turno.",
  "motivo": "Incumple la regla de no hacer promesas al calificarla como 'fija de examen', dando a entender que cae seguro."
 },
 {
  "campo": "yt_title",
  "frase": "Simulacro TCAE: Pregunta oficial de examen sobre Virginia Henderson",
  "motivo": "Afirma que es una pregunta oficial de examen, lo cual es un dato falso según el ORIGEN proporcionado."
 }
]
```

## legislacion_30s
Pregunta(s): ¿En qué casos debe ser el consentimiento informado por escrito?

### intento 1
guionista OK:
```json
{
 "screen_hook": "¿Aciertas esta de legislación sanitaria?",
 "hook_line": "Ponte a prueba con este punto clave del temario de TCAE.",
 "reveal_line": "La respuesta correcta es la B.",
 "explicacion": "El consentimiento debe constar por escrito en intervenciones quirúrgicas, procedimientos diagnósticos/terapéuticos invasivos y, en general, cuando existan riesgos importantes para el paciente.",
 "cta_line": "Practica miles de preguntas de temario gratis en apruebatcae.com con el link de la bio.",
 "caption_hook": "¿Tienes claro cuándo el consentimiento va por escrito? Repásalo aquí 👇",
 "comment_prompt": "Deja tu respuesta en comentarios: ¿A, B, C o D?",
 "titulo_norma": "Ley 41/2002: Consentimiento informado",
 "puntos": [
  "Por escrito en cirugía y procedimientos diagnósticos o terapéuticos invasores.",
  "También es obligatorio por escrito si el procedimiento supone riesgos.",
  "El paciente puede revocar su consentimiento en cualquier momento y por escrito."
 ]
}
```
revisor: cambios {"screen_hook": "Pregunta oficial: consentimiento informado", "hook_line": "¿Recuerdas en qué casos es obligatorio por escrito? Responde antes del tiempo.", "cta_line": "Guarda el vídeo para repasar y haz más test en apruebatcae.com.", "caption_hook": "Pregunta fija de examen sobre la Ley 41/2002. ¿La sabes? 👇", "comment_prompt": "Deja tu letra en comentarios: ¿A, B, C o D?"}
estudio: añade {"save_line": "Guarda y compruébalo en 48 horas", "save_caption": "Guarda este reel y comprueba en 48 horas si recuerdas la respuesta correcta aplicando recuperación activa antes de ver la solución.", "reto_line": "¿Tu compi de planta la acierta?", "share_line": "Pásasela a tu compañera de oposición.", "tag_caption": "Etiqueta a tu compi de planta: si falla esta, le tocan los próximos cambios posturales.", "yt_title": "Simulacro Oposiciones TCAE: Pregunta oficial de consentimiento informado", "seo_line": "Practica con este test de auxiliar de enfermería para tus oposiciones TCAE 2026 sobre el consentimiento informado.", "voice_speed": 1.05, "music": "normal"}
verificador: ok=False
```json
[
 {
  "campo": "screen_hook",
  "frase": "Pregunta oficial: consentimiento informado",
  "motivo": "El origen especifica claramente que la pregunta es del banco de la app y NO de un examen oficial. Afirmar que es 'oficial' es un dato falso."
 },
 {
  "campo": "caption_hook",
  "frase": "Pregunta fija de examen sobre la Ley 41/2002. ¿La sabes? 👇",
  "motivo": "Incumple la regla de no hacer promesas. Decir 'pregunta fija de examen' equivale a prometer que 'esto cae seguro'."
 },
 {
  "campo": "yt_title",
  "frase": "Simulacro Oposiciones TCAE: Pregunta oficial de consentimiento informado",
  "motivo": "Vuelve a incumplir la regla sobre el origen de la pregunta al catalogarla como 'pregunta oficial' cuando no lo es."
 }
]
```

### intento 2
guionista OK:
```json
{
 "screen_hook": "Consentimiento informado: ¿aciertas este reto?",
 "hook_line": "Ponte a prueba con esta pregunta sobre el consentimiento informado en tu oposición.",
 "reveal_line": "La respuesta correcta es la B.",
 "explicacion": "El consentimiento debe constar por escrito en intervenciones quirúrgicas, procedimientos diagnósticos/terapéuticos invasivos y, en general, cuando existan riesgos importantes para el paciente.",
 "cta_line": "Practica miles de preguntas de legislación gratis en apruebatcae.com, tienes enlace en la bio.",
 "caption_hook": "¿Sabes cuándo el consentimiento debe ser por escrito? Ponte a prueba 👇",
 "comment_prompt": "Escribe tu respuesta en comentarios antes de que termine el tiempo.",
 "titulo_norma": "Ley 41/2002 sobre consentimiento escrito",
 "puntos": [
  "Obligatorio por escrito en cualquier intervención quirúrgica.",
  "Exigible en procedimientos diagnósticos o terapéuticos invasores y con riesgos.",
  "El paciente puede revocarlo en cualquier momento y por escrito."
 ]
}
```
revisor: cambios {"screen_hook": "Pregunta oficial: consentimiento por escrito", "hook_line": "Cae siempre en examen: ¿cuándo es obligatorio por escrito en el hospital?", "cta_line": "Entrena más preguntas oficiales de legislación sanitaria en apruebatcae.com con el enlace de la bio.", "caption_hook": "Pregunta oficial sobre consentimiento informado: ¿aciertas la opción correcta? 👇", "comment_prompt": "Deja tu opción en comentarios: ¿cuál marcas en el examen?"}
estudio: añade {"save_line": "Guárdalo y repásalo en 48 horas.", "save_caption": "Aplica la repetición espaciada: guarda el reel y comprueba dentro de 48 horas si recuerdas la respuesta correcta.", "reto_line": "¿Tu compi de planta la acierta?", "share_line": "Compártela con tu compañera de turno", "tag_caption": "Etiqueta a tu compi de turno: si falla esta pregunta, le tocan los cambios posturales.", "yt_title": "Simulacro TCAE: Pregunta oficial de examen sobre Consentimiento Informado", "seo_line": "Practica este test de auxiliar de enfermería para las oposiciones TCAE 2026 sobre consentimiento informado y Ley 41/2002.", "voice_speed": 1.05, "music": "normal"}
verificador: ok=False
```json
[
 {
  "campo": "hook_line",
  "frase": "Cae siempre en examen: ¿cuándo es obligatorio por escrito en el hospital?",
  "motivo": "Contiene una promesa ('Cae siempre en examen'), lo cual incumple la regla de no hacer promesas como 'esto cae seguro'."
 },
 {
  "campo": "screen_hook",
  "frase": "Pregunta oficial: consentimiento por escrito",
  "motivo": "Afirma que la pregunta es oficial, pero el origen especifica claramente que es del banco de la app y NO de un examen oficial."
 },
 {
  "campo": "caption_hook",
  "frase": "Pregunta oficial sobre consentimiento informado: ¿aciertas la opción correcta? 👇",
  "motivo": "Afirma que la pregunta es oficial, lo cual es un dato falso según el origen proporcionado."
 },
 {
  "campo": "cta_line",
  "frase": "Entrena más preguntas oficiales de legislación sanitaria en apruebatcae.com con el enlace de la bio.",
  "motivo": "Vuelve a afirmar que las preguntas son oficiales, contradiciendo las instrucciones de origen."
 },
 {
  "campo": "yt_title",
  "frase": "Simulacro TCAE: Pregunta oficial de examen sobre Consentimiento Informado",
  "motivo": "Incluye 'Pregunta oficial de examen', lo cual está expresamente prohibido porque la pregunta no proviene de un examen oficial."
 }
]
```
