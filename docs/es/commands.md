# Cómo funciona la búsqueda

[English](../en/commands.md) · [한국어](../ko/commands.md) · [日本語](../ja/commands.md) · [简体中文](../zh-Hans/commands.md) · **Español** · [Français](../fr/commands.md)

Mira la tabla de comandos del README para ver la lista completa. Esta
página solo explica con más detalle una cosa: cómo decide `llmw search`
qué cuenta como una coincidencia.

## La búsqueda prueba tres formas, de la más estricta a la más flexible

Puedes escribir una búsqueda igual que harías una pregunta — frases
completas están bien, no necesitas adivinar palabras clave especiales.
Por detrás, prueba hasta tres formas de buscar, y solo pasa a la siguiente
si la anterior no encontró absolutamente nada — así una nota que coincide
exactamente con tu búsqueda nunca queda por debajo de una nota que apenas
coincide un poco:

1. **Estricta** — cada palabra de tu búsqueda tiene que aparecer en algún
   lugar de la nota.
2. **Flexible** — las palabras que no aparecen en ninguna nota (por un
   error de tipeo, o por estar en una forma ligeramente distinta) se
   descartan sin avisar; el resto de las palabras todavía tienen que
   coincidir.
3. **Cualquier coincidencia** — cada palabra pasa a ser opcional, y los
   resultados simplemente se ordenan según qué tan bien coinciden.

Si pides la salida en formato `--json`, te dice cuál de las tres formas
encontró el resultado: `{"mode": "strict"|"relaxed"|"any", "dropped_tokens": [...], "results": [...]}`.
Agrega `--strict` si solo quieres que use la primera forma, la más
estricta.

Para texto en coreano: a una palabra de búsqueda que es un solo sustantivo
coreano con una pequeña terminación gramatical pegada (como `스탯창을` o
`포탈에서`) se le recorta esa terminación antes de buscar (queda como
`스탯창`, `포탈`), para que igual pueda encontrar una nota que use el
sustantivo solo, sin la terminación. Esto solo cubre una lista pequeña y
común de terminaciones, no todas las formas posibles de cada palabra —
está pensado para que nunca se le escape una nota, solo para que a veces
ordene los resultados un poco distinto de lo esperado.
