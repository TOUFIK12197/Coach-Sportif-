# ============================================================
# app.py — Serveur Flask
# ============================================================

from flask import Flask, request, jsonify, render_template, send_file
import json
import os
import uuid
from datetime import datetime

from coach_engine import (
    INTENTS_DATA,
    charger_modele,
    classifier_message,
    extraire_entites,
    CoachDialogManager,
    SuiviProgression,
    OllamaClient,
    generer_programme,
    formater_programme_texte,
    generer_pdf,
    extraire_exercice_depuis_message,
    remplacer_exercice_dans_programme,
    trouver_exercice_alternatif,
)

app     = Flask(__name__)
modele  = charger_modele()
ollama  = OllamaClient()

# Stockage sessions en mémoire
sessions = {}


def get_session(session_id):
    if session_id not in sessions:
        sessions[session_id] = {
            'dialog':    CoachDialogManager(),
            'suivi':     SuiviProgression(session_id),
            'programme': None,
        }
    return sessions[session_id]


# ══════════════════════════════════════════════════════════
# ROUTES
# ══════════════════════════════════════════════════════════

@app.route('/')
def index():
    return render_template(
        'index.html',
        ollama_statut=ollama.statut,
        ollama_dispo=ollama.disponible
    )


@app.route('/api/session', methods=['POST'])
def nouvelle_session():
    session_id = str(uuid.uuid4())[:8]
    sess       = get_session(session_id)
    rep        = sess['dialog'].message_initial()
    return jsonify({
        'session_id': session_id,
        'reponse':    rep,
        'ollama': {
            'disponible': ollama.disponible,
            'statut':     ollama.statut
        }
    })


@app.route('/api/chat', methods=['POST'])
def chat():
    data       = request.get_json()
    session_id = data.get('session_id', '')
    message    = data.get('message', '').strip()

    if not message:
        return jsonify({'erreur': 'Message vide'}), 400

    if session_id not in sessions:
        return jsonify({'erreur': 'Session expirée'}), 404

    sess   = sessions[session_id]
    dialog = sess['dialog']
    suivi  = sess['suivi']

    # Classification en cascade
    intent_tag, _, methode, conf = classifier_message(message, modele)

    # NER
    entites = extraire_entites(message)

    # Machine à états
    rep    = dialog.traiter(message, intent_tag, entites)
    action = rep.get('action')

    # Initialisation
    reponse_finale = rep.get('texte', '')
    extra          = {}

    # ── Actions ──────────────────────────────────
    if action == 'generer_programme':
        prog = generer_programme(dialog.profil)
        sess['programme'] = prog
        suivi.enregistrer_programme(prog)

        ts   = datetime.now().strftime('%Y%m%d_%H%M%S')
        fich = f'data/programme_{session_id}_{ts}.json'
        with open(fich, 'w', encoding='utf-8') as f:
            json.dump(prog, f, ensure_ascii=False, indent=2)

        reponse_finale = formater_programme_texte(prog)
        dialog._transition('suivi')
        extra['programme'] = prog

    elif action == 'afficher_progression':
        reponse_finale = suivi.afficher_bilan()
        extra['stats'] = suivi.get_stats()

    elif action == 'enregistrer_seance':
        seance         = suivi.enregistrer_seance(note=message)
        stats          = suivi.get_stats()
        reponse_finale = (
            f"✅ Séance du {seance['date']} enregistrée ! "
            f"({stats['total_seances']} séances au total) 🎉\n"
            f"Super travail ! 💪"
        )
        if ollama.disponible:
            try:
                m = ollama.generer(
                    f"L'utilisateur a fait {stats['total_seances']} séances. "
                    f"Objectif : {dialog.profil.get('objectif_label','?')}. "
                    f"Message de motivation court (2 phrases max).",
                    temperature=0.9
                )
                if m:
                    reponse_finale += f"\n\n🤖 *{m}*"
            except Exception:
                pass
        extra['stats'] = stats

    elif action == 'telecharger_pdf':
        if sess.get('programme'):
            try:
                fich_pdf = generer_pdf(
                    sess['programme'],
                    f'programmes_pdf/programme_{session_id}.pdf'
                )
                reponse_finale = (
                    "✅ PDF généré !\n"
                    "📄 Cliquez sur le bouton **Télécharger PDF** "
                    "dans la barre latérale."
                )
                extra['pdf_url'] = f'/api/pdf/{session_id}'
            except Exception as e:
                reponse_finale = f"⚠️ Erreur PDF : {e}"
        else:
            reponse_finale = (
                "⚠️ Complétez d'abord le bilan pour "
                "générer un programme !"
            )

    elif action == 'rechercher_exercice_a_remplacer':
        programme = sess.get('programme')

        if not programme:
            dialog.attente_exercice_a_remplacer = False
            reponse_finale = (
                "⚠️ Vous n'avez pas encore de programme. "
                "Complétez d'abord le bilan !"
            )
        else:
            ex_trouve, s_idx, j_idx, e_idx = extraire_exercice_depuis_message(
                message, programme
            )

            if ex_trouve:
                nouvel_ex = trouver_exercice_alternatif(
                    ex_trouve, dialog.profil, programme
                )

                if nouvel_ex:
                    prog_modifie = remplacer_exercice_dans_programme(
                        programme, s_idx, j_idx, e_idx, nouvel_ex
                    )
                    sess['programme'] = prog_modifie
                    suivi.enregistrer_programme(prog_modifie)

                    ts   = datetime.now().strftime('%Y%m%d_%H%M%S')
                    fich = f'data/programme_{session_id}_{ts}.json'
                    with open(fich, 'w', encoding='utf-8') as f:
                        json.dump(prog_modifie, f, ensure_ascii=False, indent=2)

                    reponse_finale = (
                        f"✅ **'{ex_trouve['nom']}'** remplacé par "
                        f"**'{nouvel_ex['nom']}'** "
                        f"({nouvel_ex['volume']} — {nouvel_ex['muscle']})\n\n"
                        f"Appliqué dans **toutes les semaines** "
                        f"de votre programme.\n\n"
                        + formater_programme_texte(prog_modifie)
                    )

                    if ollama.disponible:
                        try:
                            conseil = ollama.proposer_alternatif(
                                nouvel_ex['nom'], dialog.profil
                            )
                            if conseil:
                                reponse_finale += f"\n\n💡 **Conseil IA :** {conseil}"
                        except Exception:
                            pass

                    dialog.attente_exercice_a_remplacer = False
                    extra['programme']     = prog_modifie
                    extra['programme_maj'] = True

                else:
                    reponse_finale = (
                        f"⚠️ Pas d'alternative trouvée pour "
                        f"**'{ex_trouve['nom']}'** avec votre profil.\n"
                        f"Voulez-vous essayer un autre exercice ?"
                    )
                    dialog.attente_exercice_a_remplacer = False

            else:
                # Exercice non trouvé → proposer la liste
                exercices_liste = []
                if programme.get('semaines'):
                    try:
                        seance1 = programme['semaines'][0]['seances'][0]
                        exercices_liste = [
                            ex['nom'] for ex in seance1['exercices']
                        ]
                    except Exception:
                        pass

                reponse_finale = (
                    "❓ Je n'ai pas trouvé cet exercice dans votre programme.\n\n"
                    "**Exercices disponibles :**\n"
                    + '\n'.join([f"• {ex}" for ex in exercices_liste])
                    + "\n\nCliquez sur un bouton ou tapez le nom exact."
                )
                extra['boutons'] = [
                    {'label': ex, 'value': f'remplacer {ex}'}
                    for ex in exercices_liste
                ]
                # Garder le mode attente actif

    elif action == 'ollama_question':
        reponse_ia     = ollama.repondre_question(
            message, dialog.profil, sess.get('programme')
        )
        reponse_finale = f"🤖 **Coach IA :**\n{reponse_ia}"

    elif action == 'fin':
        pass

    # ── Réponse finale ────────────────────────────
    response_data = {
        'reponse':   reponse_finale,
        'boutons':   extra.get('boutons', rep.get('boutons', [])),
        'etat':      dialog.etat,
        'profil':    dialog.profil,
        'intent':    intent_tag,
        'methode':   methode,
        'confiance': round(conf * 100, 1),
    }

    if extra.get('programme'):
        response_data['programme']     = extra['programme']
    if extra.get('programme_maj'):
        response_data['programme_maj'] = True
    if extra.get('pdf_url'):
        response_data['pdf_url']       = extra['pdf_url']
    if extra.get('stats'):
        response_data['stats']         = extra['stats']

    return jsonify(response_data)


@app.route('/api/pdf/<session_id>', methods=['GET'])
def telecharger_pdf(session_id):
    fich = f'programmes_pdf/programme_{session_id}.pdf'
    if os.path.exists(fich):
        return send_file(
            fich,
            as_attachment=True,
            download_name='mon_programme_sportif.pdf'
        )
    if session_id in sessions and sessions[session_id].get('programme'):
        try:
            generer_pdf(sessions[session_id]['programme'], fich)
            return send_file(
                fich,
                as_attachment=True,
                download_name='mon_programme_sportif.pdf'
            )
        except Exception as e:
            return jsonify({'erreur': str(e)}), 500
    return jsonify({'erreur': 'Programme non trouvé'}), 404


@app.route('/api/progression/<session_id>', methods=['GET'])
def get_progression(session_id):
    if session_id not in sessions:
        return jsonify({'erreur': 'Session introuvable'}), 404
    return jsonify(sessions[session_id]['suivi'].get_stats())


@app.route('/api/poids', methods=['POST'])
def enregistrer_poids():
    data       = request.get_json()
    session_id = data.get('session_id', '')
    poids      = data.get('poids_kg')
    if session_id not in sessions or not poids:
        return jsonify({'erreur': 'Données manquantes'}), 400
    sessions[session_id]['suivi'].enregistrer_poids(float(poids))
    return jsonify({
        'ok':    True,
        'stats': sessions[session_id]['suivi'].get_stats()
    })


@app.route('/api/ollama/statut', methods=['GET'])
def ollama_statut():
    ollama._diagnostiquer()
    return jsonify({
        'disponible': ollama.disponible,
        'statut':     ollama.statut,
        'modele':     ollama.modele
    })


@app.route('/api/reset/<session_id>', methods=['POST'])
def reset_session(session_id):
    if session_id in sessions:
        del sessions[session_id]
    sess = get_session(session_id)
    rep  = sess['dialog'].message_initial()
    return jsonify({'reponse': rep, 'etat': 'imc'})


if __name__ == '__main__':
    print('🚀 Coach Sportif IA — Démarrage...')
    print(f'   Modèle ML : models/modele_coach.pkl')
    print(f'   Ollama    : {ollama.statut}')
    print('   URL       : http://localhost:5000')
    app.run(debug=True, port=5000)