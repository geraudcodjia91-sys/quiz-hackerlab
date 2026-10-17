# 🚀 Déploiement du Quiz Hacker Lab sur Vercel (gratuit)

Site : quiz de révision + cours PDF protégés par mot de passe.
Fonctionne 100 % sur le plan **Hobby (gratuit)** de Vercel.

---

## 1️⃣ Les mots de passe (à connaître)

| Qui | Mot de passe | Accès |
|-----|-------------|-------|
| 🎓 Étudiants | `hackerlab2026` | Quiz + lecture des cours PDF |
| 🧑‍🏫 Toi (admin) | `admin2026` | Tout + ajout / suppression des PDF |

➡️ Pour les changer : modifie `config.py` (en haut du fichier), puis repousse sur GitHub → Vercel se redéploie tout seul.

---

## 2️⃣ Les fichiers à mettre sur GitHub

Ouvre le dossier `quiz-hacker-lab/` et envoie **exactement** ces fichiers
(le dossier `api/` avec ses 6 fichiers doit garder sa structure) :

```
index.html
vercel.json
requirements.txt
.gitignore
config.py
session.py
storage.py
handlers.py
vwrap.py
server.py          (facultatif — sert pour tester en local)
api/login.py
api/logout.py
api/me.py
api/pdfs.py
api/pdfs/[name].py
api/upload.py
```

Ne PAS envoyer : le dossier `pdfs/` (il est exclu par `.gitignore`).

### Création du repo GitHub (5 min)
1. Va sur **github.com** → compte gratuit (crée-le si besoin)
2. Clique **+ → New repository** → nom : `quiz-hacker-lab` → **Create**
3. Sur la page du repo vide : **uploading an existing file**
4. **Glisse le CONTENU du dossier** `quiz-hacker-lab` (les fichiers, PAS le dossier lui-même) — le dossier `api/` peut être glissé tel quel
5. **Commit changes**

---

## 3️⃣ Déploiement sur Vercel (5 min)

1. Va sur **vercel.com** → **Sign Up** → **Continue with GitHub**
2. **Add New → Project** → choisis `quiz-hacker-lab`
3. Sur l'écran d'import :
   - Dans la section **Environment Variables**, ajoute :
     - Nom : `SESSION_SECRET` → Valeur :
       ```
       66c663cd206f05f12456afb2babbaadafab036940c22b150
       ```
   - (Framework : "Other" — rien d'autre à configurer)
4. Clique **Deploy** → 30 secondes → ✅

## 4️⃣ Créer le stockage PDF (Vercel Blob)

1. Dans Vercel, ouvre ton projet → onglet **Storage**
2. **Create store** → nom : `quiz-pdfs` → **Access : `private`** → Create
   - ⚠️ Choisis **private** : les PDF ne sont alors lisibles QUE via ton
     site (après connexion). Avec `public`, n'importe qui connaissant l'URL
     du fichier pourrait le télécharger sans mot de passe.
3. Redéploie une fois (menu ⋯ → **Redeploy**) pour que les fonctions voient le store.

## 5️⃣ C'est en ligne ! 🎉

Ton lien permanent : **`https://quiz-hacker-lab.vercel.app`**
(ou `https://<ton-nom-de-projet>.vercel.app`)

À envoyer aux élèves :

```
🔐 Quiz Hacker Lab :
https://quiz-hacker-lab.vercel.app

➡️ Entre ton nom + ce mot de passe :
hackerlab2026
```

- 📱 Fonctionne sur téléphone et PC, 24 h/24, 7 j/7
- 📚 Tes PDF restent **stockés sur Vercel** (ils ne disparaissent pas)
- ✏️ Ajouter / retirer un cours : connecte-toi avec `admin2026` → onglet **Cours PDF** → glisse tes fichiers
- 🔄 Modifier le site (questions, mots de passe, design) : change un fichier sur GitHub → Vercel republie automatiquement en ~30 s

---

## 🧩 Pourquoi le code a été réécrit pour Vercel

| Avant (sandbox) | Après (Vercel) | Pourquoi |
|---|---|---|
| `python server.py` qui tourne en continu | **Fonctions serverless** dans `api/` | Vercel ne fait pas tourner de serveur permanent |
| Sessions en mémoire | **Cookies signés (HMAC)** | Le serverless n'a pas de mémoire entre 2 requêtes |
| PDF dans un dossier local | **Vercel Blob** (store `private`) | Le disque du serverless est effacé à chaque requête |
| Upload en 1 fois | **Upload par morceaux de 3,5 Mo** | Limite Vercel : 4,5 Mo par requête |

Tout est testé : 20 tests automatisés (`tests/local_test.py`) + test HTTP complet.

## 🔧 Panne fréquentes

| Problème | Solution |
|---|---|
| Le lien Vercel n'ouvre rien | Vérifie que le repo contient bien `index.html` **à la racine** (pas dans un sous-dossier) |
| « Nom ou mot de passe incorrect » malgré le bon mdp | C'est le mdp de `config.py` qui compte — vérifie qu'il n'y a pas d'espace |
| Upload PDF qui échoue | Vérifie que le store Blob est bien **créé** (onglet Storage) et **private** |
| Je veux un sous-domaine perso | Settings → Domains (plan gratuit : 1 domaine `*.vercel.app` seulement) |
