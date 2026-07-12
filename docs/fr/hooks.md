# Les filets de sécurité intégrés au plugin

[English](../en/hooks.md) · [한국어](../ko/hooks.md) · [日本語](../ja/hooks.md) · [简体中文](../zh-Hans/hooks.md) · [Español](../es/hooks.md) · **Français**

Installer le plugin Claude Code (voir [installation.md](installation.md))
active quatre fonctionnalités de sécurité automatiques. Aucune d'elles
n'est indispensable pour utiliser `llmw` — ce sont juste des commodités en
plus d'un outil qui se protège déjà tout seul de toute façon.

## Fonctionnalité 1 : empêcher l'IA de modifier les notes de la mauvaise manière

Rien n'empêche techniquement un assistant IA d'ignorer cet outil et de
modifier directement une note du wiki, comme il le ferait pour n'importe
quel autre fichier. Si cela arrive, vous perdez la sauvegarde
automatique, la note obligatoire expliquant « pourquoi ce changement », et
la vérification que la note reste bien écrite — et en pratique, cela
arrive dès qu'une autre instruction prend le dessus sans jamais mentionner
cet outil.

Quand il est installé comme plugin Claude Code, une vérification de
sécurité intercepte ce cas : si l'IA essaie de modifier directement une
note du wiki avec ses outils habituels d'édition de fichiers, la
modification est bloquée (ou, si vous préférez, elle demande d'abord une
confirmation), et l'IA reçoit exactement la commande `llmw` à utiliser à
la place — elle peut donc réessayer immédiatement, de la bonne façon,
sans rester bloquée.

Cette vérification ne s'intéresse qu'aux modifications visant les notes
du wiki (et le dossier `raw/`, les notes de matériel source non modifiées
à partir desquelles le wiki est construit) dans un projet qui utilise cet
outil — tout le reste est laissé complètement tranquille, y compris la
simple lecture de fichiers.

Vous pouvez désactiver cette vérification, ou changer son niveau de
sévérité, projet par projet, dans `.llmw/config.toml` — le même réglage
contrôle à la fois les notes du wiki et le dossier `raw/` :

```toml
[hooks]
wiki_guard = "deny"  # par défaut : bloquer la modification, et expliquer la bonne façon de faire
# wiki_guard = "ask"   # demander une confirmation au lieu de bloquer
# wiki_guard = "off"   # désactiver cette vérification pour ce projet
```

Sur Windows, cette vérification a besoin de « Git Bash » installé pour
fonctionner. S'il est absent, la vérification ne se lance tout simplement
pas — les propres règles de sécurité intégrées de `llmw` (une raison
obligatoire à chaque changement, des sauvegardes avant chaque
modification, etc.) s'appliquent quand même dans tous les cas.

## Fonctionnalité 2 : rappeler à l'IA de consulter le wiki avant chaque demande

Un wiki plein de décisions passées et d'erreurs déjà commises n'est utile
que si l'IA le consulte vraiment avant de commencer un nouveau travail —
et livrée à son propre jugement, elle n'y pense pas toujours. (C'est le
même problème qu'on rencontre avec un wiki tenu à la main dans une
application de prise de notes : vous notez tout consciencieusement, et
l'IA va quand même répéter une erreur que vous aviez déjà notée, parce que
rien ne lui a rappelé d'aller regarder.)

Un petit rappel s'affiche aussi au début de chaque session : « ce projet
a un wiki avec N notes » si un wiki existe déjà, ou un indice d'une ligne
« vous devriez lancer `llmw init` » sinon — pour que l'IA connaisse
l'existence de cet outil dès le tout premier message, même dans un projet
tout neuf.

Pour aller encore plus loin, la plupart des messages que vous envoyez se
voient aussi attacher un court rappel : « ce projet a un wiki — cherchez-y
d'abord ». C'est volontairement simple : ce rappel n'essaie pas de
deviner si votre message est vraiment lié à quelque chose dans le wiki en
comparant des mots-clés, parce que ce genre de déduction automatique peut
facilement passer à côté d'une note formulée différemment de votre
message. Il se contente plutôt de demander à l'IA d'aller vérifier, à
chaque fois, et laisse le vrai jugement — et la recherche elle-même — à
l'IA. (Un message très court, comme « ok » ou « merci », ne déclenche pas
le rappel — il n'y a pas vraiment de travail qui commence là pour le
confronter au wiki.)

À lui seul, ce rappel n'est qu'un coup de pouce léger — il ne bloque
jamais votre demande et ne la ralentit pas non plus, et il ne peut pas
empêcher l'IA de continuer de toute façon. En pratique, voir la même
ligne à chaque tour la rend aussi facile à ignorer avec le temps.

Il y a donc en dessous une deuxième couche, plus forte : la première
fois, au cours d'une session, que l'IA essaie de modifier un vrai
fichier du projet (pas une note du wiki elle-même) sans avoir encore
fait de recherche, cette modification est mise en pause une fois, et on
lui demande soit de chercher d'abord, soit de décider explicitement que
cette tâche n'en a pas besoin. Cela ne se déclenche qu'une fois par
session au maximum — dès qu'une recherche est lancée (même ponctuelle),
ou juste après cette unique vérification, les modifications reprennent
normalement. Ce n'est toujours pas un verrou total : l'IA peut confirmer
et continuer sans jamais avoir réellement cherché. Ce que cela apporte,
c'est un moment de décision forcé, au lieu d'un rappel qu'on peut
facilement faire défiler sans y penser.

```toml
[hooks]
search_gate = "ask"  # par défaut : met en pause la première vraie modification d'une session jusqu'à ce qu'on cherche ou confirme
# search_gate = "off"   # désactive cette vérification pour ce projet
```

## Fonctionnalité 3 : rappeler à l'IA de mettre le wiki à jour une fois le travail terminé

Un wiki ne reste utile que s'il suit vraiment ce qui s'est passé — et
tout comme une IA peut oublier de consulter le wiki avant de commencer,
elle peut tout aussi bien terminer un vrai travail sans jamais en
laisser de trace écrite, même avec les meilleures intentions au départ.

Pour repérer ça, `llmw` garde la trace, par session, du fait que des
fichiers du projet ont changé depuis la dernière fois que le wiki a été
touché (via `llmw write`/`edit`/`patch`/`archive`). Si l'IA essaie de
terminer son tour alors que c'est toujours le cas, elle est arrêtée une
fois et on lui demande soit de noter ce qui a changé et pourquoi, soit
de décider explicitement que ce changement précis ne mérite pas de mise
à jour du wiki. Comme la vérification de recherche ci-dessus, cela se
déclenche au maximum une fois par tour — la propre protection
anti-boucle de Claude Code garantit que ça ne peut jamais devenir une
boucle de réessai bloquée — donc ça relance le rappel à la fin du tour
*suivant* si le wiki n'a toujours pas rattrapé son retard, plutôt que
d'insister à chaque message.

```toml
[hooks]
update_gate = "ask"  # par défaut : met en pause une fois par tour quand le code a changé mais pas le wiki
# update_gate = "off"   # désactive cette vérification pour ce projet
```

## Fonctionnalité 4 : garder l'outil en ligne de commande lui-même à jour

Le plugin comprend un petit programme d'appoint, mais le vrai travail est
fait par une copie séparée de `llmw` installée sur votre ordinateur.
Mettre à jour le plugin via la marketplace ne met **pas** automatiquement
à jour cette copie séparée — sans intervention, vous pourriez vous
retrouver à utiliser une version dépassée sans même vous en rendre compte.

Pour éviter ça, une vérification rapide se lance au début de chaque
session : elle compare la version de `llmw` installée sur votre ordinateur
à la version attendue par le plugin. Si elles ne correspondent pas — y
compris si `llmw` n'est pas encore installé du tout — elle réinstalle
automatiquement la bonne version pour vous. Donc mettre à jour le plugin
garde aussi l'outil en ligne de commande synchronisé, sans rien de plus à
faire de votre côté.

Quand les versions correspondent déjà, cette vérification est juste un
contrôle rapide et local, sans besoin de connexion internet — la
réinstallation ne se déclenche que dans les rares cas où quelque chose
n'est plus synchronisé.
