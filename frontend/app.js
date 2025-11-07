/**
 * Module pour gérer le chat de TengLaafi.
 * Utilise un IIFE (Immediately Invoked Function Expression) pour éviter de polluer l'espace de noms global.
 */
const TengLaafiChat = (() => {
    // === Configuration ===
    const API_URL = "https://tenglaafi-chat.y7-solutions.online";
    const HEALTH_URL = "https://tenglaafi-chat.y7-solutions.online/health";
    const HEALTH_CHECK_INTERVAL = 10000; // 10 secondes

    // === Sélecteurs DOM ===
    const chatContainer = document.getElementById("chatContainer");
    const messageInput = document.getElementById("messageInput");
    const sendButton = document.getElementById("sendButton");
    const statusIndicator = document.querySelector(".status-indicator");

    // === Variables d'état ===
    let loadingInterval = null;
    let loadingMessageElement = null;

    /**
     * Supprime les citations de type [Document X] ou (Document Y) ou Document Z du texte.
     * @param {string} text - Le texte potentiellement contenant des citations.
     * @returns {string} - Le texte sans les citations.
     */
    const removeCitations = (text) => {
        // Regex pour capturer [Document X], (Document 123), Document 123, etc.
        // où X est un chiffre.
        // \[(?:Document\s\d+)\]  -> [Document 123]
        // \((?:Document\s\d+)\)  -> (Document 123)
        // Document\s\d+         -> Document 123 (sans parenthèses)
        return text.replace(/\[Document\s\d+\]|\(Document\s\d+\)|Document\s\d+/g, '').trim();
    };

    /**
     * Formate la réponse du bot pour une meilleure lisibilité.
     * Convertit les listes numérotées et les paragraphes en HTML.
     * @param {string} text - La réponse brute du bot.
     * @returns {string} - La réponse formatée en HTML.
     */
    const formatResponse = (text) => {
        if (!text) return "";

        // Diviser le texte en lignes pour analyser les listes et les paragraphes
        const lines = text.split('\n').filter(line => line.trim() !== '');
        let formattedHtml = '';
        let inList = false;

        lines.forEach(line => {
            const trimmedLine = line.trim();
            // Détecter les éléments de liste numérotés
            const listItemMatch = trimmedLine.match(/^(\d+[.)-]\s*)(.*)/);

            if (listItemMatch) {
                if (!inList) {
                    formattedHtml += '<ol>';
                    inList = true;
                }
                // Enlever le préfixe de numérotation pour la liste HTML
                formattedHtml += `<li>${listItemMatch[2].trim()}</li>`;
            } else {
                if (inList) {
                    formattedHtml += '</ol>';
                    inList = false;
                }
                // Traiter comme un paragraphe
                formattedHtml += `<p>${trimmedLine}</p>`;
            }
        });

        if (inList) {
            formattedHtml += '</ol>';
        }

        return formattedHtml;
    };


    /**
     * Vérifie périodiquement la disponibilité du backend.
     */
    const checkBackendStatus = async () => {
        try {
            const response = await fetch(HEALTH_URL);
            if (!response.ok) throw new Error('Backend non disponible');
            
            statusIndicator.style.background = "#4CAF50";
            statusIndicator.title = "Backend: Connecté";
        } catch (error) {
            statusIndicator.style.background = "#d32f2f";
            statusIndicator.title = "Backend: Déconnecté";
            // Pas besoin de spammer la console si le backend est juste down.
            // console.error("Erreur de connexion au backend:", error);
        }
    };

    /**
     * Ajoute un message au conteneur de chat.
     * @param {string} content - Le contenu du message (texte brut ou HTML).
     * @param {string} type - Le type de message ('user', 'bot', 'source-group', etc.).
     * @param {boolean} isHTML - Si true, le contenu sera traité comme du HTML.
     * @returns {HTMLElement} - L'élément de message créé.
     */
    const addMessage = (content, type, isHTML = false) => {
        const messageElement = document.createElement("div");
        messageElement.className = `message ${type}`;
        
        if (isHTML) {
            messageElement.innerHTML = content;
        } else {
            messageElement.textContent = content;
        }
        
        chatContainer.appendChild(messageElement);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        return messageElement;
    };

    /**
     * Affiche un indicateur de chargement.
     */
    const showLoadingIndicator = () => {
        loadingMessageElement = addMessage("TengLaafi réfléchit", "bot loading");
        
        let dotCount = 0;
        loadingInterval = setInterval(() => {
            dotCount = (dotCount + 1) % 4;
            loadingMessageElement.textContent = "TengLaafi réfléchit" + ".".repeat(dotCount);
        }, 500);
    };

    /**
     * Masque l'indicateur de chargement.
     */
    const hideLoadingIndicator = () => {
        if (loadingInterval) clearInterval(loadingInterval);
        if (loadingMessageElement) loadingMessageElement.remove();
        loadingInterval = null;
        loadingMessageElement = null;
    };
    
    /**
     * Crée et affiche la section des sources.
     * @param {Array} sources - La liste des sources retournée par l'API.
     */
    const renderSources = (sources) => {
        if (!sources || sources.length === 0) return;

        const sourcesHeader = "<strong>Sources consultées :</strong>";
        const sourcesList = sources.map((src, index) => {
            const sourceId = src.id || "N/A";
            const sourceTitle = src.title || "Source inconnue";
            const sourceUrl = src.url || "";
            
            let sourceHTML;
            // Ne pas afficher de lien pour les sources locales (chemin de fichier)
            if (sourceUrl && sourceUrl.startsWith('http')) {
                sourceHTML = `
                    <div class="source-item">
                        ${index + 1}. <a href="${sourceUrl}" target="_blank" class="source-link">
                            [${sourceId}] ${sourceTitle}
                        </a>
                    </div>`;
            } else {
                sourceHTML = `<div class="source-item">${index + 1}. [${sourceId}] ${sourceTitle}</div>`;
            }
            return sourceHTML;
        }).join('');

        addMessage(sourcesHeader + sourcesList, "source-group", true);
    };

    /**
     * Gère l'envoi d'un message par l'utilisateur.
     */
    const handleSendMessage = async () => {
        const question = messageInput.value.trim();
        if (!question) return;

        addMessage(question, "user");
        messageInput.value = "";
        showLoadingIndicator();

        try {
            const response = await fetch(`${API_URL}/query`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question, top_k: 3 }),
            });

            if (!response.ok) throw new Error(`Erreur API: ${response.statusText}`);

            const data = await response.json();
            
            hideLoadingIndicator();

            let answer = data.answer || "Je n’ai pas trouvé de réponse précise à cette question.";
            answer = removeCitations(answer); // Supprime les citations du texte de la réponse
            answer = formatResponse(answer); // Formate la réponse pour l'affichage
            addMessage(answer, "bot", true); // On suppose que la réponse peut contenir du HTML
            
            renderSources(data.sources);

        } catch (error) {
            hideLoadingIndicator();
            console.error("Erreur lors de l'envoi du message:", error);
            addMessage("Désolé, une erreur de communication avec le serveur est survenue. Veuillez réessayer.", "bot error");
        }
    };
    
    /**
     * Initialise les gestionnaires d'événements et les vérifications périodiques.
     */
    const init = () => {
        sendButton.addEventListener("click", handleSendMessage);
        messageInput.addEventListener("keypress", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault(); // Empêche le retour à la ligne
                handleSendMessage();
            }
        });

        checkBackendStatus();
        setInterval(checkBackendStatus, HEALTH_CHECK_INTERVAL);
        
        console.log("TengLaafi Chat initialisé.");
    };

    // Expose la méthode d'initialisation
    return {
        init,
    };
})();

// Initialise le module de chat lorsque le DOM est entièrement chargé.
document.addEventListener('DOMContentLoaded', TengLaafiChat.init);
