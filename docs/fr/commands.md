# Détails des commandes

[English](../en/commands.md) · [한국어](../ko/commands.md) · [日本語](../ja/commands.md) · [简体中文](../zh-Hans/commands.md) · [Español](../es/commands.md) · **Français**

Voir le tableau de référence des commandes du README pour la liste complète des commandes et de leurs drapeaux. Cette page couvre les parties trop profondes pour une entrée de tableau d'une ligne.

## Sémantique de recherche

`llmw search` ne nécessite jamais une formulation exclusive aux mots-clés — une requête en langage naturel complet convient. Il essaie jusqu'à trois niveaux, ne passant au suivant que quand le précédent ne trouve rien, donc une correspondance complète ne peut jamais être dépassée par une partielle :

1. **strict** — chaque terme de requête requis (AND).
2. **relaxed** — les termes qui ne peuvent correspondre à aucune page indexée du tout (fautes de frappe, conjugaisons verbales) sont supprimés ; le reste est toujours requis.
3. **any** — chaque terme devient optionnel (OR), classé par pertinence.

La sortie `--json` rapporte quel niveau a répondu à la requête : `{"mode": "strict"|"relaxed"|"any", "dropped_tokens": [...], "results": [...]}`. Passez `--strict` pour désactiver les niveaux de fallback et n'exécuter que le niveau 1.

Les termes de requête qui sont un mot Hangul unique avec une particule finale (un 조사 — par exemple `스탯창을`, `포탈에서`) sont trouvés à la racine nue (`스탯창`, `포탈`) avant correspondance, puisque la recherche de préfixe FTS5 SQLite ne correspond qu'à une requête qui est un préfixe du mot indexé, pas l'inverse, donc une requête fléchie manquerait autrement une page de nom nu. C'est une petite liste de suffixes curatée, pas un analyseur morphologique complet — il ne stemme pas les conjugaisons verbales (c'est ce que le niveau relaxed est pour) et occasionnellement supprimera une fin coïncidentelle non-particule (par exemple `도로` → `도`) ; c'est toujours recall-safe (le stem est un préfixe du mot original) au pire ajoutant du bruit de classement mineur, jamais une page manquée.
