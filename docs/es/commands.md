# Detalles de comandos

[English](../en/commands.md) · [한국어](../ko/commands.md) · [日本語](../ja/commands.md) · [简体中文](../zh-Hans/commands.md) · **Español** · [Français](../fr/commands.md)

Ver la tabla de referencia de comandos del README para la lista completa de comandos y
sus banderas. Esta página cubre las partes demasiado profundas para una entrada de tabla de una línea.

## Semántica de búsqueda

`llmw search` nunca requiere fraseología solo con palabras clave — una consulta de lenguaje natural completo
está bien. Intenta hasta tres niveles, solo moviéndose al siguiente
cuando el anterior no encuentra nada, así que una coincidencia completa nunca puede
ser superada por una parcial:

1. **strict** — cada término de consulta requerido (AND).
2. **relaxed** — términos que no pueden coincidir con ninguna página indexada en absoluto (errores tipográficos,
   conjugaciones verbales) se descartan; el resto todavía se requieren.
3. **any** — cada término se vuelve opcional (OR), clasificado por relevancia.

La salida `--json` reporta qué nivel respondió la consulta:
`{"mode": "strict"|"relaxed"|"any", "dropped_tokens": [...], "results": [...]}`.
Pasa `--strict` para desactivar los niveles de fallback y solo ejecutar nivel 1.

Los términos de consulta que son una sola palabra Hangul con una partícula final (una 조사
— p. ej. `스탯창을`, `포탈에서`) se reducen a la sustancia desnuda (`스탯창`, `포탈`)
antes de coincidir, ya que la búsqueda de prefijo de SQLite FTS5 solo coincide con una consulta
que es un prefijo de la palabra indexada, no al revés, así que una
consulta flexionada de otra manera echaría de menos una página de sustantivo desnudo. Esta es una
lista de sufijos curada pequeña, no un analizador morfológico completo — no reducirá
conjugaciones verbales (eso es para lo que es el nivel relajado) y ocasionalmente
eliminará una terminación coincidental no-partícula (p. ej. `도로` → `도`); esto es
siempre seguro para recall (el tallo es un prefijo de la palabra original) en el peor de los casos
agregando ruido de clasificación menor, nunca una página faltante.
