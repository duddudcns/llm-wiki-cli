# Comment fonctionne la recherche

[English](../en/commands.md) · [한국어](../ko/commands.md) · [日本語](../ja/commands.md) · [简体中文](../zh-Hans/commands.md) · [Español](../es/commands.md) · **Français**

Voir le tableau des commandes du README pour la liste complète. Cette page
explique juste une chose plus en détail : comment `llmw search` décide ce
qui compte comme un résultat.

## La recherche essaie trois approches, de la plus stricte à la plus souple

Vous pouvez taper une recherche comme vous poseriez une question — des
phrases complètes conviennent très bien, pas besoin de deviner des
mots-clés particuliers. En coulisse, l'outil essaie jusqu'à trois
approches, et ne passe à la suivante que si la précédente n'a rien trouvé
du tout — donc une note qui correspond exactement à votre recherche ne
sera jamais reléguée derrière une note qui ne correspond qu'à moitié :

1. **Stricte** — chaque mot de votre recherche doit apparaître quelque part dans la note.
2. **Souple** — les mots qui n'apparaissent dans aucune note (fautes de
   frappe, ou une forme légèrement différente d'un mot) sont
   discrètement ignorés ; les autres mots doivent quand même
   correspondre.
3. **N'importe quelle correspondance** — chaque mot devient facultatif, et
   les résultats sont simplement classés selon leur degré de
   correspondance.

Si vous demandez un résultat en `--json`, il vous indique laquelle des
trois approches a trouvé le résultat :
`{"mode": "strict"|"relaxed"|"any", "dropped_tokens": [...], "results": [...]}`.
Ajoutez `--strict` si vous ne voulez toujours que le premier type de
correspondance, le plus strict.

Pour le texte en coréen : un mot de recherche qui est un simple nom coréen
avec une petite terminaison grammaticale collée dessus (comme `스탯창을`
ou `포탈에서`) se voit retirer cette terminaison avant la recherche
(pour donner `스탯창`, `포탈`), pour pouvoir quand même retrouver une note
qui utilise juste le nom tout simple. Cela ne gère qu'une petite liste de
terminaisons courantes, pas toutes les formes possibles de tous les
mots — c'est pensé pour ne jamais faire manquer une note, tout au plus
pour classer les résultats un peu différemment de ce à quoi on
s'attendrait.
