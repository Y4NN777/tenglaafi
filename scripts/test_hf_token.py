import os
import requests
from dotenv import load_dotenv
import time

# Charger les variables d'environnement
load_dotenv()

# Récupérer le token
token = os.getenv("HF_TOKEN")

print(f"🔍 Token chargé : {token[:10]}..." if token else "❌ ERREUR : Token non trouvé dans .env")

# Tester l'API Hugging Face
if token:
    # ✅ URL CORRECTE pour l'API Inference
    url = "https://router.huggingface.co/hf-inference/models/google/flan-t5-large"
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\n🧪 Test du modèle : google/flan-t5-large")
    print("⏳ Envoi de la requête...\n")
    
    response = requests.post(
        url,
        headers=headers,
        json={"inputs": "What are the symptoms of malaria?", "parameters": {"max_length": 150}}
    )
    
    print(f"📊 Status code : {response.status_code}")
    
    if response.status_code == 200:
        print("✅ SUCCESS : Token valide et modèle fonctionnel !")
        result = response.json()
        
        # flan-t5 renvoie une liste avec le texte généré
        if isinstance(result, list) and len(result) > 0:
            answer = result[0].get('generated_text', str(result[0]))
            print(f"📝 Réponse générée :\n{answer}\n")
            print("🎉 PARFAIT ! Ton setup HuggingFace fonctionne !")
            print("✅ Tu peux maintenant l'intégrer dans ton API")
        else:
            print(f"📝 Réponse brute : {result}")
            
    elif response.status_code == 401:
        print("❌ ERREUR 401 : Token invalide ou expiré")
        print(f"Détails : {response.text}")
        print("\n💡 Solution : Génère un nouveau token sur https://router.huggingface.co/hf-inference /settings/tokens")
        
    elif response.status_code == 403:
        print("⚠️ ERREUR 403 : Tu dois accepter la licence du modèle")
        print("👉 Va sur :https://router.huggingface.co/hf-inference /google/flan-t5-large")
        print("Clique sur 'Agree and access repository'")
        
    elif response.status_code == 503:
        print("⏳ ERREUR 503 : Le modèle est en cours de chargement")
        print("💡 Attends 20-30 secondes, c'est normal pour le premier appel\n")
        print("Réessai automatique dans 30 secondes...")
        
        time.sleep(30)
        
        # Deuxième tentative
        print("\n🔄 Nouvelle tentative...")
        response = requests.post(url, headers=headers, json={"inputs": "What are the symptoms of malaria?"})
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS après attente !")
            if isinstance(result, list) and len(result) > 0:
                print(f"📝 Réponse : {result[0].get('generated_text', result)}")
            print("\n🎉 Ton setup fonctionne maintenant !")
        else:
            print(f"❌ Toujours erreur {response.status_code}: {response.text[:200]}")
            
    else:
        print(f"⚠️ Erreur {response.status_code}")
        print(f"Détails : {response.text[:300]}")
        
else:
    print("❌ Impossible de tester : token manquant dans le fichier .env")