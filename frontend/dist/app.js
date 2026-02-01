/**
 * TengLaafi Chat Application
 * Main chat application with session management and enhanced UI
 */
import { SessionManager } from './session.js';
class TengLaafiChat {
    constructor() {
        this.API_URL = "/tenglaafi";
        this.HEALTH_CHECK_INTERVAL = 10000;
        this.loadingElement = null;
        this.loadingInterval = null;
        this.sessionManager = new SessionManager(this.API_URL);
        this.chatContainer = document.getElementById("chatContainer");
        this.messageInput = document.getElementById("messageInput");
        this.sendButton = document.getElementById("sendButton");
        this.statusIndicator = document.querySelector(".status-indicator");
        this.themeToggleBtn = document.getElementById("themeToggleBtn");
        // Sidebar elements
        this.sidebar = document.getElementById("conversationSidebar");
        this.sidebarOverlay = document.getElementById("sidebarOverlay");
        this.conversationList = document.getElementById("conversationList");
    }
    /**
     * Initialize the chat application
     */
    async init() {
        this.initTheme();
        this.setupEventListeners();
        this.setupSidebarEvents();
        await this.loadConversationHistory();
        await this.renderConversationList();
        this.checkBackendStatus();
        setInterval(() => this.checkBackendStatus(), this.HEALTH_CHECK_INTERVAL);
        console.log("TengLaafi Chat initialized");
    }
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        this.sendButton.addEventListener("click", () => this.handleSendMessage());
        this.messageInput.addEventListener("keypress", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                this.handleSendMessage();
            }
        });
        // Add new conversation button if it exists
        const newChatBtn = document.getElementById("newChatButton");
        if (newChatBtn) {
            newChatBtn.addEventListener("click", () => this.createNewConversation());
        }
        this.themeToggleBtn.addEventListener("click", () => this.toggleTheme());
        // Example queries
        this.setupExampleQueries();
    }
    /**
     * Setup example query buttons
     */
    setupExampleQueries() {
        const exampleBtns = document.querySelectorAll('.example-query-btn');
        exampleBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const query = btn.getAttribute('data-query');
                if (query) {
                    this.messageInput.value = query;
                    this.handleSendMessage();
                    this.hideExampleQueries();
                }
            });
        });
    }
    /**
     * Hide example queries (after first message)
     */
    hideExampleQueries() {
        const exampleQueries = document.getElementById('exampleQueries');
        if (exampleQueries) {
            exampleQueries.classList.add('hidden');
        }
    }
    /**
     * Show example queries (for new conversations)
     */
    showExampleQueries() {
        const exampleQueries = document.getElementById('exampleQueries');
        if (exampleQueries) {
            exampleQueries.classList.remove('hidden');
        }
    }
    /**
     * Setup sidebar event listeners
     */
    setupSidebarEvents() {
        // Menu toggle button
        const menuToggleBtn = document.getElementById("menuToggleBtn");
        if (menuToggleBtn) {
            menuToggleBtn.addEventListener("click", () => this.toggleSidebar());
        }
        // Close sidebar button
        const closeSidebarBtn = document.getElementById("closeSidebarBtn");
        if (closeSidebarBtn) {
            closeSidebarBtn.addEventListener("click", () => this.closeSidebar());
        }
        // Sidebar overlay (click to close)
        if (this.sidebarOverlay) {
            this.sidebarOverlay.addEventListener("click", () => this.closeSidebar());
        }
        // New chat button in sidebar
        const sidebarNewChatBtn = document.getElementById("sidebarNewChatBtn");
        if (sidebarNewChatBtn) {
            sidebarNewChatBtn.addEventListener("click", () => {
                this.createNewConversation();
                this.closeSidebar();
            });
        }
    }
    initTheme() {
        const saved = localStorage.getItem('tenglaafi-theme');
        if (saved === 'light') {
            document.documentElement.setAttribute('data-theme', 'light');
            this.updateHljsTheme('light');
        }
    }
    toggleTheme() {
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'light' ? 'dark' : 'light';
        if (next === 'light') {
            document.documentElement.setAttribute('data-theme', 'light');
        }
        else {
            document.documentElement.removeAttribute('data-theme');
        }
        this.updateHljsTheme(next);
        localStorage.setItem('tenglaafi-theme', next);
    }
    updateHljsTheme(theme) {
        const link = document.getElementById('hljsTheme');
        if (link) {
            const base = 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/';
            link.href = theme === 'light' ? base + 'github-light.min.css' : base + 'github-dark.min.css';
        }
    }
    /**
     * Toggle sidebar visibility
     */
    toggleSidebar() {
        this.sidebar.classList.toggle("open");
        this.sidebarOverlay.classList.toggle("active");
    }
    /**
     * Close sidebar
     */
    closeSidebar() {
        this.sidebar.classList.remove("open");
        this.sidebarOverlay.classList.remove("active");
    }
    /**
     * Render the conversation list in sidebar
     */
    async renderConversationList() {
        const sessions = await this.sessionManager.getAllSessions();
        const currentSessionId = this.sessionManager.getCurrentSessionId();
        if (sessions.length === 0) {
            this.conversationList.innerHTML = `
                <div class="conversation-empty">
                    <p>Aucune conversation</p>
                    <p>Commencez une nouvelle discussion!</p>
                </div>
            `;
            return;
        }
        // Sort by last_updated descending
        const sortedSessions = sessions.sort((a, b) => new Date(b.last_updated).getTime() - new Date(a.last_updated).getTime());
        this.conversationList.innerHTML = sortedSessions.map(session => {
            const isActive = session.session_id === currentSessionId;
            const title = this.generateConversationTitle(session.messages);
            const date = this.formatDate(session.last_updated);
            return `
                <div class="conversation-item ${isActive ? 'active' : ''}" data-session-id="${session.session_id}">
                    <div class="conversation-item-content" onclick="window.tengLaafiChat.switchToConversation('${session.session_id}')">
                        <div class="conversation-title">${title}</div>
                        <div class="conversation-date">${date}</div>
                    </div>
                    <button class="conversation-delete-btn" onclick="event.stopPropagation(); window.tengLaafiChat.deleteConversation('${session.session_id}')" title="Supprimer">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                        </svg>
                    </button>
                </div>
            `;
        }).join('');
    }
    /**
     * Generate a title for a conversation based on first user message
     */
    generateConversationTitle(messages) {
        const firstUserMessage = messages.find(m => m.role === 'user');
        if (firstUserMessage) {
            const content = firstUserMessage.content;
            return content.length > 35 ? content.substring(0, 35) + '...' : content;
        }
        return 'Nouvelle conversation';
    }
    /**
     * Format date for display
     */
    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        if (diffMins < 1)
            return "À l'instant";
        if (diffMins < 60)
            return `Il y a ${diffMins} min`;
        if (diffHours < 24)
            return `Il y a ${diffHours}h`;
        if (diffDays < 7)
            return `Il y a ${diffDays}j`;
        return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
    }
    /**
     * Switch to a different conversation
     */
    async switchToConversation(sessionId) {
        await this.sessionManager.switchSession(sessionId);
        this.chatContainer.innerHTML = '';
        await this.loadConversationHistory();
        await this.renderConversationList();
        this.closeSidebar();
    }
    /**
     * Delete a conversation
     */
    async deleteConversation(sessionId) {
        if (!confirm('Supprimer cette conversation ?'))
            return;
        await this.sessionManager.deleteSession(sessionId);
        this.chatContainer.innerHTML = '';
        await this.loadConversationHistory();
        await this.renderConversationList();
    }
    /**
     * Load conversation history from localStorage
     */
    async loadConversationHistory() {
        const history = await this.sessionManager.loadHistory();
        if (history.length === 0) {
            // Show welcome message if no history
            this.addMessage('Bonjour ! Je suis <strong>TengLaafi</strong>, votre assistant santé ancré dans les savoirs africains. ' +
                'Posez-moi une question par exemple sur le <em>paludisme</em>, l\'<em>Artemisia</em> ou tout autre sujet de santé tropicales et plantes médicinales.', 'bot', true);
            this.showExampleQueries();
            return;
        }
        // Hide example queries if there's history
        this.hideExampleQueries();
        history.forEach(message => {
            if (message.role === 'user') {
                this.addMessage(message.content, 'user');
            }
            else {
                const formatted = this.formatResponse(message.content);
                this.addMessage(formatted, 'bot', true);
                if (message.sources && message.sources.length > 0) {
                    this.renderSources(message.sources);
                }
            }
        });
    }
    /**
     * Check backend health status
     */
    async checkBackendStatus() {
        try {
            const response = await fetch(`${this.API_URL}/health`);
            if (!response.ok)
                throw new Error('Backend unavailable');
            this.statusIndicator.style.background = "#4CAF50";
            this.statusIndicator.title = "Backend: Connecté";
        }
        catch (error) {
            this.statusIndicator.style.background = "#d32f2f";
            this.statusIndicator.title = "Backend: Déconnecté";
        }
    }
    /**
     * Handle sending a message
     */
    async handleSendMessage() {
        const question = this.messageInput.value.trim();
        if (!question)
            return;
        // Add user message to UI
        this.addMessage(question, "user");
        this.messageInput.value = "";
        this.showLoadingIndicator();
        try {
            const request = {
                message: question,
                session_id: this.sessionManager.getCurrentSessionId(),
                top_k: 5,
                include_sources: true
            };
            const response = await fetch(`${this.API_URL}/query`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question: request.message, top_k: request.top_k })
            });
            if (!response.ok) {
                throw new Error(`Error: ${response.statusText}`);
            }
            const data = await response.json();
            this.hideLoadingIndicator();
            // Save user message to session
            await this.sessionManager.saveMessage({
                role: 'user',
                content: question,
                timestamp: new Date().toISOString()
            });
            // Process and display answer
            const answer = this.removeCitations(data.answer);
            const formatted = this.formatResponse(answer);
            this.addMessage(formatted, "bot", true);
            // Save assistant message to session
            await this.sessionManager.saveMessage({
                role: 'assistant',
                content: data.answer,
                timestamp: new Date().toISOString(),
                sources: data.sources
            });
            // Update conversation list (to show new title if first message)
            this.renderConversationList();
            // Display sources
            if (data.sources && data.sources.length > 0) {
                this.renderSources(data.sources);
            }
        }
        catch (error) {
            this.hideLoadingIndicator();
            console.error("Error sending message:", error);
            this.addMessage("Désolé, une erreur est survenue. Veuillez réessayer.", "bot error");
        }
    }
    /**
     * Remove citations from text
     */
    removeCitations(text) {
        return text.replace(/\[Document\s\d+\]|\(Document\s\d+\)|Document\s\d+/g, '').trim();
    }
    /**
     * Add a message to the chat container
     */
    addMessage(content, type, isHTML = false) {
        const messageElement = document.createElement("div");
        messageElement.className = `message ${type}`;
        if (isHTML) {
            messageElement.innerHTML = content;
            // Apply syntax highlighting to any code blocks
            this.highlightCodeBlocks(messageElement);
        }
        else {
            messageElement.textContent = content;
        }
        this.chatContainer.appendChild(messageElement);
        this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
        return messageElement;
    }
    /**
     * Show loading indicator with animated dots
     */
    showLoadingIndicator() {
        this.loadingElement = this.addMessage("TengLaafi réfléchit", "bot loading");
        let dotCount = 0;
        this.loadingInterval = window.setInterval(() => {
            dotCount = (dotCount + 1) % 4;
            if (this.loadingElement) {
                this.loadingElement.textContent = "TengLaafi réfléchit" + ".".repeat(dotCount);
            }
        }, 500);
    }
    /**
     * Hide loading indicator
     */
    hideLoadingIndicator() {
        if (this.loadingInterval !== null) {
            clearInterval(this.loadingInterval);
            this.loadingInterval = null;
        }
        if (this.loadingElement) {
            this.loadingElement.remove();
            this.loadingElement = null;
        }
    }
    /**
     * Format response text to HTML using marked.js for markdown
     */
    formatResponse(text) {
        if (!text)
            return "";
        try {
            // Configure marked for safe rendering
            if (typeof marked !== 'undefined') {
                marked.setOptions({
                    breaks: true,
                    gfm: true
                });
                const html = marked.parse(text);
                return `<div class="markdown-content">${html}</div>`;
            }
        }
        catch (e) {
            console.warn('Marked.js not available, using fallback formatting');
        }
        // Fallback formatting if marked is not available
        const lines = text.split('\n').filter(line => line.trim() !== '');
        let formattedHtml = '';
        let inList = false;
        lines.forEach(line => {
            const trimmedLine = line.trim();
            const listItemMatch = trimmedLine.match(/^(\d+[.)-]\s*)(.*)/);
            if (listItemMatch) {
                if (!inList) {
                    formattedHtml += '<ol>';
                    inList = true;
                }
                formattedHtml += `<li>${listItemMatch[2].trim()}</li>`;
            }
            else {
                if (inList) {
                    formattedHtml += '</ol>';
                    inList = false;
                }
                formattedHtml += `<p>${trimmedLine}</p>`;
            }
        });
        if (inList) {
            formattedHtml += '</ol>';
        }
        return formattedHtml;
    }
    /**
     * Apply syntax highlighting to code blocks
     */
    highlightCodeBlocks(element) {
        if (typeof hljs !== 'undefined') {
            element.querySelectorAll('pre code').forEach((block) => {
                hljs.highlightElement(block);
            });
        }
    }
    /**
     * Render sources as collapsible cards
     */
    renderSources(sources) {
        if (!sources || sources.length === 0)
            return;
        const sourceCards = sources.map((src) => {
            const sourceId = src.id || "N/A";
            const sourceTitle = src.title || "Source inconnue";
            const sourceUrl = src.url || "";
            const sourceType = src.source || "Document";
            const relevanceScore = src.relevance_score;
            // Determine source type icon and color
            const typeInfo = this.getSourceTypeInfo(sourceType);
            // Relevance badge
            const relevanceBadge = relevanceScore !== undefined
                ? `<span class="relevance-badge" style="background: ${this.getRelevanceColor(relevanceScore)}">${Math.round(relevanceScore * 100)}%</span>`
                : '';
            // View button if URL available
            const viewButton = sourceUrl && sourceUrl.startsWith('http')
                ? `<a href="${sourceUrl}" target="_blank" class="source-view-btn">Voir le document</a>`
                : '';
            return `
                <div class="source-card">
                    <div class="source-card-header" onclick="this.parentElement.classList.toggle('expanded')">
                        <div class="source-card-left">
                            <span class="source-type-badge" style="background: ${typeInfo.color}">${typeInfo.icon} ${typeInfo.label}</span>
                            <span class="source-title">${sourceTitle}</span>
                        </div>
                        <div class="source-card-right">
                            ${relevanceBadge}
                            <span class="source-expand-icon">▼</span>
                        </div>
                    </div>
                    <div class="source-card-content">
                        <div class="source-details">
                            <p><strong>ID:</strong> ${sourceId}</p>
                            <p><strong>Type:</strong> ${sourceType}</p>
                            ${relevanceScore !== undefined ? `<p><strong>Pertinence:</strong> ${Math.round(relevanceScore * 100)}%</p>` : ''}
                        </div>
                        ${viewButton}
                    </div>
                </div>`;
        }).join('');
        const sourcesContainer = `
            <div class="sources-container">
                <div class="sources-header" onclick="this.parentElement.classList.toggle('collapsed')">
                    <span class="sources-header-label">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:middle;margin-right:6px"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>
                        Sources consultées (${sources.length})
                    </span>
                    <span class="sources-toggle">▼</span>
                </div>
                <div class="sources-list">
                    ${sourceCards}
                </div>
            </div>`;
        this.addMessage(sourcesContainer, "source-group", true);
    }
    /**
     * Get source type info (icon, label, color)
     */
    getSourceTypeInfo(sourceType) {
        const svgBase = 'width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:middle;margin-right:4px"';
        const building = `<svg ${svgBase}><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 21h16.5M4.5 6.75h15m-15 10.5h15M5.25 6.75a2.25 2.25 0 002.25 2.25h9a2.25 2.25 0 002.25-2.25m-13.5 0a2.25 2.25 0 012.25-2.25h9a2.25 2.25 0 012.25 2.25m-9 8.25a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25h-.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z"/></svg>`;
        const book = `<svg ${svgBase}><path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>`;
        const doc = `<svg ${svgBase}><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.125A1.125 1.125 0 0114.25 7.125v-1.125a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"/></svg>`;
        const clipboard = `<svg ${svgBase}><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 10.5V6a3.75 3.75 0 10-7.5 0v4.5m11.356-1.993l1.263 12c.07.665-.45 1.243-1.119 1.243H4.25a1.125 1.125 0 01-1.12-1.243l1.264-12A1.125 1.125 0 015.513 7.5h12.974c.576 0 1.059.435 1.119 1.007z"/></svg>`;
        const type = sourceType.toLowerCase();
        if (type.includes('who') || type.includes('oms')) {
            return { icon: building, label: 'OMS/WHO', color: '#1976d2' };
        }
        else if (type.includes('pubmed') || type.includes('ncbi')) {
            return { icon: book, label: 'PubMed', color: '#7b1fa2' };
        }
        else if (type.includes('local') || type.includes('document')) {
            return { icon: doc, label: 'Local', color: '#388e3c' };
        }
        return { icon: clipboard, label: 'Source', color: '#757575' };
    }
    /**
     * Get color based on relevance score
     */
    getRelevanceColor(score) {
        if (score >= 0.8)
            return '#4caf50';
        if (score >= 0.6)
            return '#ff9800';
        return '#f44336';
    }
    /**
     * Create a new conversation
     */
    async createNewConversation() {
        this.sessionManager.createNewSession();
        this.chatContainer.innerHTML = '';
        // Add welcome message
        this.addMessage('Bonjour ! Je suis <strong>TengLaafi</strong>, votre assistant santé. Posez-moi une question.', 'bot', true);
        this.showExampleQueries();
        await this.renderConversationList();
    }
}
// Initialize on DOM load
const chat = new TengLaafiChat();
window.tengLaafiChat = chat;
document.addEventListener('DOMContentLoaded', () => chat.init());
//# sourceMappingURL=app.js.map