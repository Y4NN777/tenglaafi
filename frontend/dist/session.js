export class SessionManager {
    constructor(_apiUrl) {
        this.DB_NAME = 'tenglaafi_db';
        this.STORE_NAME = 'sessions';
        this.SESSION_KEY = 'tenglaafi_current_session';
        this.DB_VERSION = 1;
        this.db = null;
        this.currentSessionId =
            sessionStorage.getItem(this.SESSION_KEY) || this.generateSessionId();
    }
    // ── DB bootstrap ───────────────────────────────────────────────
    openDb() {
        if (this.db)
            return Promise.resolve(this.db);
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.DB_NAME, this.DB_VERSION);
            request.onupgradeneeded = () => {
                const db = request.result;
                if (!db.objectStoreNames.contains(this.STORE_NAME)) {
                    db.createObjectStore(this.STORE_NAME, { keyPath: 'session_id' });
                }
            };
            request.onsuccess = () => {
                this.db = request.result;
                resolve(this.db);
            };
            request.onerror = () => reject(request.error);
        });
    }
    // ── Helpers ────────────────────────────────────────────────────
    generateSessionId() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
            const r = (Math.random() * 16) | 0;
            const v = c === 'x' ? r : (r & 0x3) | 0x8;
            return v.toString(16);
        });
    }
    async getConversation(sessionId) {
        const db = await this.openDb();
        return new Promise((resolve, reject) => {
            const tx = db.transaction(this.STORE_NAME, 'readonly');
            const req = tx.objectStore(this.STORE_NAME).get(sessionId);
            req.onsuccess = () => resolve(req.result || null);
            req.onerror = () => reject(req.error);
        });
    }
    // ── Public API ─────────────────────────────────────────────────
    getCurrentSessionId() {
        return this.currentSessionId;
    }
    createNewSession() {
        this.currentSessionId = this.generateSessionId();
        sessionStorage.setItem(this.SESSION_KEY, this.currentSessionId);
        return this.currentSessionId;
    }
    async saveMessage(message) {
        const db = await this.openDb();
        const existing = await this.getConversation(this.currentSessionId);
        const now = new Date().toISOString();
        const conversation = existing || {
            session_id: this.currentSessionId,
            messages: [],
            created_at: now,
            last_updated: now,
        };
        conversation.messages.push(message);
        conversation.last_updated = now;
        // Cap at 10 messages per session
        if (conversation.messages.length > 10) {
            conversation.messages = conversation.messages.slice(-10);
        }
        return new Promise((resolve, reject) => {
            const tx = db.transaction(this.STORE_NAME, 'readwrite');
            const req = tx.objectStore(this.STORE_NAME).put(conversation);
            req.onsuccess = () => resolve();
            req.onerror = () => reject(req.error);
        });
    }
    async loadHistory() {
        const conversation = await this.getConversation(this.currentSessionId);
        return conversation ? conversation.messages : [];
    }
    async getAllSessions() {
        const db = await this.openDb();
        return new Promise((resolve, reject) => {
            const tx = db.transaction(this.STORE_NAME, 'readonly');
            const req = tx.objectStore(this.STORE_NAME).getAll();
            req.onsuccess = () => resolve(req.result);
            req.onerror = () => reject(req.error);
        });
    }
    async switchSession(sessionId) {
        const conversation = await this.getConversation(sessionId);
        if (conversation) {
            this.currentSessionId = sessionId;
            sessionStorage.setItem(this.SESSION_KEY, this.currentSessionId);
        }
    }
    async deleteSession(sessionId) {
        const db = await this.openDb();
        await new Promise((resolve, reject) => {
            const tx = db.transaction(this.STORE_NAME, 'readwrite');
            const req = tx.objectStore(this.STORE_NAME).delete(sessionId);
            req.onsuccess = () => resolve();
            req.onerror = () => reject(req.error);
        });
        if (this.currentSessionId === sessionId) {
            this.currentSessionId = this.generateSessionId();
            sessionStorage.setItem(this.SESSION_KEY, this.currentSessionId);
        }
    }
    async clearAllSessions() {
        const db = await this.openDb();
        await new Promise((resolve, reject) => {
            const tx = db.transaction(this.STORE_NAME, 'readwrite');
            const req = tx.objectStore(this.STORE_NAME).clear();
            req.onsuccess = () => resolve();
            req.onerror = () => reject(req.error);
        });
        this.currentSessionId = this.generateSessionId();
        sessionStorage.setItem(this.SESSION_KEY, this.currentSessionId);
    }
}
//# sourceMappingURL=session.js.map