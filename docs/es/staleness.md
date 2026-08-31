# Cómo evitar que las notas se queden obsoletas sin que nadie lo note

[English](../en/staleness.md) · [한국어](../ko/staleness.md) · [日本語](../ja/staleness.md) · [简体中文](../zh-Hans/staleness.md) · **Español** · [Français](../fr/staleness.md)

Las notas más útiles son las que dicen cómo funciona algo realmente —
qué archivo llama a qué función, en qué orden. Pero son también las
primeras notas que dejan de ser correctas, porque el código sigue
cambiando y la nota no.

El problema no es que una nota envejezca. Es que una nota vieja se ve
exactamente igual que una fresca, así que la IA la lee, la cree, y toma
una decisión basándose en información que dejó de ser verdadera hace
semanas. Eso es peor que no tener nota alguna.

`llmw` no intenta adivinar cuáles notas están obsoletas — mira
[Por qué no solo revisa el código](#por-qué-no-solo-revisa-el-código)
al final. En cambio, hace tres cosas más simples.

## 1. Buscar y leer te dicen qué tan vieja es la información de una nota

Los resultados ahora muestran el título de la nota y cuándo se actualizó
por última vez:

```
1. wiki/decisions/retry-budget.md
   title: Retry budget moves into the uploader (v0.1.18)
   updated: 2026-07-13 (49d ago)
   summary: ...
```

Si `llmw` ha visto que el cuerpo de la nota cambió después de la fecha que
la nota dice, verás ambas:

```
   updated: 2026-07-13 (49d ago, body changed 2026-08-31)
```

Esa diferencia significa que alguien reescribió lo que la nota dice y no
actualizó su fecha — así que la nota podría describir algo más nuevo, o
más viejo, de lo que dice. Mostrar ambos números es deliberado: elegir uno
convertiría silenciosamente "cuándo alguien cambió esto por última vez"
en "cuándo alguien verificó que esto seguía siendo verdad", y esas no son
la misma cosa.

**El cuerpo, no el archivo.** Marcar una nota como reemplazada, agregar una
lista `code:`, o arreglar una etiqueta reescribe el archivo sin cambiar una
sola palabra de lo que la nota dice — y se te dice que *no* toques la fecha
para eso. Una versión anterior de esto comparaba timestamps del archivo, y
un ciclo de mantenimiento en el wiki de este proyecto dejó una advertencia
permanente "esto cambió" en 21 de sus 31 notas, ninguna de las cuales lo
había hecho. Una advertencia que casi siempre está equivocada es una que
dejas de leer.

`llmw read <path> --full` se deja solo — imprime la nota y nada más,
porque ese texto exacto es lo que se usa para hacer ediciones cuidadosas.

## 2. Reemplazar una decisión vieja la marca, en un paso

Cuando una nota nueva reemplaza una más antigua, escríbela con `--supersedes`:

```bash
llmw write wiki/decisions/retry-in-the-uploader.md \
  --reason "the uploader owns retries now" \
  --supersedes wiki/decisions/retry-in-the-client.md --stdin
```

La nota vieja se marca `status: superseded` con un puntero a la nueva,
y las búsquedas la muestran junto al camino:

```
1. wiki/decisions/retry-in-the-client.md [superseded -> wiki/decisions/retry-in-the-uploader.md]
```

Ambas notas quedan en la copia de seguridad y en el registro, y si la nota
que nombraste no existe, nada se escribe en absoluto.

La razón de que sea un comando en lugar de dos: escribir la nota nueva es
la parte que la gente recuerda, e ir atrás a marcar la vieja es la parte
que olvida. Una nota que sigue marcada "activa" meses después de ser
revertida es exactamente lo que causa una decisión equivocada después.

La nota vieja guarda su cuerpo. Una decisión revertida aún explica *por qué*
fue tomada, y ese razonamiento generalmente sobrevive a la decisión misma
— así que las notas reemplazadas se marcan, no se ocultan ni bajan en los
resultados.

## 3. Las notas pueden decir qué archivos describen

Agrega una lista `code:` al frontmatter de una nota:

```yaml
---
title: Retry budget moves into the uploader
type: decision
status: active
created: 2026-08-31
updated: 2026-08-31
code:
  - src/uploader.py
  - src/retry.py
---
```

Entonces, cuando la IA termina un turno en el que editó uno de esos
archivos, el recordatorio de fin de turno nombra la nota:

```
Source changed: record durable knowledge with `llmw write`/`edit`/`patch`...
Pages describing what changed: wiki/decisions/retry-budget.md
```

Esta es la diferencia entre "acuérdate de actualizar la wiki" y "esta nota
específica habla del archivo que acabas de cambiar." La IA sigue teniendo
el cambio fresco en la mente en ese momento, que es la única vez que
actualizar la nota es barato.

Estos caminos son relativos a tu carpeta de proyecto. No son enlaces — una
nota que liste `src/uploader.py` no se reportará como teniendo un enlace
roto, y `llmw lint` no se quejará sobre ellos.

## Recordatorios pequeños mientras escribes

`llmw write`, `edit` y `patch` imprimen una nota breve (al flujo de error,
así nunca se mezcla en la salida que otra cosa está leyendo) cuando:

- a una nota le faltan campos de frontmatter que tu proyecto requiere, o
- cambiaste el cuerpo de una nota pero dejaste su fecha `updated` igual.

Ninguno de los dos detiene la escritura. Son recordatorios, no reglas —
bien podrías estar arreglando una falta de ortografía, en cuyo caso no hay
nada que reafirmar. El segundo se queda callado si la nota ya se actualizó
hoy.

**`updated` nunca se cambia por ti.** Si lo fuera, arreglar una falta de
ortografía haría que una nota obsoleta parezca verificada recientemente —
y una nota que parece más fresca de lo que es causa exactamente la
decisión equivocada para la que existe esta característica. Una nota que
parece *más vieja* de lo que es solo te cuesta una mirada rápida al código.
Cuando tengas dudas, el display debería hacerte confiar menos en una nota,
no más.

## Por qué no solo revisa el código

La idea obvia es comparar cada nota contra sus archivos en control de
versiones y marcar aquellas cuyo código cambió más recientemente. Eso fue
construido y medido en la propia wiki de este proyecto, y no funciona: **17
de 24 notas fueron marcadas**, casi todas por un único refactor que movió
algunos imports alrededor y cambió el significado de nada.

Achicarlo a funciones individuales tampoco ayuda — ese mismo refactor
genuinamente editó los interiores de las funciones que las notas nombraban.
La razón subyacente es simple: un archivo que cambia no es evidencia de que
una oración sobre él se hizo falsa. Renombrar cosas, dividir una función,
limpiar imports — todos disparan el chequeo, ninguno hace que una nota
esté equivocada.

Un chequeo que está equivocado dos de cada tres veces se ignora, y una vez
que se ignora es peor que nada, porque hace que la wiki parezca supervisada
cuando no lo está. Así que `llmw` te muestra las fechas y te deja juzgar,
marca lo que alguien explícitamente dijo que fue reemplazado, y apunta a
las notas que dicen que hablan sobre el archivo que acabas de tocar. Los
tres son cosas que realmente puede saber.
