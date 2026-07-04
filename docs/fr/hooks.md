# Les filets de sécurité intégrés au plugin

[English](../en/hooks.md) · [한국어](../ko/hooks.md) · [日本語](../ja/hooks.md) · [简体中文](../zh-Hans/hooks.md) · [Español](../es/hooks.md) · **Français**

Installer le plugin Claude Code (voir [installation.md](installation.md))
active deux fonctionnalités de sécurité automatiques. Aucune des deux
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
du wiki dans un projet qui utilise cet outil — tout le reste est laissé
complètement tranquille, y compris la simple lecture de fichiers.

Vous pouvez désactiver cette vérification, ou changer son niveau de
sévérité, projet par projet, dans `.llmw/config.toml` :

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

Un petit rappel s'affiche aussi au début de chaque session : « ce projet
a un wiki avec N notes » si un wiki existe déjà, ou un indice d'une ligne
« vous devriez lancer `llmw init` » sinon — pour que l'IA connaisse
l'existence de cet outil dès le tout premier message, même dans un projet
tout neuf.

## Fonctionnalité 2 : garder l'outil en ligne de commande lui-même à jour

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
