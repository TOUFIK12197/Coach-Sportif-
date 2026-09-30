/* ============================================================
   chat.js — Coach Sportif IA
   ============================================================ */

let sessionId    = null;
let enAttente    = false;
let pdfUrl       = null;
let statsGlobales = {};

// ══════════════════════════════════════════════════════════
// INITIALISATION
// ══════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
  demarrerSession();
  verifierOllama();
  configurerSaisie();
});

async function demarrerSession() {
  try {
    const resp = await fetch('/api/session', { method: 'POST' });
    const data = await resp.json();

    sessionId = data.session_id;
    document.getElementById('session-label').textContent = `Session : ${sessionId}`;
    document.getElementById('loading-init').style.display = 'none';

    // Activer la saisie
    document.getElementById('msg-input').disabled   = false;
    document.getElementById('btn-envoyer').disabled = false;
    document.getElementById('msg-input').focus();

    // Afficher le message d'accueil
    afficherReponse(data.reponse);

    // Statut Ollama initial
    if (data.ollama) {
      mettreAJourOllama(data.ollama);
    }
  } catch (e) {
    document.getElementById('loading-init').innerHTML =
      '<p style="color:red">❌ Erreur de connexion au serveur</p>';
    console.error(e);
  }
}

function configurerSaisie() {
  const input = document.getElementById('msg-input');

  // Auto-resize textarea
  input.addEventListener('input', () => {
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 120) + 'px';
  });

  // Entrée = envoyer (Shift+Entrée = nouvelle ligne)
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      envoyerMessage();
    }
  });
}

// ══════════════════════════════════════════════════════════
// ENVOI DE MESSAGE
// ══════════════════════════════════════════════════════════

async function envoyerMessage(texteForce = null) {
  if (enAttente || !sessionId) return;

  const input = document.getElementById('msg-input');
  const texte = (texteForce || input.value).trim();
  if (!texte) return;

  input.value       = '';
  input.style.height = 'auto';

  // Afficher message utilisateur
  ajouterBulle('user', texte);
  cacherBoutonsRapides();

  // Indicateur de frappe
  const typingId = afficherTyping();
  enAttente = true;
  document.getElementById('btn-envoyer').disabled = true;

  try {
    const resp = await fetch('/api/chat', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ session_id: sessionId, message: texte })
    });

    if (resp.status === 404) {
      retirerTyping(typingId);
      await demarrerSession();
      return;
    }

    const data = await resp.json();
    retirerTyping(typingId);

    // Afficher réponse
    if (data.reponse) {
      afficherReponse(data.reponse, data.boutons || []);
    }

    // Mettre à jour l'interface
    if (data.profil)   mettreAJourProfil(data.profil);
    // Gérer le programme mis à jour
    if (data.programme_maj) {
      document.getElementById('btn-pdf').disabled = false;
    // Notification visuelle
      afficherNotification('✅ Programme mis à jour !', 'success');}

    // Gérer les boutons d'exercices proposés
    if (data.boutons && data.boutons.length > 0) {
      afficherBoutonsRapides(data.boutons);} 


    if (data.etat)     mettreAJourEtat(data.etat);
    if (data.stats)    mettreAJourStats(data.stats);
    if (data.pdf_url)  { pdfUrl = data.pdf_url; afficherModalPDF(data.pdf_url); }
    if (data.methode)  mettreAJourMethode(data.methode, data.confiance);

    // Activer bouton PDF si programme généré
    if (data.programme || data.pdf_url) {
      document.getElementById('btn-pdf').disabled = false;
    }

  } catch (e) {
    retirerTyping(typingId);
    ajouterBulle('bot', '⚠️ Erreur de connexion. Veuillez réessayer.');
    console.error(e);
  } finally {
    enAttente = false;
    document.getElementById('btn-envoyer').disabled = false;
    document.getElementById('msg-input').focus();
  }
}

// ══════════════════════════════════════════════════════════
// AFFICHAGE MESSAGES
// ══════════════════════════════════════════════════════════

function ajouterBulle(role, texte) {
  const zone   = document.getElementById('chat-messages');
  const heure  = new Date().toLocaleTimeString('fr-FR', {hour:'2-digit',minute:'2-digit'});
  const avatar = role === 'bot' ? '🏋️' : '👤';

  const wrapper = document.createElement('div');
  wrapper.className = `bulle-wrapper ${role}`;

  const html = markdownVersHTML(texte);

  wrapper.innerHTML = `
    <div class="bulle-avatar">${avatar}</div>
    <div>
      <div class="bulle">${html}</div>
      <div class="bulle-heure">${heure}</div>
    </div>
  `;
  zone.appendChild(wrapper);
  zone.scrollTop = zone.scrollHeight;
}

function afficherReponse(reponse, boutons = []) {
  if (typeof reponse === 'object' && reponse.texte) {
    ajouterBulle('bot', reponse.texte);
    if (reponse.boutons && reponse.boutons.length > 0) {
      afficherBoutonsRapides(reponse.boutons);
    }
  } else if (typeof reponse === 'string') {
    ajouterBulle('bot', reponse);
    if (boutons.length > 0) {
      afficherBoutonsRapides(boutons);
    }
  }
}

function afficherTyping() {
  const zone    = document.getElementById('chat-messages');
  const id      = 'typing-' + Date.now();
  const wrapper = document.createElement('div');
  wrapper.id        = id;
  wrapper.className = 'bulle-wrapper bot';
  wrapper.innerHTML = `
    <div class="bulle-avatar">🏋️</div>
    <div class="typing-indicator">
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
    </div>
  `;
  zone.appendChild(wrapper);
  zone.scrollTop = zone.scrollHeight;
  return id;
}

function retirerTyping(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

// ══════════════════════════════════════════════════════════
// BOUTONS RAPIDES
// ══════════════════════════════════════════════════════════

function afficherBoutonsRapides(boutons) {
  const zone = document.getElementById('boutons-rapides');
  zone.innerHTML = '';
  boutons.forEach(b => {
    const btn = document.createElement('button');
    btn.className   = 'btn-rapide';
    btn.textContent = b.label;
    btn.onclick     = () => envoyerMessage(b.value);
    zone.appendChild(btn);
  });
}

function cacherBoutonsRapides() {
  document.getElementById('boutons-rapides').innerHTML = '';
}

// ══════════════════════════════════════════════════════════
// MISE À JOUR PROFIL / SIDEBAR
// ══════════════════════════════════════════════════════════

function mettreAJourProfil(profil) {
  // Textes
  const set = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.textContent = val || '—';
  };
  set('val-objectif',   profil.objectif_label  || profil.objectif);
  set('val-niveau',     profil.niveau_label    || profil.niveau);
  set('val-frequence',  profil.frequence ? `${profil.frequence}x/semaine` : null);
  set('val-contraintes',
    profil.contraintes && profil.contraintes.length > 0
      ? profil.contraintes.map(c => c.replace('contrainte_','')).join(', ')
      : 'Aucune'
  );

  // IMC
  if (profil.imc) {
    const ficheImc = document.getElementById('fiche-imc');
    ficheImc.style.display = 'block';
    document.getElementById('imc-valeur').textContent = profil.imc;
    document.getElementById('imc-label').textContent  = `IMC — ${(profil.categorie_imc||'').replace('_',' ')}`;

    // Curseur IMC (plage 10-40)
    const pct    = Math.max(0, Math.min(100, ((profil.imc - 10) / 30) * 100));
    document.getElementById('imc-curseur').style.left = pct + '%';

    // Couleur valeur
    const couleurs = {
      maigreur:        '#2196F3',
      normal:          '#4CAF50',
      surpoids:        '#FF9800',
      obesite_moderee: '#F44336',
      obesite_severe:  '#B71C1C',
    };
    document.getElementById('imc-valeur').style.color =
      couleurs[profil.categorie_imc] || '#333';
  }

  // Piste athlétisme
  if (profil.frequence) {
    document.getElementById('piste-container').style.display = 'block';
  }
}

function mettreAJourStats(stats) {
  statsGlobales = stats;

  // Header stats
  const headerStats = document.getElementById('header-stats');
  headerStats.style.display = 'flex';
  document.getElementById('mini-seances').textContent = stats.total_seances || 0;
  document.getElementById('mini-jours').textContent   = stats.jours_depuis_debut || 0;

  // Piste athlétisme
  const nbSeances = stats.total_seances || 0;
  const pct       = Math.min(90, (nbSeances / 48) * 90); // 48 séances = programme 4 semaines
  document.getElementById('piste-coureur').style.left = `${5 + pct}%`;
  document.getElementById('piste-seances').textContent = `${nbSeances} séances`;
  document.getElementById('piste-jours').textContent   =
    stats.jours_depuis_debut ? `${stats.jours_depuis_debut}j` : '0j';
}

function mettreAJourEtat(etat) {
  document.querySelectorAll('.etat-item').forEach(el => {
    const e = el.dataset.etat;
    el.classList.remove('active', 'done');
    const ordre = ['imc','objectif','niveau','contraintes','frequence','suivi'];
    const idxCourant = ordre.indexOf(etat);
    const idxItem    = ordre.indexOf(e);
    if (e === etat)             el.classList.add('active');
    else if (idxItem < idxCourant) el.classList.add('done');
  });
}

function mettreAJourMethode(methode, confiance) {
  const el = document.getElementById('methode-detection');
  if (!el) return;
  const labels = { regles: '📏 Règles', ml: '🤖 ML', fallback: '❓ Fallback' };
  el.textContent = `${labels[methode] || methode} (${confiance}%)`;
}

// ══════════════════════════════════════════════════════════
// OLLAMA
// ══════════════════════════════════════════════════════════

function mettreAJourOllama(data) {
  const dot   = document.getElementById('ollama-dot');
  const texte = document.getElementById('ollama-texte');
  if (data.disponible) {
    dot.className   = 'badge-dot actif';
    texte.textContent = `IA : ${data.modele || 'connectée'}`;
  } else {
    dot.className   = 'badge-dot inactif';
    texte.textContent = 'IA non connectée';
  }
}

async function verifierOllama() {
  try {
    const resp = await fetch('/api/ollama/statut');
    const data = await resp.json();
    mettreAJourOllama(data);
  } catch (e) {
    console.log('Ollama non disponible');
  }
  // Re-vérifier toutes les 30 secondes
  setTimeout(verifierOllama, 30000);
}

// ══════════════════════════════════════════════════════════
// PDF
// ══════════════════════════════════════════════════════════

async function telechargerPDF() {
  if (!sessionId) return;
  const btn = document.getElementById('btn-pdf');
  btn.disabled     = true;
  btn.textContent  = '⏳ Génération...';

  try {
    const resp = await fetch('/api/chat', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ session_id: sessionId, message: 'télécharger mon programme' })
    });
    const data = await resp.json();
    if (data.pdf_url) {
      afficherModalPDF(data.pdf_url);
    } else if (data.reponse) {
      ajouterBulle('bot', data.reponse);
    }
  } catch (e) {
    ajouterBulle('bot', '⚠️ Erreur lors de la génération du PDF.');
  } finally {
    btn.disabled    = false;
    btn.textContent = '📄 Télécharger PDF';
  }
}

function afficherModalPDF(url) {
  pdfUrl = url;
  document.getElementById('pdf-link').href = url;
  document.getElementById('modal-pdf').style.display = 'flex';
}

function fermerModal() {
  document.getElementById('modal-pdf').style.display = 'none';
}

// ══════════════════════════════════════════════════════════
// NOUVELLE SESSION
// ══════════════════════════════════════════════════════════

async function nouvelleSession() {
  if (sessionId) {
    try {
      await fetch(`/api/reset/${sessionId}`, { method: 'POST' });
    } catch (e) {}
  }

  // Réinitialiser l'interface
  document.getElementById('chat-messages').innerHTML = `
    <div class="loading-init" id="loading-init">
      <div class="spinner"></div>
      <p>Démarrage...</p>
    </div>
  `;
  document.getElementById('boutons-rapides').innerHTML = '';
  document.getElementById('btn-pdf').disabled = true;
  document.getElementById('header-stats').style.display = 'none';
  document.getElementById('fiche-imc').style.display    = 'none';
  document.getElementById('piste-container').style.display = 'none';
  document.getElementById('val-objectif').textContent   = '—';
  document.getElementById('val-niveau').textContent     = '—';
  document.getElementById('val-frequence').textContent  = '—';
  document.getElementById('val-contraintes').textContent = '—';

  document.querySelectorAll('.etat-item').forEach(el => {
    el.classList.remove('active', 'done');
  });
  document.querySelector('[data-etat="imc"]').classList.add('active');

  sessionId = null;
  pdfUrl    = null;
  await demarrerSession();
}

// ══════════════════════════════════════════════════════════
// MARKDOWN → HTML (simple)
// ══════════════════════════════════════════════════════════

function markdownVersHTML(texte) {
  if (!texte) return '';

  return texte
    // Titres
    .replace(/^### (.+)$/gm,  '<h3>$1</h3>')
    .replace(/^## (.+)$/gm,   '<h2>$1</h2>')
    // Gras et italique
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g,     '<em>$1</em>')
    // Liens
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')
    // Listes
    .replace(/^• (.+)$/gm,    '<div style="margin:2px 0">• $1</div>')
    // Séparateurs
    .replace(/^---$/gm,        '<hr>')
    // Sauts de ligne
    .replace(/\n/g,            '<br>');
}
// Ajouter la fonction notification
function afficherNotification(message, type = 'info') {
    const couleurs = {
        success: '#4CAF50',
        warning: '#FF9800',
        error:   '#F44336',
        info:    '#2196F3',
    };

    const notif = document.createElement('div');
    notif.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${couleurs[type]};
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 600;
        z-index: 9999;
        animation: slideIn .3s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,.2);
    `;
    notif.textContent = message;
    document.body.appendChild(notif);

    setTimeout(() => {
        notif.style.opacity = '0';
        notif.style.transition = 'opacity .3s';
        setTimeout(() => notif.remove(), 300);
    }, 3000);
}