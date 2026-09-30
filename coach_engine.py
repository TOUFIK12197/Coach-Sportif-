# ============================================================
# coach_engine.py — Moteur principal du Coach Sportif IA
# ============================================================

import json
import re
import random
import os
import pickle
import unicodedata
import copy
import threading
import urllib.request
import urllib.error
from datetime import datetime

# ── Dossiers ──────────────────────────────────────────────
for d in ['data', 'models', 'progressions', 'programmes_pdf']:
    os.makedirs(d, exist_ok=True)

# ══════════════════════════════════════════════════════════
# 1. BASE DE CONNAISSANCES JSON
# ══════════════════════════════════════════════════════════

INTENTS_DATA = {
  "intents": [
    {
      "tag": "salutation",
      "patterns": [
        "bonjour", "salut", "coucou", "hello", "bonsoir",
        "hey", "hi", "bonne journée", "yo"
      ],
      "responses": [
        "Bonjour ! Je suis votre coach sportif personnel 💪",
        "Salut ! Heureux de vous accompagner !",
        "Hello ! Prêt à créer votre programme sur mesure ?"
      ]
    },
    {
      "tag": "au_revoir",
      "patterns": [
        "au revoir", "bye", "à bientôt", "ciao", "tchao",
        "bonne soirée", "bonne nuit", "je pars", "arrêter"
      ],
      "responses": [
        "À bientôt ! Bonne séance 🏃",
        "Au revoir ! La régularité est la clé du succès 🔥",
        "Ciao ! Revenez me voir pour suivre votre progression !"
      ]
    },
    {
      "tag": "objectif_poids",
      "patterns": [
        "perdre du poids", "maigrir", "mincir", "brûler des graisses",
        "perdre des kilos", "perte de poids", "affiner ma silhouette",
        "brûler des calories", "sécher", "réduire ma masse graisseuse",
        "perdre du ventre", "ventre plat", "éliminer les graisses",
        "perdre du gras", "perte de gras"
      ],
      "responses": ["Objectif perte de poids noté ! 🔥"]
    },
    {
      "tag": "objectif_muscle",
      "patterns": [
        "prendre de la masse", "musculation", "devenir plus fort",
        "muscle", "bodybuilding", "prise de masse", "développer mes muscles",
        "grossir en muscle", "renforcement musculaire", "hypertrophie",
        "sculpter mon corps", "tonifier", "force", "prendre du muscle"
      ],
      "responses": ["Objectif renforcement musculaire noté ! 💪"]
    },
    {
      "tag": "objectif_endurance",
      "patterns": [
        "améliorer mon endurance", "courir plus longtemps", "cardio",
        "marathon", "course à pied", "vélo", "natation", "triathlon",
        "souffle", "cardio-vasculaire", "résistance", "endurance",
        "10km", "semi-marathon", "améliorer ma condition physique",
        "courir", "running"
      ],
      "responses": ["Objectif endurance et cardio noté ! 🏃"]
    },
    {
      "tag": "objectif_forme",
      "patterns": [
        "rester en forme", "santé", "bien-être", "me sentir mieux",
        "souplesse", "flexibilité", "yoga", "pilates", "équilibre",
        "forme générale", "maintien", "garder la forme", "rester actif",
        "stress", "me détendre", "relaxation", "bien etre"
      ],
      "responses": ["Objectif bien-être et forme générale noté ! 🧘"]
    },
    {
      "tag": "niveau_debutant",
      "patterns": [
        "débutant", "jamais fait de sport", "je commence", "novice",
        "pas d'expérience", "sédentaire", "je ne fais pas de sport",
        "premier programme", "tout nouveau", "commencer le sport",
        "j'ai arrêté depuis longtemps", "reprise", "debutant"
      ],
      "responses": ["Niveau débutant noté 🌱"]
    },
    {
      "tag": "niveau_intermediaire",
      "patterns": [
        "intermédiaire", "quelques mois de sport", "pratique régulière",
        "1 an de sport", "2 ans", "assez expérimenté", "niveau moyen",
        "je m'entraine parfois", "quelques fois par semaine",
        "intermediaire", "moyen"
      ],
      "responses": ["Niveau intermédiaire noté 📈"]
    },
    {
      "tag": "niveau_avance",
      "patterns": [
        "avancé", "expert", "plusieurs années de sport", "compétition",
        "je m'entraîne tous les jours", "sportif confirmé", "athlète",
        "je connais bien", "niveau élevé", "avance", "confirme"
      ],
      "responses": ["Niveau avancé noté 🏆"]
    },
    {
      "tag": "contrainte_blessure",
      "patterns": [
        "blessure", "mal au genou", "douleur épaule", "problème de dos",
        "tendinite", "hernie discale", "arthrose", "opéré", "fracture",
        "entorse", "claquage", "douleur", "mal au dos", "lombalgie",
        "genou", "épaule", "dos"
      ],
      "responses": ["Blessure notée — programme adapté 📝"]
    },
    {
      "tag": "contrainte_temps",
      "patterns": [
        "peu de temps", "30 minutes", "45 minutes", "séances courtes",
        "pas beaucoup de temps", "surchargé", "occupé", "manque de temps",
        "pas le temps"
      ],
      "responses": ["Contrainte de temps notée ⏰"]
    },
    {
      "tag": "contrainte_materiel",
      "patterns": [
        "pas de salle de sport", "à la maison", "sans matériel",
        "haltères", "tapis", "élastiques", "poids de maison", "extérieur",
        "home gym", "maison"
      ],
      "responses": ["Contrainte matérielle notée 🏠"]
    },
    {
      "tag": "changer_exercice",
      "patterns": [
        "changer un exercice", "remplacer exercice", "je n'aime pas",
        "exercice alternatif", "substituer", "autre exercice",
        "modifier mon programme", "exercice de remplacement",
        "remplacer", "alternative", "changer", "supprimer exercice",
        "enlever exercice", "je veux changer", "remplace"
      ],
      "responses": ["Quel exercice souhaitez-vous remplacer ?"]
    },
    {
      "tag": "question_programme",
      "patterns": [
        "comment faire", "technique", "comment exécuter",
        "comment réaliser", "conseils sur", "expliquer",
        "je ne comprends pas", "comment", "explique"
      ],
      "responses": ["Je vous explique 🤖"]
    },
    {
      "tag": "motivation",
      "patterns": [
        "je suis découragé", "c'est trop dur", "j'abandonne", "pas motivé",
        "à quoi ça sert", "j'ai du mal", "je n'y arrive pas",
        "je veux arrêter", "c'est inutile", "je suis fatigué",
        "découragé", "abandonne", "fatigue"
      ],
      "responses": [
        "Ne lâchez pas ! 💪 Chaque séance compte !",
        "Les résultats arrivent. Continuez ! 🌟",
        "Les champions ont aussi des mauvais jours. Revenez ! 🔥"
      ]
    },
    {
      "tag": "progression",
      "patterns": [
        "mes stats", "mon évolution", "résultats", "mes progrès",
        "voir mon historique", "bilan", "combien de séances",
        "statistiques", "progression", "stats"
      ],
      "responses": ["Voici votre tableau de bord 📊"]
    },
    {
      "tag": "telecharger_pdf",
      "patterns": [
        "télécharger mon programme", "exporter en pdf", "avoir le pdf",
        "sauvegarder programme", "imprimer programme", "pdf",
        "telecharger", "télécharger"
      ],
      "responses": ["Génération du PDF en cours 📄"]
    },
    {
      "tag": "seance_faite",
      "patterns": [
        "j'ai fait ma séance", "séance terminée", "workout done",
        "j'ai fait mon entrainement", "séance faite", "c'est fait",
        "entrainement terminé", "j ai fait", "seance faite"
      ],
      "responses": ["Bravo ! Séance enregistrée 🎉"]
    },
    {
      "tag": "aide",
      "patterns": [
        "aide", "help", "je ne comprends pas", "comment ça marche",
        "que peux-tu faire", "quelles commandes", "expliquer"
      ],
      "responses": [
        "Je peux : créer votre programme, suivre votre progression, "
        "télécharger le PDF, remplacer des exercices !"
      ]
    },
    {
      "tag": "inconnu",
      "patterns": [],
      "responses": [
        "Je n'ai pas bien compris. Pouvez-vous reformuler ?",
        "Hmm, pouvez-vous préciser ?",
        "Pouvez-vous reformuler autrement ?"
      ]
    }
  ]
}

with open('data/intents_coach.json', 'w', encoding='utf-8') as f:
    json.dump(INTENTS_DATA, f, ensure_ascii=False, indent=2)


# ══════════════════════════════════════════════════════════
# 2. NLP — NORMALISATION & MATCHING
# ══════════════════════════════════════════════════════════

def normaliser(texte):
    texte = texte.lower().strip()
    nfkd  = unicodedata.normalize('NFKD', texte)
    texte = ''.join(c for c in nfkd if not unicodedata.combining(c))
    texte = re.sub(r'[^\w\s]', ' ', texte)
    return texte


def corriger_fautes(texte):
    corrections = {
        r'\bdebutant\b':      'débutant',
        r'\bintermediaire\b': 'intermédiaire',
        r'\bavance\b':        'avancé',
        r'\bmusculaton\b':    'musculation',
        r'\bendurence\b':     'endurance',
        r'\bmaigire\b':       'maigrir',
        r'\bpoid\b':          'poids',
        r'\bblesure\b':       'blessure',
        r'\bgenoux\b':        'genou',
        r'\bepaule\b':        'épaule',
        r'\bhalter\b':        'haltères',
        r'\belastique\b':     'élastiques',
        r'\bseance\b':        'séance',
        r'\bentrainement\b':  'entraînement',
        r'\bfrequence\b':     'fréquence',
        r'\bprogresion\b':    'progression',
        r'\btelecharger\b':   'télécharger',
    }
    texte_lower = texte.lower()
    for pattern, replacement in corrections.items():
        texte_lower = re.sub(pattern, replacement, texte_lower)
    return texte_lower


def trouver_intent_regles(message, intents_data):
    message_norm = normaliser(corriger_fautes(message))
    for intent in intents_data['intents']:
        for pattern in intent['patterns']:
            if normaliser(pattern) in message_norm:
                return intent['tag'], random.choice(intent['responses'])
    fallback = next(i for i in intents_data['intents'] if i['tag'] == 'inconnu')
    return 'inconnu', random.choice(fallback['responses'])


# ══════════════════════════════════════════════════════════
# 3. MACHINE LEARNING
# ══════════════════════════════════════════════════════════

def entrainer_modele():
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.pipeline import Pipeline

    X_data, y_data = [], []
    for intent in INTENTS_DATA['intents']:
        for pattern in intent['patterns']:
            X_data.append(normaliser(pattern))
            y_data.append(intent['tag'])

    modele = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
        ('clf',   MultinomialNB(alpha=0.1))
    ])
    modele.fit(X_data, y_data)

    with open('models/modele_coach.pkl', 'wb') as f:
        pickle.dump(modele, f)

    print(f'✅ Modèle ML entraîné — {len(X_data)} exemples')
    return modele


def charger_modele():
    if os.path.exists('models/modele_coach.pkl'):
        with open('models/modele_coach.pkl', 'rb') as f:
            return pickle.load(f)
    return entrainer_modele()


def trouver_intent_ml(message, modele, seuil=0.25):
    msg_norm = normaliser(corriger_fautes(message))
    probas   = modele.predict_proba([msg_norm])[0]
    classes  = modele.classes_
    idx      = probas.argmax()
    tag      = classes[idx]
    conf     = probas[idx]

    if conf < seuil:
        tag = 'inconnu'

    for intent in INTENTS_DATA['intents']:
        if intent['tag'] == tag:
            return tag, random.choice(intent['responses']), conf

    fallback = next(i for i in INTENTS_DATA['intents'] if i['tag'] == 'inconnu')
    return 'inconnu', random.choice(fallback['responses']), 0.0


def classifier_message(message, modele):
    # 1. Règles
    tag_r, rep_r = trouver_intent_regles(message, INTENTS_DATA)
    if tag_r != 'inconnu':
        return tag_r, rep_r, 'regles', 1.0
    # 2. ML
    tag_ml, rep_ml, conf = trouver_intent_ml(message, modele)
    if tag_ml != 'inconnu':
        return tag_ml, rep_ml, 'ml', conf
    # 3. Fallback
    fallback = next(i for i in INTENTS_DATA['intents'] if i['tag'] == 'inconnu')
    return 'inconnu', random.choice(fallback['responses']), 'fallback', 0.0


# ══════════════════════════════════════════════════════════
# 4. EXTRACTION D'ENTITÉS
# ══════════════════════════════════════════════════════════

ENTITES_SPORTIVES = {
    'parties_corps': [
        'genou', 'genoux', 'épaule', 'épaules', 'dos', 'lombaire',
        'cheville', 'chevilles', 'poignet', 'hanche', 'coude',
        'cou', 'nuque', 'mollet', 'cuisse', 'abdominaux',
        'pectoraux', 'biceps', 'triceps'
    ],
    'types_blessures': [
        'tendinite', 'hernie discale', 'arthrose', 'entorse',
        'claquage', 'fracture', 'luxation', 'lombalgie',
        'inflammation', 'contracture'
    ],
    'equipements': [
        'haltères', 'barre', 'kettlebell', 'élastiques',
        'tapis', 'corde à sauter', 'vélo stationnaire',
        'rameur', 'poids', 'banc', 'pull-up bar'
    ],
    'lieux': [
        'salle de sport', 'gym', 'gymnase', 'maison',
        'extérieur', 'parc', 'piscine'
    ]
}

PATTERNS_DUREE = [
    r'(\d+)\s*(?:fois|séances?)\s*(?:par|/)\s*semaine',
    r'(\d+)x\s*(?:par)?\s*semaine',
    r'(\d+)\s*(?:minutes?|min)',
    r'(\d+)\s*(?:heures?|h)\b',
    r'(\d+)\s*(?:jours?|j)\s*(?:par|/)?\s*semaine'
]


def extraire_entites(texte):
    texte_lower = texte.lower()
    entites = {
        'parties_corps':   [],
        'types_blessures': [],
        'equipements':     [],
        'lieux':           [],
        'frequences':      [],
        'durees':          [],
        'poids_kg':        None,
        'taille_cm':       None,
    }

    def norm(t):
        nfkd = unicodedata.normalize('NFKD', t.lower())
        return ''.join(c for c in nfkd if not unicodedata.combining(c))

    texte_norm = norm(texte)

    for cat, termes in ENTITES_SPORTIVES.items():
        for terme in termes:
            if norm(terme) in texte_norm and terme not in entites[cat]:
                entites[cat].append(terme)

    for pattern in PATTERNS_DUREE:
        for match in re.findall(pattern, texte_lower):
            val = int(match) if str(match).isdigit() else None
            if val:
                if 'semaine' in pattern and val <= 7:
                    entites['frequences'].append(val)
                else:
                    entites['durees'].append(val)

    m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:kg|kilos?)', texte_lower)
    if m:
        entites['poids_kg'] = float(m.group(1).replace(',', '.'))

    m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:cm|centimètres?)', texte_lower)
    if m:
        entites['taille_cm'] = float(m.group(1).replace(',', '.'))
    else:
        m = re.search(r'(\d[.,]\d+)\s*(?:m\b|mètres?)', texte_lower)
        if m:
            entites['taille_cm'] = float(m.group(1).replace(',', '.')) * 100
        else:
            m = re.search(r'\b(1[5-9]\d)\b', texte)
            if m:
                val = int(m.group(1))
                if 140 <= val <= 220:
                    entites['taille_cm'] = float(val)

    for cle in ['parties_corps', 'types_blessures', 'equipements',
                'lieux', 'frequences', 'durees']:
        entites[cle] = list(dict.fromkeys(entites[cle]))

    return entites


# ══════════════════════════════════════════════════════════
# 5. MACHINE À ÉTATS
# ══════════════════════════════════════════════════════════

class CoachDialogManager:
    """
    Machine à états pour le bilan sportif complet.
    États : accueil → imc → objectif → niveau →
            contraintes → frequence → generation → suivi
    """

    ETATS = [
        'accueil', 'imc', 'objectif', 'niveau',
        'contraintes', 'frequence', 'generation', 'suivi'
    ]

    QUESTIONS = {
        'accueil': (
            "Bonjour ! 💪 Je suis votre coach sportif personnel.\n\n"
            "Je vais créer un programme sportif sur mesure pour vous.\n"
            "Commençons par calculer votre **IMC** :\n\n"
            "Donnez-moi votre **poids (kg)** et votre **taille (cm)**\n"
            "Ex : *Je fais 175 cm et je pèse 70 kg*"
        ),
        'imc': (
            "Pouvez-vous me donner votre **poids (kg)** et **taille (cm)** ?\n"
            "Ex : *Je mesure 170 cm et pèse 65 kg*"
        ),
        'objectif':    "Quel est votre **objectif principal** ?",
        'niveau':      "Quel est votre **niveau sportif actuel** ?",
        'contraintes': (
            "Avez-vous des **contraintes** à me signaler ?\n"
            "(blessures, peu de matériel, peu de temps...)\n\n"
            "Tapez **aucune** si vous n'en avez pas."
        ),
        'frequence': (
            "Combien de **séances par semaine** pouvez-vous "
            "vous consacrer ?\n*(entre 2 et 5 séances)*"
        ),
    }

    RELANCES = {
        'imc': [
            "Je n'ai pas trouvé votre taille/poids. Ex : '175 cm, 70 kg'",
            "Précisez votre taille en cm et poids en kg svp."
        ],
        'objectif': [
            "Précisez : perte de poids, musculation, endurance ou forme ?",
            "Quel est votre objectif principal ?"
        ],
        'niveau': [
            "Quel est votre niveau ? Débutant, intermédiaire ou avancé ?",
            "Depuis combien de temps pratiquez-vous du sport ?"
        ],
        'contraintes': [
            "Des contraintes ? (blessures, matériel...) Ou tapez 'aucune'.",
            "Blessures, peu de matériel ? Sinon tapez 'aucune'."
        ],
        'frequence': [
            "Combien de fois par semaine ? (2 à 6)",
            "Ex : '3 fois par semaine' ou simplement '3'"
        ]
    }

    def __init__(self):
        self.etat                         = 'accueil'
        self.profil                       = {}
        self.compteur_fallback            = 0
        self.historique_etats             = ['accueil']
        self.attente_exercice_a_remplacer = False
        self.exercice_en_attente          = None

    def to_dict(self):
        return {
            'etat':                          self.etat,
            'profil':                        self.profil,
            'compteur_fallback':             self.compteur_fallback,
            'historique_etats':              self.historique_etats,
            'attente_exercice_a_remplacer':  self.attente_exercice_a_remplacer,
            'exercice_en_attente':           self.exercice_en_attente,
        }

    @classmethod
    def from_dict(cls, d):
        obj = cls.__new__(cls)
        obj.etat                         = d.get('etat', 'accueil')
        obj.profil                       = d.get('profil', {})
        obj.compteur_fallback            = d.get('compteur_fallback', 0)
        obj.historique_etats             = d.get('historique_etats', ['accueil'])
        obj.attente_exercice_a_remplacer = d.get('attente_exercice_a_remplacer', False)
        obj.exercice_en_attente          = d.get('exercice_en_attente', None)
        return obj

    def message_initial(self):
        self._transition('imc')
        return {
            'texte':   self.QUESTIONS['accueil'],
            'boutons': [],
            'etat':    self.etat,
            'profil':  self.profil
        }

    def traiter(self, message, intent_tag, entites):
        self.compteur_fallback = 0

        # ── Intents globaux ──
        if intent_tag == 'motivation':
            return self._rep(self._reponse_motivation())

        if intent_tag == 'au_revoir':
            return self._rep("À bientôt ! Bonne séance 💪", action='fin')

        if intent_tag == 'progression':
            return self._rep(None, action='afficher_progression')

        if intent_tag == 'telecharger_pdf':
            return self._rep(None, action='telecharger_pdf')

        if intent_tag == 'seance_faite':
            return self._rep(None, action='enregistrer_seance')

        if intent_tag == 'changer_exercice':
            if self.attente_exercice_a_remplacer:
                return self._rep(
                    "Quel exercice voulez-vous remplacer ? "
                    "Précisez son nom (ex: 'pompes', 'squats'...)"
                )
            self.attente_exercice_a_remplacer = True
            return self._rep(
                "🔄 Quel exercice souhaitez-vous remplacer ?\n\n"
                "Tapez le **nom de l'exercice** et je le remplacerai "
                "dans tout votre programme.\n"
                "Ex : *'remplacer les pompes'* ou *'changer les squats'*"
            )

        if intent_tag == 'question_programme':
            return self._rep(None, action='ollama_question')

        # ── Mode remplacement d'exercice ──
        if self.attente_exercice_a_remplacer:
            return self._rep(None, action='rechercher_exercice_a_remplacer')

        # ── Machine à états ──
        if self.etat == 'imc':
            return self._traiter_imc(message, entites)
        elif self.etat == 'objectif':
            return self._traiter_objectif(message, intent_tag)
        elif self.etat == 'niveau':
            return self._traiter_niveau(message, intent_tag)
        elif self.etat == 'contraintes':
            return self._traiter_contraintes(message, intent_tag, entites)
        elif self.etat == 'frequence':
            return self._traiter_frequence(message, entites)
        elif self.etat == 'suivi':
            return self._traiter_suivi(message, intent_tag, entites)
        else:
            return self._rep("Quel est votre objectif ?")

    # ── Helpers ───────────────────────────────────
    def _rep(self, texte, boutons=None, action=None):
        return {
            'texte':   texte,
            'boutons': boutons or [],
            'action':  action,
            'etat':    self.etat,
            'profil':  self.profil
        }

    def _transition(self, etat_suivant):
        self.etat = etat_suivant
        self.historique_etats.append(etat_suivant)
        self.compteur_fallback = 0

    def _fallback(self, etat):
        self.compteur_fallback += 1
        relances = self.RELANCES.get(etat, [])
        idx = min(self.compteur_fallback - 1, len(relances) - 1)
        msg = relances[idx] if relances else "Pouvez-vous reformuler ?"
        return self._rep(msg)

    # ── États ─────────────────────────────────────
    def _traiter_imc(self, message, entites):
        poids  = entites.get('poids_kg')
        taille = entites.get('taille_cm')

        if not poids:
            m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:kg|kilo)', message.lower())
            if m:
                poids = float(m.group(1).replace(',', '.'))
        if not taille:
            m = re.search(r'(\d+)\s*(?:cm)', message.lower())
            if m:
                taille = float(m.group(1))
            else:
                m = re.search(r'\b(1[5-9]\d)\b', message)
                if m:
                    taille = float(m.group(1))

        if poids and taille and poids > 0 and taille > 0:
            taille_m = taille / 100
            imc      = round(poids / (taille_m ** 2), 1)

            if imc < 18.5:
                cat     = 'maigreur'
                emoji   = '⚠️'
                conseil = "Votre IMC indique une maigreur. Programme orienté prise de masse saine."
                couleur = '#FF9800'
            elif imc < 25:
                cat     = 'normal'
                emoji   = '✅'
                conseil = "Votre IMC est normal. Excellent point de départ !"
                couleur = '#4CAF50'
            elif imc < 30:
                cat     = 'surpoids'
                emoji   = '⚠️'
                conseil = "IMC surpoids. Programme orienté perte de poids progressive."
                couleur = '#FF9800'
            elif imc < 35:
                cat     = 'obesite_moderee'
                emoji   = '🔴'
                conseil = "Programme adapté avec exercices à faible impact articulaire."
                couleur = '#F44336'
            else:
                cat     = 'obesite_severe'
                emoji   = '🔴'
                conseil = "Consultez un médecin avant de commencer. Exercices très doux."
                couleur = '#B71C1C'

            self.profil.update({
                'poids_kg':      poids,
                'taille_cm':     taille,
                'imc':           imc,
                'categorie_imc': cat,
                'imc_couleur':   couleur,
            })
            self._transition('objectif')

            texte = (
                f"{emoji} **IMC : {imc}** ({cat.replace('_', ' ')})\n"
                f"{conseil}\n\n"
                f"{self.QUESTIONS['objectif']}"
            )
            boutons = [
                {'label': '🔥 Perdre du poids',  'value': 'perdre du poids'},
                {'label': '💪 Musculation',       'value': 'musculation'},
                {'label': '🏃 Endurance',          'value': 'endurance'},
                {'label': '🧘 Forme générale',     'value': 'rester en forme'},
            ]
            return self._rep(texte, boutons)

        return self._fallback('imc')

    def _traiter_objectif(self, message, intent_tag):
        objectifs = {
            'objectif_poids':    ('Perte de poids 🔥',             '#FF5722'),
            'objectif_muscle':   ('Renforcement musculaire 💪',     '#2196F3'),
            'objectif_endurance':('Endurance et cardio 🏃',         '#4CAF50'),
            'objectif_forme':    ('Forme générale et bien-être 🧘', '#9C27B0'),
        }
        if intent_tag in objectifs:
            label, couleur = objectifs[intent_tag]
            self.profil['objectif']         = intent_tag
            self.profil['objectif_label']   = label
            self.profil['objectif_couleur'] = couleur
            self._transition('niveau')
            texte   = f"✅ **{label}** enregistré !\n\n{self.QUESTIONS['niveau']}"
            boutons = [
                {'label': '🌱 Débutant',      'value': 'débutant'},
                {'label': '📈 Intermédiaire', 'value': 'intermédiaire'},
                {'label': '🏆 Avancé',        'value': 'avancé'},
            ]
            return self._rep(texte, boutons)
        return self._fallback('objectif')

    def _traiter_niveau(self, message, intent_tag):
        niveaux = {
            'niveau_debutant':      ('Débutant 🌱',      '#8BC34A'),
            'niveau_intermediaire': ('Intermédiaire 📈', '#03A9F4'),
            'niveau_avance':        ('Avancé 🏆',        '#FF5722'),
        }
        if intent_tag in niveaux:
            label, couleur = niveaux[intent_tag]
            self.profil['niveau']         = intent_tag
            self.profil['niveau_label']   = label
            self.profil['niveau_couleur'] = couleur
            self._transition('contraintes')
            texte   = f"✅ **{label}** enregistré !\n\n{self.QUESTIONS['contraintes']}"
            boutons = [
                {'label': '🦵 Blessure genou',   'value': 'mal au genou'},
                {'label': '💪 Blessure épaule',  'value': 'douleur épaule'},
                {'label': '🔙 Mal au dos',        'value': 'mal au dos'},
                {'label': '🏠 Sans matériel',     'value': 'sans matériel'},
                {'label': '⏰ Peu de temps',      'value': 'peu de temps'},
                {'label': '✅ Aucune contrainte', 'value': 'aucune'},
            ]
            return self._rep(texte, boutons)
        return self._fallback('niveau')

    def _traiter_contraintes(self, message, intent_tag, entites):
        contraintes = []

        if intent_tag and intent_tag.startswith('contrainte_'):
            contraintes.append(intent_tag)

        if entites.get('parties_corps') or entites.get('types_blessures'):
            self.profil['blessures_detail'] = (
                entites['parties_corps'] + entites['types_blessures']
            )
            if 'contrainte_blessure' not in contraintes:
                contraintes.append('contrainte_blessure')

        if entites.get('equipements'):
            self.profil['equipements'] = entites['equipements']
        if entites.get('lieux'):
            self.profil['lieu'] = entites['lieux'][0]

        msg_lower = message.lower()
        mots_negatifs = ['aucune', 'aucun', 'non', 'pas de', 'rien', 'ok', 'oui']
        if any(m in msg_lower for m in mots_negatifs):
            contraintes = []

        self.profil['contraintes'] = contraintes
        self._transition('frequence')

        if contraintes:
            labels_c = {
                'contrainte_blessure': (
                    f"Blessure ({', '.join(self.profil.get('blessures_detail', []))})"
                ),
                'contrainte_temps':    'Manque de temps',
                'contrainte_materiel': 'Matériel limité',
            }
            c_txt = ', '.join([labels_c.get(c, c) for c in contraintes])
            texte = f"✅ Contraintes notées : **{c_txt}**\n\n{self.QUESTIONS['frequence']}"
        else:
            texte = f"✅ Aucune contrainte.\n\n{self.QUESTIONS['frequence']}"

        boutons = [
            {'label': '2x/semaine', 'value': '2 fois par semaine'},
            {'label': '3x/semaine', 'value': '3 fois par semaine'},
            {'label': '4x/semaine', 'value': '4 fois par semaine'},
            {'label': '5x/semaine', 'value': '5 fois par semaine'},
        ]
        return self._rep(texte, boutons)

    def _traiter_frequence(self, message, entites):
        freq = None
        if entites.get('frequences'):
            freq = entites['frequences'][0]
        if not freq:
            chiffres = re.findall(r'\b([2-6])\b', message)
            if chiffres:
                freq = int(chiffres[0])

        if freq and 1 <= freq <= 7:
            self.profil['frequence'] = freq
            self._transition('generation')
            return self._rep(
                "⏳ Génération de votre programme personnalisé...",
                action='generer_programme'
            )
        return self._fallback('frequence')

    def _traiter_suivi(self, message, intent_tag, entites):
        if intent_tag == 'motivation':
            return self._rep(self._reponse_motivation())
        if intent_tag == 'progression':
            return self._rep(None, action='afficher_progression')
        if intent_tag == 'telecharger_pdf':
            return self._rep(None, action='telecharger_pdf')
        if intent_tag == 'seance_faite':
            return self._rep(None, action='enregistrer_seance')
        if intent_tag == 'changer_exercice':
            self.attente_exercice_a_remplacer = True
            return self._rep(
                "🔄 Quel exercice souhaitez-vous remplacer ?\n\n"
                "Tapez le **nom de l'exercice** et je le remplacerai "
                "dans tout votre programme.\n"
                "Ex : *'remplacer les pompes'* ou *'changer les squats'*"
            )
        if intent_tag == 'question_programme':
            return self._rep(None, action='ollama_question')

        return self._rep(
            "Continuez sur votre lancée ! 💪\n"
            "• *'mes stats'* → voir votre progression\n"
            "• *'j\\'ai fait ma séance'* → enregistrer\n"
            "• *'télécharger'* → obtenir le PDF 📄\n"
            "• *'changer un exercice'* → remplacer un exercice 🔄"
        )

    def _reponse_motivation(self):
        return random.choice([
            "Ne lâchez pas ! 💪 La régularité est la clé !",
            "Les champions ont des mauvais jours. Revenez ! 🌟",
            "Vous êtes plus fort que vous ne le pensez ! 🔥",
            "Rappelez-vous pourquoi vous avez commencé ! 🎯"
        ])


# ══════════════════════════════════════════════════════════
# 6. GÉNÉRATEUR DE PROGRAMME
# ══════════════════════════════════════════════════════════

EXERCICES_DB = {
    'objectif_poids': {
        'niveau_debutant': [
            ('Marche rapide',            '30 min',      'Cardio'),
            ('Squats au poids du corps', '3x15',        'Jambes'),
            ('Pompes sur genoux',        '3x10',        'Haut du corps'),
            ('Gainage planche',          '3x30s',       'Abdominaux'),
            ('Jumping jacks',            '3x30s',       'Cardio'),
            ('Fentes avant',             '3x10/jambe',  'Jambes'),
        ],
        'niveau_intermediaire': [
            ('Course à pied',            '30 min',      'Cardio'),
            ('Burpees',                  '4x10',        'Full body'),
            ('Pompes',                   '4x15',        'Haut du corps'),
            ('Squats sautés',            '4x12',        'Jambes'),
            ('Mountain climbers',        '4x30s',       'Cardio'),
            ('Crunchs',                  '3x20',        'Abdominaux'),
        ],
        'niveau_avance': [
            ('HIIT 20/10',               '20 min',      'Cardio intense'),
            ('Burpees avec saut',        '5x12',        'Full body'),
            ('Box jumps',                '4x10',        'Explosivité'),
            ('Pompes claquées',          '4x10',        'Haut du corps'),
            ('Sprint 100m',              '8x',          'Cardio'),
            ('Gainage dynamique',        '4x45s',       'Abdominaux'),
        ]
    },
    'objectif_muscle': {
        'niveau_debutant': [
            ('Pompes',                   '3x8',         'Pectoraux/Triceps'),
            ('Squats',                   '3x12',        'Quadriceps'),
            ('Rowing haltères',          '3x10',        'Dos'),
            ('Curl biceps',              '3x12',        'Biceps'),
            ('Développé épaules',        '3x10',        'Épaules'),
            ('Gainage',                  '3x30s',       'Abdominaux'),
        ],
        'niveau_intermediaire': [
            ('Développé couché',         '4x10',        'Pectoraux'),
            ('Squat barre',              '4x8',         'Jambes'),
            ('Tractions',                '4x6',         'Dos/Biceps'),
            ('Développé militaire',      '4x8',         'Épaules'),
            ('Dips',                     '4x10',        'Triceps'),
            ('Soulevé de terre roumain', '3x10',        'Ischio/Dos'),
        ],
        'niveau_avance': [
            ('Squat lourd',              '5x5',         'Jambes (force)'),
            ('Développé couché lourd',   '5x5',         'Pectoraux (force)'),
            ('Soulevé de terre',         '5x5',         'Full body'),
            ('Tractions lestées',        '4x8',         'Dos'),
            ('Presse épaules',           '4x6',         'Épaules'),
            ('Dips lestés',              '4x8',         'Triceps'),
        ]
    },
    'objectif_endurance': {
        'niveau_debutant': [
            ('Marche/Jogging alterné',   '20 min',      'Endurance'),
            ('Vélo doux',                '30 min',      'Cardio'),
            ('Natation débutant',        '20 min',      'Cardio complet'),
            ('Corde à sauter',           '5x1 min',     'Cardio'),
            ('Étirements dynamiques',    '10 min',      'Mobilité'),
        ],
        'niveau_intermediaire': [
            ('Jogging 5km',              '30 min',      'Endurance'),
            ('Intervals 1min/1min',      '20 min',      'Cardio fractionné'),
            ('Vélo 45 min',              '45 min',      'Cardio'),
            ('Natation 1km',             '30 min',      'Endurance'),
            ('Circuit training',         '30 min',      'Cardio + force'),
        ],
        'niveau_avance': [
            ('Sortie longue 10km+',      '60 min+',     'Endurance fondamentale'),
            ('HIIT courte durée',        '20 min',      'VO2max'),
            ('Tempo run 5km',            '25 min',      'Allure seuil'),
            ('Natation 2km',             '45 min',      'Endurance'),
            ('Vélo 1h30',                '90 min',      'Endurance longue'),
        ]
    },
    'objectif_forme': {
        'niveau_debutant': [
            ('Yoga débutant',            '20 min',      'Souplesse'),
            ('Marche rapide',            '30 min',      'Cardio doux'),
            ('Pilates basique',          '30 min',      'Gainage/Souplesse'),
            ('Étirements complets',      '15 min',      'Mobilité'),
            ('Respiration',              '10 min',      'Récupération'),
        ],
        'niveau_intermediaire': [
            ('Yoga flow',                '45 min',      'Équilibre/Souplesse'),
            ('Jogging léger',            '30 min',      'Cardio'),
            ('Gainage avancé',           '4x45s',       'Abdominaux'),
            ('Mobilité articulaire',     '15 min',      'Prévention'),
            ('Natation',                 '30 min',      'Cardio complet'),
        ],
        'niveau_avance': [
            ('Yoga power',               '60 min',      'Force + Souplesse'),
            ('Course trail',             '45 min',      'Cardio/Nature'),
            ('Crossfit light',           '45 min',      'Full body'),
            ('Méditation sportive',      '20 min',      'Mental'),
        ]
    }
}

ADAPTATIONS_IMC = {
    'obesite_moderee': {
        'exclusions': ['jumping', 'saut', 'box jump', 'burpee', 'sprint'],
        'additions':  [
            ('Marche nordique',        '30 min', 'Cardio doux'),
            ('Vélo stationnaire',      '30 min', 'Cardio sans impact'),
            ('Étirements actifs',      '15 min', 'Mobilité'),
        ]
    },
    'obesite_severe': {
        'exclusions': ['jumping', 'saut', 'box jump', 'burpee', 'sprint',
                       'course', 'squat', 'fente'],
        'additions':  [
            ('Marche douce',           '20 min', 'Cardio très doux'),
            ('Vélo stationnaire doux', '20 min', 'Cardio assis'),
            ('Exercices assis',        '15 min', 'Renforcement'),
        ]
    },
    'maigreur': {
        'exclusions': ['sprint', 'hiit', 'cardio intense'],
        'additions':  [
            ('Pompes progressives',    '3x8',    'Prise de masse'),
            ('Squats goblet',          '3x12',   'Jambes'),
        ]
    }
}


def generer_programme(profil):
    objectif      = profil.get('objectif', 'objectif_forme')
    niveau        = profil.get('niveau',   'niveau_debutant')
    frequence     = profil.get('frequence', 3)
    blessures     = profil.get('blessures_detail', [])
    contraintes   = profil.get('contraintes', [])
    categorie_imc = profil.get('categorie_imc', 'normal')

    exercices_base = EXERCICES_DB.get(objectif, {}).get(niveau, [])

    adapt      = ADAPTATIONS_IMC.get(categorie_imc, {})
    exclusions = adapt.get('exclusions', [])
    additions  = adapt.get('additions', [])

    exercices = [
        ex for ex in exercices_base
        if not any(excl in ex[0].lower() for excl in exclusions)
    ]
    exercices = additions + exercices

    if blessures:
        mots_exclus = []
        for b in blessures:
            if 'genou'    in b: mots_exclus += ['squat', 'saut', 'fente', 'jump']
            if 'épaule'   in b: mots_exclus += ['développé', 'pompe', 'traction', 'dip']
            if 'dos'      in b: mots_exclus += ['soulevé', 'rowing', 'deadlift']
            if 'lombaire' in b: mots_exclus += ['soulevé', 'rowing']
        exercices = [
            ex for ex in exercices
            if not any(m in ex[0].lower() for m in mots_exclus)
        ]

    if len(exercices) < 3:
        exercices = exercices_base

    jours_sem    = ['Lundi', 'Mercredi', 'Vendredi', 'Samedi', 'Mardi', 'Jeudi', 'Dimanche']
    jours_actifs = jours_sem[:frequence]

    programme = {
        'profil': {
            'objectif':      profil.get('objectif_label', objectif),
            'niveau':        profil.get('niveau_label',   niveau),
            'frequence':     frequence,
            'blessures':     blessures,
            'contraintes':   [c.replace('contrainte_', '') for c in contraintes],
            'imc':           profil.get('imc'),
            'categorie_imc': categorie_imc,
            'poids_kg':      profil.get('poids_kg'),
            'taille_cm':     profil.get('taille_cm'),
        },
        'date_creation': datetime.now().strftime('%d/%m/%Y'),
        'duree':         '4 semaines',
        'semaines':      []
    }

    for num in range(1, 5):
        seances = []
        for j, jour in enumerate(jours_actifs):
            n_exos    = min(4, len(exercices))
            start     = (j * 2) % max(1, len(exercices))
            exos_jour = [exercices[(start + i) % len(exercices)] for i in range(n_exos)]
            note      = ['(découverte)', '(consolidation)', '+10% volume', '+20% volume'][num - 1]

            seances.append({
                'jour':      jour,
                'note':      note,
                'exercices': [
                    {'nom': e[0], 'volume': e[1], 'muscle': e[2]}
                    for e in exos_jour
                ]
            })

        programme['semaines'].append({
            'numero':  num,
            'titre':   f'Semaine {num}',
            'focus':   ['Adaptation', 'Progression', 'Intensification', 'Consolidation'][num - 1],
            'seances': seances
        })

    conseils = [
        "💧 Hydratez-vous : 1,5-2L/jour minimum.",
        "😴 Dormez 7-8h — la récupération est essentielle.",
        "🍎 Adaptez votre alimentation à votre objectif."
    ]
    if categorie_imc in ['obesite_moderee', 'obesite_severe']:
        conseils.append("⚠️ Consultez un médecin avant de commencer.")
    if 'contrainte_blessure' in contraintes:
        conseils.append("⚠️ Consultez un kiné avant les exercices ciblant votre blessure.")
    if niveau == 'niveau_debutant':
        conseils.append("🌱 Commencez doucement. La régularité prime sur l'intensité !")

    programme['conseils'] = conseils
    return programme


def formater_programme_texte(programme):
    p = programme['profil']
    lignes = [
        "## 🎯 Votre programme sportif personnalisé",
        "---",
        f"**Objectif** : {p['objectif']}",
        f"**Niveau** : {p['niveau']}",
        f"**Fréquence** : {p['frequence']} séances/semaine",
        f"**Durée** : {programme['duree']}",
    ]
    if p.get('imc'):
        lignes.append(
            f"**IMC** : {p['imc']} ({p.get('categorie_imc', '').replace('_', ' ')})"
        )
    if p.get('blessures'):
        lignes.append(f"**Adapté pour** : {', '.join(p['blessures'])}")

    lignes.append("")
    s1 = programme['semaines'][0]
    lignes.append(f"### 📅 {s1['titre']} — {s1['focus']}")
    for seance in s1['seances']:
        lignes.append(f"\n**🗓 {seance['jour']}** {seance['note']}")
        for ex in seance['exercices']:
            lignes.append(f"• {ex['nom']} — {ex['volume']} *({ex['muscle']})*")

    lignes += [
        "",
        "*(Semaines 2, 3, 4 progressivement plus intenses)*",
        "",
        "### 💡 Conseils personnalisés"
    ]
    for c in programme['conseils']:
        lignes.append(f"• {c}")

    lignes += [
        "",
        "---",
        "✅ Programme généré !",
        "📄 Tapez **'télécharger'** pour le PDF",
        "🔄 Tapez **'changer un exercice'** pour remplacer un exercice"
    ]
    return '\n'.join(lignes)


# ══════════════════════════════════════════════════════════
# 7. REMPLACEMENT D'EXERCICE
# ══════════════════════════════════════════════════════════

def extraire_exercice_depuis_message(message, programme):
    """
    Détecte quel exercice l'utilisateur veut remplacer
    en comparant son message aux exercices du programme.
    Retourne (exercice, semaine_idx, seance_idx, exercice_idx) ou (None,None,None,None)
    """
    if not programme:
        return None, None, None, None

    message_norm  = normaliser(message)
    meilleur_score = 0
    resultat       = (None, None, None, None)

    for s_idx, semaine in enumerate(programme.get('semaines', [])):
        for j_idx, seance in enumerate(semaine.get('seances', [])):
            for e_idx, ex in enumerate(seance.get('exercices', [])):
                nom_norm = normaliser(ex['nom'])
                mots_ex  = set(nom_norm.split())
                mots_msg = set(message_norm.split())
                communs  = mots_ex & mots_msg

                if communs:
                    score = len(communs) / max(len(mots_ex), 1)
                    if score > meilleur_score:
                        meilleur_score = score
                        resultat       = (ex, s_idx, j_idx, e_idx)

    if meilleur_score >= 0.3:
        return resultat
    return None, None, None, None


def remplacer_exercice_dans_programme(programme, semaine_idx,
                                       seance_idx, exercice_idx,
                                       nouvel_exercice):
    """
    Remplace un exercice dans TOUTES les semaines du programme
    à la même position (jour/index).
    """
    prog_modifie = copy.deepcopy(programme)

    for semaine in prog_modifie.get('semaines', []):
        seances = semaine.get('seances', [])
        if seance_idx < len(seances):
            exercices = seances[seance_idx].get('exercices', [])
            if exercice_idx < len(exercices):
                exercices[exercice_idx] = nouvel_exercice

    prog_modifie['date_modification'] = datetime.now().strftime('%d/%m/%Y %H:%M')
    return prog_modifie


def trouver_exercice_alternatif(exercice_original, profil, programme):
    """
    Trouve un exercice alternatif dans la base locale
    qui cible le même groupe musculaire.
    """
    objectif      = profil.get('objectif', 'objectif_forme')
    niveau        = profil.get('niveau',   'niveau_debutant')
    muscle        = exercice_original.get('muscle', '')
    nom_orig      = exercice_original.get('nom', '').lower()
    blessures     = profil.get('blessures_detail', [])
    categorie_imc = profil.get('categorie_imc', 'normal')

    # Mots à exclure selon blessures
    mots_exclus = []
    for b in blessures:
        if 'genou'   in b: mots_exclus += ['squat', 'saut', 'fente', 'jump']
        if 'épaule'  in b: mots_exclus += ['développé', 'pompe', 'traction', 'dip']
        if 'dos'     in b: mots_exclus += ['soulevé', 'rowing', 'deadlift']

    adapt = ADAPTATIONS_IMC.get(categorie_imc, {})
    mots_exclus += adapt.get('exclusions', [])

    # Exercices déjà dans le programme
    exercices_existants = set()
    for sem in programme.get('semaines', []):
        for seance in sem.get('seances', []):
            for ex in seance.get('exercices', []):
                exercices_existants.add(ex['nom'].lower())

    # Chercher des candidats
    candidats = []
    for obj_key, niveaux in EXERCICES_DB.items():
        for niv_key, exercices in niveaux.items():
            for ex in exercices:
                nom_ex = ex[0].lower()

                if nom_ex == nom_orig:
                    continue
                if any(m in nom_ex for m in mots_exclus):
                    continue

                muscle_ex   = ex[2].lower()
                muscle_orig = muscle.lower()
                mots_m_orig = set(muscle_orig.replace('/', ' ').split())
                mots_m_ex   = set(muscle_ex.replace('/', ' ').split())
                communs     = mots_m_orig & mots_m_ex

                score = 0
                if obj_key == objectif: score += 2
                if niv_key == niveau:   score += 2
                if communs:             score += len(communs) * 3

                if score > 0:
                    candidats.append((score, ex))

    # Fallback si aucun candidat
    if not candidats:
        for ex in EXERCICES_DB.get(objectif, {}).get(niveau, []):
            if ex[0].lower() != nom_orig and \
               not any(m in ex[0].lower() for m in mots_exclus):
                candidats.append((1, ex))

    if not candidats:
        return None

    # Trier par score
    candidats.sort(key=lambda x: x[0], reverse=True)

    # Préférer un exercice pas déjà dans le programme
    for _, ex in candidats:
        if ex[0].lower() not in exercices_existants:
            return {'nom': ex[0], 'volume': ex[1], 'muscle': ex[2]}

    # Sinon prendre le meilleur
    ex = candidats[0][1]
    return {'nom': ex[0], 'volume': ex[1], 'muscle': ex[2]}


# ══════════════════════════════════════════════════════════
# 8. SUIVI DE PROGRESSION
# ══════════════════════════════════════════════════════════

class SuiviProgression:

    def __init__(self, user_id='utilisateur'):
        self.user_id = user_id
        self.fichier = f'progressions/{user_id}_progression.json'
        self.donnees = self._charger()

    def _charger(self):
        if os.path.exists(self.fichier):
            with open(self.fichier, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'user_id':          self.user_id,
            'seances':          [],
            'poids':            [],
            'imc_historique':   [],
            'programme_actuel': None,
        }

    def sauvegarder(self):
        with open(self.fichier, 'w', encoding='utf-8') as f:
            json.dump(self.donnees, f, ensure_ascii=False, indent=2)

    def enregistrer_programme(self, programme):
        self.donnees['programme_actuel'] = programme
        self.donnees['date_debut']       = datetime.now().strftime('%d/%m/%Y')
        imc = programme.get('profil', {}).get('imc')
        if imc:
            self.donnees['imc_historique'].append({
                'date':      datetime.now().strftime('%d/%m/%Y'),
                'imc':       imc,
                'categorie': programme['profil'].get('categorie_imc'),
                'poids':     programme['profil'].get('poids_kg'),
            })
        self.sauvegarder()

    def enregistrer_seance(self, note=None, ressenti=None, duree=None):
        seance = {
            'date':      datetime.now().strftime('%d/%m/%Y %H:%M'),
            'note':      note,
            'ressenti':  ressenti,
            'duree_min': duree
        }
        self.donnees['seances'].append(seance)
        self.sauvegarder()
        return seance

    def enregistrer_poids(self, poids_kg):
        self.donnees['poids'].append({
            'date':   datetime.now().strftime('%d/%m/%Y'),
            'valeur': poids_kg
        })
        prog = self.donnees.get('programme_actuel')
        if prog:
            taille_cm = prog.get('profil', {}).get('taille_cm')
            if taille_cm:
                imc = round(poids_kg / (taille_cm / 100) ** 2, 1)
                self.donnees['imc_historique'].append({
                    'date':  datetime.now().strftime('%d/%m/%Y'),
                    'imc':   imc,
                    'poids': poids_kg,
                })
        self.sauvegarder()

    def get_stats(self):
        seances  = self.donnees['seances']
        poids    = self.donnees['poids']
        imc_hist = self.donnees.get('imc_historique', [])

        stats = {
            'total_seances':      len(seances),
            'ressenti_moyen':     None,
            'variation_poids':    None,
            'evolution_imc':      None,
            'jours_depuis_debut': None,
            'imc_historique':     imc_hist,
            'poids_historique':   poids,
            'seances_recentes':   seances[-5:],
        }

        if seances:
            r = [s['ressenti'] for s in seances if s.get('ressenti')]
            if r:
                stats['ressenti_moyen'] = round(sum(r) / len(r), 1)

        if len(poids) >= 2:
            stats['variation_poids'] = round(
                poids[-1]['valeur'] - poids[0]['valeur'], 1
            )

        if len(imc_hist) >= 2:
            stats['evolution_imc'] = round(
                imc_hist[-1]['imc'] - imc_hist[0]['imc'], 1
            )

        if self.donnees.get('date_debut'):
            debut = datetime.strptime(self.donnees['date_debut'], '%d/%m/%Y')
            stats['jours_depuis_debut'] = (datetime.now() - debut).days

        return stats

    def afficher_bilan(self):
        stats    = self.get_stats()
        imc_hist = self.donnees.get('imc_historique', [])
        lignes   = [
            "## 📊 Votre bilan de progression",
            "---",
            f"🏃 **Séances effectuées** : {stats['total_seances']}",
        ]
        if stats['jours_depuis_debut'] is not None:
            lignes.append(f"📅 **Jours depuis le début** : {stats['jours_depuis_debut']}")
        if stats['ressenti_moyen']:
            lignes.append(f"😊 **Ressenti moyen** : {stats['ressenti_moyen']}/5")
        if stats['variation_poids'] is not None:
            s = '+' if stats['variation_poids'] > 0 else ''
            lignes.append(f"⚖️ **Évolution poids** : {s}{stats['variation_poids']} kg")
        if stats['evolution_imc'] is not None:
            s = '+' if stats['evolution_imc'] > 0 else ''
            lignes.append(f"📏 **Évolution IMC** : {s}{stats['evolution_imc']}")
        if len(imc_hist) >= 2:
            lignes.append("\n**📈 Historique IMC :**")
            for e in imc_hist[-5:]:
                lignes.append(f"• {e['date']} : IMC {e['imc']}")
        if stats['total_seances'] == 0:
            lignes.append("\n⚠️ Aucune séance. Tapez 'j'ai fait ma séance' !")
        elif stats['total_seances'] >= 10:
            lignes.append("\n🏆 Excellent ! Très régulier !")
        elif stats['total_seances'] >= 5:
            lignes.append("\n💪 Bonne progression !")
        else:
            lignes.append("\n🌱 Bon départ !")
        return '\n'.join(lignes)


# ══════════════════════════════════════════════════════════
# 9. CLIENT OLLAMA
# ══════════════════════════════════════════════════════════

class OllamaClient:

    MODELES_PRIORITE = ['mistral', 'llama3', 'llama2', 'phi', 'gemma', 'qwen']

    def __init__(self, base_url='http://localhost:11434'):
        self.base_url   = base_url
        self.modele     = None
        self.disponible = False
        self.statut     = 'non vérifié'
        self._diagnostiquer()
        if self.disponible:
            self._prechauffer()

    def _diagnostiquer(self):
        try:
            with urllib.request.urlopen(
                f'{self.base_url}/api/tags', timeout=5
            ) as resp:
                data    = json.loads(resp.read().decode())
                modeles = [m['name'].split(':')[0] for m in data.get('models', [])]

                if not modeles:
                    self.statut = 'Ollama connecté mais aucun modèle installé'
                    return

                for m in self.MODELES_PRIORITE:
                    if m in modeles:
                        self.modele     = m
                        self.disponible = True
                        self.statut     = f'✅ IA connectée — modèle : {m}'
                        return

                self.modele     = modeles[0]
                self.disponible = True
                self.statut     = f'✅ IA connectée — modèle : {self.modele}'

        except urllib.error.URLError:
            self.statut = '⚠️ Ollama non démarré (lancez : ollama serve)'
        except Exception as e:
            self.statut = f'⚠️ Erreur Ollama : {e}'

    def _prechauffer(self):
        def warmup():
            try:
                self.generer("Bonjour", temperature=0.1)
                print(f'✅ Ollama préchauffé ({self.modele})')
            except Exception:
                pass
        threading.Thread(target=warmup, daemon=True).start()

    def generer(self, prompt, contexte_systeme=None, temperature=0.7):
        if not self.disponible:
            return None
        systeme = contexte_systeme or (
            "Tu es un coach sportif expert et bienveillant. "
            "Tu réponds en français, de façon concise et pratique. "
            "Maximum 5 phrases."
        )
        payload = {
            'model':  self.modele,
            'prompt': prompt,
            'system': systeme,
            'stream': False,
            'options': {'temperature': temperature, 'num_predict': 400}
        }
        try:
            data = json.dumps(payload).encode('utf-8')
            req  = urllib.request.Request(
                f'{self.base_url}/api/generate',
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=90) as resp:
                result = json.loads(resp.read().decode())
                return result.get('response', '').strip()
        except Exception as e:
            print(f'⚠️ Ollama erreur : {e}')
            return None

    def proposer_alternatif(self, exercice, profil):
        if not self.disponible:
            return None
        prompt = (
            f"Profil : objectif={profil.get('objectif_label','?')}, "
            f"niveau={profil.get('niveau_label','?')}, "
            f"IMC={profil.get('imc','?')} ({profil.get('categorie_imc','?')}), "
            f"blessures={profil.get('blessures_detail',[])}.\n\n"
            f"Donne un conseil court (2-3 phrases) sur comment bien exécuter "
            f"'{exercice}' en remplacement."
        )
        return self.generer(prompt)

    def repondre_question(self, question, profil, programme=None):
        if not self.disponible:
            return (
                "L'IA Ollama n'est pas disponible.\n"
                "Lancez Ollama avec : `ollama serve` puis `ollama pull mistral`"
            )
        contexte = (
            f"Profil : objectif={profil.get('objectif_label','?')}, "
            f"niveau={profil.get('niveau_label','?')}, "
            f"IMC={profil.get('imc','?')}.\n"
        )
        if programme:
            try:
                s1_exos = [
                    e['nom'] for e in
                    programme['semaines'][0]['seances'][0]['exercices'][:3]
                ]
                contexte += f"Programme : {', '.join(s1_exos)}.\n"
            except Exception:
                pass
        return (
            self.generer(f"{contexte}Question : {question}")
            or "Je n'ai pas pu répondre. Réessayez."
        )


# ══════════════════════════════════════════════════════════
# 10. EXPORT PDF
# ══════════════════════════════════════════════════════════

def generer_pdf(programme, nom_fichier=None):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib.colors import HexColor, white
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer,
            Table, TableStyle, HRFlowable
        )
        from reportlab.lib.enums import TA_CENTER
    except ImportError:
        return generer_pdf_txt(programme, nom_fichier)

    if not nom_fichier:
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        nom_fichier = f'programmes_pdf/programme_{ts}.pdf'

    doc = SimpleDocTemplate(
        nom_fichier, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )

    C_BLEU   = HexColor('#2196F3')
    C_VERT   = HexColor('#4CAF50')
    C_ORANGE = HexColor('#FF9800')
    C_GRIS   = HexColor('#f5f5f5')
    C_GRIS2  = HexColor('#eeeeee')

    styles = getSampleStyleSheet()
    s_titre = ParagraphStyle(
        'Titre', parent=styles['Title'],
        fontSize=20, textColor=C_BLEU, alignment=TA_CENTER, spaceAfter=4
    )
    s_sous = ParagraphStyle(
        'Sous', parent=styles['Normal'],
        fontSize=10, textColor=HexColor('#666'), alignment=TA_CENTER, spaceAfter=10
    )
    s_h2 = ParagraphStyle(
        'H2', parent=styles['Heading2'],
        fontSize=13, textColor=C_BLEU, spaceBefore=12, spaceAfter=4
    )
    s_h3 = ParagraphStyle(
        'H3', parent=styles['Heading3'],
        fontSize=11, textColor=HexColor('#333'), spaceBefore=8, spaceAfter=4
    )
    s_body = ParagraphStyle(
        'Body', parent=styles['Normal'], fontSize=10, spaceAfter=4
    )
    s_pied = ParagraphStyle(
        'Pied', parent=styles['Normal'],
        fontSize=9, textColor=HexColor('#888'), alignment=TA_CENTER
    )

    elems = []
    p     = programme['profil']

    elems.append(Paragraph("🏋️ Coach Sportif IA — Programme Personnalisé", s_titre))
    elems.append(Paragraph(
        f"Généré le {programme.get('date_creation','?')} "
        f"| Durée : {programme.get('duree','?')}",
        s_sous
    ))
    elems.append(HRFlowable(width="100%", thickness=2, color=C_BLEU, spaceAfter=10))

    elems.append(Paragraph("👤 Profil", s_h2))
    data_p = [['Paramètre', 'Valeur']]
    data_p.append(['🎯 Objectif',  p.get('objectif', '—')])
    data_p.append(['📊 Niveau',    p.get('niveau', '—')])
    data_p.append(['📅 Fréquence', f"{p.get('frequence', 3)} séances/sem"])
    if p.get('imc'):
        data_p.append([
            '📏 IMC',
            f"{p['imc']} ({p.get('categorie_imc','').replace('_',' ')})"
        ])
    if p.get('poids_kg'):
        data_p.append(['⚖️ Poids',  f"{p['poids_kg']} kg"])
    if p.get('taille_cm'):
        data_p.append(['📐 Taille', f"{p['taille_cm']} cm"])
    if p.get('blessures'):
        data_p.append(['⚠️ Blessures', ', '.join(p['blessures'])])

    t_p = Table(data_p, colWidths=[5*cm, 11*cm])
    t_p.setStyle(TableStyle([
        ('BACKGROUND',     (0, 0), (-1,  0), C_BLEU),
        ('TEXTCOLOR',      (0, 0), (-1,  0), white),
        ('FONTNAME',       (0, 0), (-1,  0), 'Helvetica-Bold'),
        ('FONTSIZE',       (0, 0), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [C_GRIS, white]),
        ('GRID',           (0, 0), (-1, -1), 0.5, C_GRIS2),
        ('PADDING',        (0, 0), (-1, -1), 8),
        ('ALIGN',          (0, 0), (-1, -1), 'LEFT'),
    ]))
    elems.append(t_p)
    elems.append(Spacer(1, 15))

    elems.append(Paragraph("📅 Programme d'entraînement", s_h2))
    for sem in programme.get('semaines', []):
        elems.append(Paragraph(f"Semaine {sem['numero']} — {sem['focus']}", s_h3))
        for seance in sem.get('seances', []):
            elems.append(Paragraph(
                f"🗓 {seance['jour']} <i>{seance.get('note','')}</i>", s_body
            ))
            data_e = [['Exercice', 'Volume', 'Muscle(s)']]
            for ex in seance.get('exercices', []):
                data_e.append([ex['nom'], ex['volume'], ex['muscle']])
            t_e = Table(data_e, colWidths=[6*cm, 3.5*cm, 6.5*cm])
            t_e.setStyle(TableStyle([
                ('BACKGROUND',     (0, 0), (-1,  0), C_VERT),
                ('TEXTCOLOR',      (0, 0), (-1,  0), white),
                ('FONTNAME',       (0, 0), (-1,  0), 'Helvetica-Bold'),
                ('FONTSIZE',       (0, 0), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#f0f9f0'), white]),
                ('GRID',           (0, 0), (-1, -1), 0.3, C_GRIS2),
                ('PADDING',        (0, 0), (-1, -1), 6),
                ('ALIGN',          (0, 0), (-1, -1), 'LEFT'),
            ]))
            elems.append(t_e)
            elems.append(Spacer(1, 5))
        elems.append(Spacer(1, 8))

    elems.append(HRFlowable(width="100%", thickness=1, color=C_ORANGE))
    elems.append(Paragraph("💡 Conseils", s_h2))
    for c in programme.get('conseils', []):
        elems.append(Paragraph(f"• {c}", s_body))
    elems.append(Spacer(1, 15))

    elems.append(Paragraph("📊 Tableau de suivi", s_h2))
    data_s = [['Semaine', 'Jour', '✓', 'Ressenti (1-5)', 'Notes']]
    for sem in programme.get('semaines', []):
        for seance in sem.get('seances', []):
            data_s.append([
                sem['titre'], seance['jour'], '☐', '__ /5',
                '________________________________'
            ])
    t_s = Table(data_s, colWidths=[2.5*cm, 2.5*cm, 1*cm, 3*cm, 7*cm])
    t_s.setStyle(TableStyle([
        ('BACKGROUND',     (0, 0), (-1,  0), C_ORANGE),
        ('TEXTCOLOR',      (0, 0), (-1,  0), white),
        ('FONTNAME',       (0, 0), (-1,  0), 'Helvetica-Bold'),
        ('FONTSIZE',       (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#fff8f0'), white]),
        ('GRID',           (0, 0), (-1, -1), 0.3, C_GRIS2),
        ('PADDING',        (0, 0), (-1, -1), 5),
        ('ALIGN',          (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN',          (4, 1), ( 4, -1), 'LEFT'),
    ]))
    elems.append(t_s)

    elems.append(Spacer(1, 20))
    elems.append(HRFlowable(width="100%", thickness=1, color=C_GRIS2))
    elems.append(Paragraph(
        "Coach Sportif IA — La régularité est la clé du succès 🏆", s_pied
    ))

    doc.build(elems)
    print(f'✅ PDF : {nom_fichier}')
    return nom_fichier


def generer_pdf_txt(programme, nom_fichier=None):
    if not nom_fichier:
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        nom_fichier = f'programmes_pdf/programme_{ts}.txt'
    with open(nom_fichier, 'w', encoding='utf-8') as f:
        f.write(formater_programme_texte(programme))
    return nom_fichier