<a name="readme-top"></a>

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/JustNao/Karrelage">
    <img src="static/k-white-fill.svg" alt="Logo" width="80" height="80" fill="white">
  </a>

<h3 align="center">Karrelage</h3>

  <p align="center">
    MITM pour Dofus 2.XX
    <br />
    <br />
    <a href="https://github.com/JustNao/Karrelage/issues">Report Bug</a>
  </p>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Sommaire</summary>
  <ol>
    <li>
      <a href="#about-the-project">A propos du projet</a>
    </li>
    <li>
      <a href="#installation">Installation</a>
    </li>
    <li>
      <a href="#modules">Modules</a>
      <ul>
        <li><a href="#module-hdv">HDV Filter</a></li>
        <li><a href="#module-team-manager">Team Manager</a></li>
        <li><a href="#module-forgemager">Forgemager</a></li>
        <li><a href="#module-biscuit">Biscuit</a></li>
        <li><a href="#module-treasure-hunter">Treasure Hunter</a></li>
        <li><a href="#module-debug">Debug</a></li>
      </ul>
    </li>
    <li>
    <a href="#packet-read">Lecture de packets</a>
      <ul>
        <li><a href="#sniffer">Sniffer</a></li>
        <li><a href="#attach">Attach</a></li>
      </ul>
    </li>
    <li><a href="#dev">Développement</a></li>
    <li><a href="#copyright">Copyright</a></li>
    <li><a href="#license">Licence</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->

## A propos du projet

<a name="about-the-project"></a>

Karrelage est un MITM pour Dofus 2.XX en Python 3. C'est la suite de [DofusHelper](https://github.com/JustNao/DofusHelper), avec une interface plus moderne et un système de module et de packet sniffing plus flexible. Il utilise [LaBot](https://github.com/louisabraham/LaBot) pour capter les paquets reçus par le client. Un système de module permet de créer plusieurs handlers à leur réception (voir plus bas pour des exemples). L'interface utilise Flask, avec TailwdindCSS et Flowbite pour le style.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- GETTING STARTED -->

## Installation

<a name="installation"></a>

1. Installer [Python 3](https://www.python.org/downloads/)
2. Ajouter PIP (installé avec les dernières versions de Python) [à votre Path](https://www.architectryan.com/2018/03/17/add-to-the-path-on-windows-10/). Si vous n'avez rien touché à l'installation de python, le dossier à ajouter devrait être
   'C:\Program Files\Python3XX\Scripts'.
3. Installer Npcap (https://npcap.com/dist)
4. Installer [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
5. Exporter le git (bash, zip, ...)
6. Installer les packages python
   ```sh
   pip install -r requirements.txt
   ```
   ou en lançant le fichier `install.bat`.
7. Lancer l'interface par la commande
   ```sh
   python app.py
   ```
   ou en lançant le fichier `launch.bat`.
   <p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- USAGE EXAMPLES -->

## Modules

<a name="modules"></a>

Karrelage utilise un système de module pour gérer les paquets reçus. Un module est un fichier python qui contient une classe qui hérite de la classe `DofusModule`. Cette classe contient une méthode `handle_packet` qui parse les messages reçus par le client, et envoie le packet avec à la fonction correspondante du module (sous la forme `handle_<packet_name>`).
Le menu de Karrelage permet de sélectionner quel module lancer. Actuellement, un seul module peut être lancé à la fois.

[![Menu Screenshot][menu-screenshot]](#)

### Module HDV Filter

<a name="module-hdv"></a>

Ce module sert à filtrer les ventes d'équipements en HDV. En sélectionnant un item en HDV, ses caractéristiques sont affichées sur l'interface de Karrelage. Vous pouvez ensuite spécifier des valeurs minimums pour chaque caractéristique, et le module ne vous affichera que les ventes qui correspondent à ces valeurs. Vous pouvez aussi rapidement ajouter un exo PA/PM/PO par les boutons.

[![HDV Filter Screenshot][hdv-screenshot]](https://example.com)

Vous pouvez ensuite bouger entre chaque vente. Le module affichera les caractéristiques de l'équipement, ainsi que le prix de vente. Un code couleur indique si la caractéristique est en jet parfait, over, exo, négative, ou moins de la valeur minimale. Une option `Stats négatives` permet aussi d'afficher la distance au jet parfait.

[![HDV Filter Screenshot][hdv-screenshot2]](https://example.com)

### Module Team Manager

<a name="module-team-manager"></a>

Ce module est un outil multicompte combiné à un récap d'équipe.

- Récap d'équipe : en entrée de combat, il affiche tous les membres de l'équipe, et compatibilise tout au long du combat les dégâts infligés, soins/bouclier envoyés et vols de vie appliqués.
- Partie multicompte : détecte les personnages de l'équipe que vous jouez. A chaque début de tour d'un jour, il met au premier plan le personnage en question (pas besoin de Alt+Tab). Il est possible de mettre dans le fichier `config/multicompte.json` les noms des personnages que vous jouez, ce qui activera la fonctionnalité de clic partagé (un clic milieu de la souris envoie un clic gauche sur tous les personnages de l'équipe à la même position). Il y'a aussi une option sur chacun de vos personnages d'activer un mode "Passe tour automatique", qui au lieu d'ouvrir la fenetre en début de tour, va envoyer la touche `V` (qui pour moi fait passer le tour) même en arrière plan (mater un film pendant un PL sasa par exemple). Faites juste attention à ne pas avoir un challenge qui vous demande d'effectuer une action avant de passer, car le passage de tour est instant.

[![Team Manager Screenshot][team-screenshot]](https://example.com)

### Forgemager

<a name="module-forgemager"></a>

Forgemager est un module de calcul automatique du reliquat. Il suit les runes utilisées ainsi que les résultats de chaque tentative, et vous affiche le reliquat disponible à un moment donné. Vous pouvez aussi manuellement augmenter/diminuer le reliquat manuellement, si vous commencez un FM avec déjà du reliquat sur l'item par exemple.

[![Forgemager screenshot][forgemager-screenshot]](https://postimg.cc/v1wzQj3m)

### Biscuit

<a name="module-biscuit"></a>

Biscuit est un module "Quality of Life". Il est destiné à être laissé en arrière plan, si un autre module n'est pas déjà en cours d'execution. C'est ici que je mets toutes les idées de petites fonctionnalités utiles qui n'ont pas de raison d'avoir un module à part. Pour l'instant, il y'a :

- Un système de commandes, utilisables en jeu. Il suffit d'utiliser le canal de guilde `/g` ou groupe `/p`, et de lancer les commander avec `$command`. Par exemple, `$price` suivi d'un link (Ctrl+shift) d'un item va calculer le prix de craft estimé à partir de la recette, et du prix moyen des ressources associées. `$srambad` et les autres variantes de dimension va afficher la position des portails de la dimension en question. Les réponses sont envoyées dans le chat actuel.
- Une détection d'archimonstre & d'avis de recherche (un son est joué en entrant sur la map), et une détection de maisons abandonnées seules (qui seront donc mises en vente au mois prochain).
  L'interface permet de choisir quels outils utiliser.

[![Biscuit screenshot][biscuit-screenshot]](#)

### Treasure Hunter

<a name="module-treasure-hunter"></a>

Treasure Hunter est un bot chasse aux trésors. Une fois celui-ci ouvert, lancez une chasse au trésor. Pour la première étape rien ne va se passer, mais une fois que allez arriver vers la position de lancement, il va aller à chaque indice automatiquement. L'interface affiche pour l'instant uniquement une option d'autopilot, qui va utiliser votre monture autopilotée à la place d'un clic sur les bords de l'écran. Pour trouver les indices, Treasure Hunter ouvre en background une fenêtre Chrome (contrôlée par Selenium), et utilise [DofusDB](https://dofusdb.fr/fr/tools/treasure-hunt) pour dynamiquement obtenir la position des indices.

### Debug

<a name="module-debug"></a>

Ici c'est juste un module de debug qui permet de parcourir tous les packets reçus. On affiche le type de packet, timestamp et packet size. Si vous sélectionnez un packet, son contenu en format json est affiché. On peut filtrer les types et le contenu des packets.

[![Debug screenshot][debug-screenshot]](#)

## Lecture de packets

<a name="packet-read"></a>

Karrelage intègre deux type de lecture de packet, sélectionnables depuis le menu avant del ancer un module : `Sniffer` et `Attach`.

### Sniffer

<a name="sniffer"></a>

Karrelage va simplement écouter tous les packets reçus par <b>n'importe quel client Dofus</b>. Il ne modifie aucune connexion entrance/sortante. Fonctionne très bien, mais a du mal à gérer les gros packets qui sont envoyés au même moment pour plusieurs clients (comme les packets de combat en multicompte). `Sniffer` est donc à utiliser quand vous êtes en mono-compte, ou n'avez pas besoin du module de combat. Lancez le à n'importe quel moment et ça marchera. C'est le mode par défaut.

### Attach

<a name="attach"></a>

Karrelage va ici hijack la connexion avec le serveur d'un client en particulier, et va ensuite transférer les packets entrants/sortants de ce client uniquement. On peut ainsi éviter d'avoir des problèmes de packet qui se chevauchent. C'est le mode à utiliser quand vous êtes en multicompte et que vous utilisez le module de combat.

Plus délicat à lancer, il faut qu'il arrive à intercepter la connexion client/serveur, qui se lance quand vous sélectionnez un serveur, ou changez de personnage. Trouvez la manip qui vous arrange le plus, et gardez Karrelage d'ouvert pour qu'il capte la connexion. De plus, Karrelage s'occupant de la transmission des packets, si celui est fermé (par vous ou par un crash) la connexion client/serveur est temporairement perdue et ça va vous faire une mini re-connexion.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Développement

<a name="dev"></a>

Commande pour lancer l'auto-compilation du CSS par TailwindCSS (nécessite `NodeJS`):

```sh
npx tailwindcss -i ./static/src/input.css -o ./static/dist/css/output.css --watch
```

Manuellement mettre à jour les packets (nécessite FFDec, testé avec la [version 20.1.0](https://github.com/jindrapetrik/jpexs-decompiler/releases/tag/version20.1.0)) :
```sh
python scripts/update_packets.py
```

Manuellement mettre à jour les ressources du jeu (noms d'item, noms de monstres, etc...):
```sh
python -m scripts.update_game_ressources
```

## Copyright

<a name="copyright"></a>

Merci à [LaBot](https://github.com/louisabraham/LaBot) pour son reader/writer de packet et [balciseri](https://github.com/balciseri/PyDofus) pour son reader/writer de fichiers Dofus.

## License

<a name="license"></a>

[MIT](https://choosealicense.com/licenses/mit/)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->

[menu-screenshot]: https://i.postimg.cc/85c8j0cG/image.png
[team-screenshot]: https://i.postimg.cc/mkMQQgW0/Screenshot-2023-03-21-183926.png
[hdv-screenshot]: https://i.postimg.cc/7Yk5d8cV/Screenshot-2023-03-21-183619.png
[hdv-screenshot2]: https://i.postimg.cc/cLGBFbMy/Screenshot-2023-03-21-183925.png
[forgemager-screenshot]: https://i.postimg.cc/g0nBKbh3/image.png
[biscuit-screenshot]: https://i.postimg.cc/Nf9H1sS9/image.png
[debug-screenshot]: https://i.postimg.cc/K8KhGVKy/image.png
