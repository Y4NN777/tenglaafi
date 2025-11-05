// === Configuration ===
const API_URL = "http://127.0.0.1:8000/query";
const HEALTH_URL = "http://127.0.0.1:8000/health";

// === Sélecteurs ===
const chatContainer = document.getElementById("chatContainer");
const messageInput = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");
const statusIndicator = document.querySelector(".status-indicator");

// === Vérification du backend ===
async function checkBackend() {
    try {
        const res = await fetch(HEALTH_URL);
        if (res.ok) {
            statusIndicator.style.background = "#4CAF50";
            statusIndicator.title = "Backend: Connecté ";
        } else {
            throw new Error();
        }
    } catch {
        statusIndicator.style.background = "#d32f2f";
        statusIndicator.title = "Backend: Déconnecté ";
    }
}
checkBackend();
setInterval(checkBackend, 10000); // recheck toutes les 10s

// === Fonction d’envoi de message ===
async function sendMessage() {
    const question = messageInput.value.trim();
    if (!question) return;

    // Ajoute le message utilisateur
    addMessage(question, "user");
    messageInput.value = "";

    // Ajoute le message de chargement
    const loadingMessage = document.createElement("div");
    loadingMessage.className = "message bot loading";
    loadingMessage.textContent = "TengLaafi réfléchit";
    chatContainer.appendChild(loadingMessage);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    // Animation "..." en boucle
    let dotCount = 0;
    const loadingInterval = setInterval(() => {
        dotCount = (dotCount + 1) % 4;
        loadingMessage.textContent = "TengLaafi réfléchit" + ".".repeat(dotCount);
    }, 500);

    try {
        // Ici tu simules un temps minimal pour voir le loading
        await new Promise(res => setTimeout(res, 2500));

        const response = await fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question: question, top_k: 3 })
        });

        if (!response.ok) throw new Error("Erreur API");

        const data = await response.json();

        // Quand la réponse arrive, on arrête l'animation et supprime le message
        clearInterval(loadingInterval);
        loadingMessage.remove();

        const answer = data.answer || "Je n’ai pas trouvé de réponse précise à cette question.";
        addMessage(answer, "bot");

//          if (data.sources && data.sources.length > 0) {
//     data.sources.forEach(src => {
//         const sourceId = src.id || "N/A";
//         const sourceTitle = src.title || "Source inconnue";
//         const similarity = src.similarity ? `${Math.round(src.similarity * 100)}%` : "";
        
//         const sourceText = similarity 
//             ? ` [${sourceId}] ${sourceTitle} `
//             : ` [${sourceId}] ${sourceTitle}`;
        
//         addMessage(sourceText, "source");
//     });
// }
if (data.sources && data.sources.length > 0) {
            // Création d'un conteneur pour toutes les sources
            const sourcesContainer = document.createElement("div");
            sourcesContainer.className = "message source-group";
            sourcesContainer.innerHTML = "<strong> Sources consultées :</strong>";
            
            data.sources.forEach((src, index) => {
                const sourceId = src.id || "N/A";
                const sourceTitle = src.title || "Source inconnue";
                const similarity = src.similarity 
                    ? Math.round(src.similarity * 100) 
                    : 0;
                const sourceUrl = src.url || "";
                
                // Création d'un élément pour chaque source
                const sourceItem = document.createElement("div");
                sourceItem.className = "source-item";
                sourceItem.style.cssText = `
                    margin: 8px 0;
                    padding: 8px;
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 4px;
                    font-size: 0.9em;
                `;
                
                // Si l'URL existe et est valide, créer un lien
                if (sourceUrl && !sourceUrl.includes("data\\raw")) {
                    sourceItem.innerHTML = `
                        ${index + 1}. <a href="${sourceUrl}" target="_blank" style="color: #4CAF50; text-decoration: none;">
                            [${sourceId}] ${sourceTitle}
                        </a>
                        <span style="color: #888;"> )</span>
                    `;
                } else {
                    sourceItem.innerHTML = `
                        ${index + 1}. [${sourceId}] ${sourceTitle}
                        <span style="color: #888;"> QU)</span>
                    `;
                }
                
                sourcesContainer.appendChild(sourceItem);
            });
            
            chatContainer.appendChild(sourcesContainer);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

// ... (reste du code)

    } catch (error) {
        clearInterval(loadingInterval);
        loadingMessage.remove();
        console.error("Erreur:", error);
        addMessage("Erreur réseau : impossible de contacter le serveur.", "bot");
    }
}


// === Fonction pour ajouter un message ===
function addMessage(text, type, loading = false) {
    const message = document.createElement("div");
    message.className = `message ${type}`;
    message.textContent = text;
    if (loading) message.classList.add("loading");
    chatContainer.appendChild(message);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    return message;
}

// === Événements ===
sendButton.addEventListener("click", sendMessage);
messageInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendMessage();
});
