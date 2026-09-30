# Coach Sportif IA

Application web de coaching sportif qui crée un programme d'entraînement personnalisé à partir du profil et des objectifs de l'utilisateur. Une interface de chat accompagne le bilan, le suivi des séances et l'adaptation du programme.

## Fonctionnalités

- Bilan guidé : IMC, objectif, niveau, contraintes et fréquence d'entraînement.
- Compréhension des messages par règles, puis par un classifieur de texte scikit-learn.
- Génération d'un programme sportif personnalisé et remplacement d'exercices.
- Suivi des séances et de la progression.
- Export du programme en PDF.
- Réponses et conseils complémentaires grâce à Ollama, si le service est installé et lancé.
- Interface en français avec réponses rapides et affichage de l'état du parcours.

## Technologies

- Python et Flask pour le serveur et l'API.
- scikit-learn pour la classification des intentions.
- HTML, CSS et JavaScript pour l'interface.
- Ollama (facultatif) pour les réponses générées par un modèle local.
- ReportLab pour produire les PDF.

## Prérequis

- Python 3 et `pip`.
- Ollama uniquement si vous souhaitez activer les réponses IA génératives.

## Installation et lancement

Depuis la racine du projet :

```bash
python -m venv .venv
```

Activez l'environnement virtuel :

```bash
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

Installez les dépendances :

```bash
python -m pip install -r requirements.txt
```

Lancez l'application :

```bash
python app.py
```

Ouvrez ensuite [http://localhost:5000](http://localhost:5000) dans votre navigateur. Au premier lancement, si le fichier `models/modele_coach.pkl` est absent, le classifieur est entraîné à partir des intentions présentes dans le moteur.

## Activer les réponses IA avec Ollama (facultatif)

Installez [Ollama](https://ollama.com/), puis démarrez le service et téléchargez un modèle pris en charge, par exemple `mistral` :

```bash
ollama serve
ollama pull mistral
```

L'application détecte Ollama à l'adresse locale `http://localhost:11434`. Sans Ollama, le parcours guidé et la génération de programme restent disponibles ; les réponses génératives ne le sont pas.

## Structure du projet

```text
.
├── app.py                  # Application Flask et routes API
├── coach_engine.py         # Dialogue, classification, programmes et suivi
├── models/
│   └── modele_coach.pkl    # Classifieur entraîné
├── templates/
│   └── index.html          # Page principale
├── static/
│   ├── css/style.css       # Styles de l'interface
│   └── js/chat.js          # Logique du chat côté navigateur
├── data/                   # Intentions et programmes générés
├── progressions/           # Fichiers de suivi générés
└── programmes_pdf/         # Programmes exportés
```

Les dossiers de stockage nécessaires sont créés automatiquement s'ils n'existent pas.

## API principale

| Méthode | Route | Description |
| --- | --- | --- |
| `POST` | `/api/session` | Crée une session de coaching. |
| `POST` | `/api/chat` | Envoie un message dans une session. |
| `GET` | `/api/progression/<session_id>` | Consulte les statistiques de progression. |
| `GET` | `/api/pdf/<session_id>` | Télécharge le programme de la session. |
| `POST` | `/api/poids` | Enregistre une mesure de poids. |
| `GET` | `/api/ollama/statut` | Vérifie la disponibilité d'Ollama. |
| `POST` | `/api/reset/<session_id>` | Réinitialise une session. |

## Données et confidentialité

Les sessions actives sont conservées en mémoire et les programmes et progressions peuvent être écrits dans `data/`, `progressions/` et `programmes_pdf/`. Les programmes, progressions, PDF, environnements virtuels et modèle entraîné locaux sont exclus du dépôt par `.gitignore`. Ne publiez pas de données d'utilisateurs.

## Avertissement

Cette application fournit des suggestions générales d'entraînement et ne remplace pas l'avis d'un médecin ou d'un professionnel de santé. En cas de douleur, de blessure ou de problème de santé, demandez conseil à un professionnel avant de commencer ou de modifier une activité physique.

## Développement

Le lancement avec `python app.py` active le mode debug de Flask : utilisez-le uniquement pour le développement local, pas pour déployer l'application en production.
