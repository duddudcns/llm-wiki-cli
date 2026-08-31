# Empêcher les notes de s'obsolèter en silence

[English](../en/staleness.md) · [한국어](../ko/staleness.md) · [日本語](../ja/staleness.md) · [简体中文](../zh-Hans/staleness.md) · [Español](../es/staleness.md) · **Français**

Les notes les plus utiles sont celles qui disent comment les choses fonctionnent vraiment —
quel fichier appelle quelle fonction, dans quel ordre. Ce sont aussi les premières
à devenir fausses, parce que le code continue d'évoluer et la note ne bouge pas.

Le problème n'est pas qu'une note vieillit. C'est qu'une vieille note ressemble
exactement à une note récente, donc l'IA la lit, la croit, et prend une décision
en fonction d'informations qui ne sont plus justes depuis des semaines. C'est pire
que de ne pas avoir de note du tout.

`llmw` n'essaie pas de deviner quelles notes sont devenues obsolètes — voir
[Pourquoi ça ne se contente pas de vérifier le code](#pourquoi-ça-ne-se-contente-pas-de-vérifier-le-code)
à la fin. À la place, ça fait trois choses plus simples.

## 1. La recherche et la lecture vous montrent l'âge des affirmations d'une note

Les résultats affichent maintenant le titre de la note et quand elle a été mise à jour pour la dernière fois :

```
1. wiki/decisions/retry-budget.md
   title: Retry budget moves into the uploader (v0.1.18)
   updated: 2026-07-13 (49d ago)
   summary: ...
```

Si le fichier sur le disque est plus récent que la date que la note indique, vous verrez
les deux :

```
   updated: 2026-07-13 (49d ago, file modified 2026-08-31)
```

Cet écart signifie que quelqu'un a modifié le corps de la note et n'a pas mis à jour sa
date — donc la note peut décrire quelque chose de plus récent, ou de plus ancien, que ce qu'elle dit.
Afficher les deux nombres c'est fait exprès : en choisir un transformerait silencieusement « quand quelqu'un
a touché ce fichier pour la dernière fois » en « quand quelqu'un a vérifié pour la dernière fois que
c'était encore vrai », et ce ne sont pas du tout la même chose.

`llmw read <path> --full` est laissé tranquille — ça imprime la note et rien d'autre,
parce que ce texte exact est celui qui sera utilisé pour faire des modifications réfléchies.

## 2. Remplacer une vieille décision la marque en une seule étape

Quand une nouvelle note renverse une ancienne, écrivez-la avec `--supersedes` :

```bash
llmw write wiki/decisions/retry-in-the-uploader.md \
  --reason "the uploader owns retries now" \
  --supersedes wiki/decisions/retry-in-the-client.md --stdin
```

L'ancienne note est marquée `status: superseded` avec un pointeur vers la nouvelle,
et les recherches l'affichent juste à côté du chemin :

```
1. wiki/decisions/retry-in-the-client.md [superseded -> wiki/decisions/retry-in-the-uploader.md]
```

Les deux notes sont sauvegardées et enregistrées, et si la note que vous avez nommée n'existe pas,
rien n'est écrit du tout.

La raison pour laquelle c'est une seule commande au lieu de deux : écrire la nouvelle note est
la partie dont les gens se souviennent, et revenir marquer l'ancienne est la partie qu'ils oublient.
Une note toujours marquée « active » des mois après son remplacement est exactement ce qui crée
une mauvaise décision plus tard.

L'ancienne note garde son contenu. Une décision renversée explique quand même *pourquoi* elle
a été prise, et ce raisonnement survive généralement à la décision elle-même — donc les notes
remplacées sont marquées, non cachées ou reléguées plus bas dans les résultats.

## 3. Les notes peuvent dire quels fichiers elles décrivent

Ajoutez une liste `code:` aux métadonnées d'une note :

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

Ensuite, quand l'IA termine un tour pendant lequel elle a modifié un de ces fichiers,
le rappel de fin de tour nomme la note :

```
Source changed: record durable knowledge with `llmw write`/`edit`/`patch`...
Pages describing what changed: wiki/decisions/retry-budget.md
```

C'est la différence entre « pense à mettre à jour le wiki » et « cette note précise
parle du fichier que tu viens de modifier ». L'IA a encore le changement frais à l'esprit
à ce moment-là, ce qui est le seul moment où mettre à jour la note est facile.

Ces chemins sont relatifs à votre dossier de projet. Ce ne sont pas des liens — une
note qui liste `src/uploader.py` ne sera pas signalée comme ayant un lien cassé,
et `llmw lint` ne se plaindra pas.

## De petits rappels pendant que vous écrivez

`llmw write`, `edit` et `patch` affichent une courte note (dans le flux d'erreur,
pour qu'elle ne se mélange jamais avec une sortie que quelque chose d'autre lit) quand :

- une note manque des champs de métadonnées que votre projet requiert, ou
- vous avez modifié le corps d'une note mais laissé sa date `updated` telle quelle.

Aucun des deux n'arrête l'écriture. Ce sont des rappels, pas des règles — vous rectifiez
peut-être juste une faute de frappe, auquel cas il n'y a rien à reformuler. Le second
reste silencieux si la note a déjà été mise à jour aujourd'hui.

**`updated` n'est jamais changé pour vous.** Si ça l'était, rectifier une faute de frappe
ferait qu'une note obsolète paraisse fraîchement vérifiée — et une note qui paraît plus récente
qu'elle ne l'est provoque exactement la mauvaise décision que toute cette fonctionnalité existe
pour prévenir. Une note qui paraît *plus vieille* qu'elle ne l'est ne coûte qu'un coup d'œil
rapide au code. En cas de doute, l'affichage devrait vous faire faire confiance à une note moins,
pas plus.

## Pourquoi ça ne se contente pas de vérifier le code

L'idée évidente est de comparer chaque note à ses fichiers dans le contrôle de version et signaler
celles dont le code a changé plus récemment. Ça a été construit et mesuré sur le propre wiki
de ce projet, et ça ne fonctionne pas : **17 sur 24 notes ont été signalées**, presque toutes
par un seul refactoring qui a juste déplacé des imports et n'a rien changé au sens.

Réduire ça à des fonctions individuelles n'aide pas non plus — ce même refactoring a
vraiment édité l'intérieur des fonctions que les notes nommaient. La raison sousjacente est simple : un fichier qui change n'est pas une preuve qu'une phrase à son propos
est devenue fausse. Renommer les choses, diviser une fonction, ranger les imports — tout ça
déclenche la vérification, rien ne rend la note fausse.

Une vérification qui se trompe deux fois sur trois est ignorée, et une fois qu'elle est
ignorée c'est pire que rien, parce que ça donne l'impression que le wiki est supervisé alors
qu'il ne l'est pas. Donc `llmw` vous montre les dates et vous laisse juger, marque ce que
quelqu'un a explicitement dit être remplacé, et pointe les notes qui disent qu'elles parlent du
fichier que vous venez de toucher. Ces trois choses sont tout ce qu'il peut vraiment savoir.
