import { Message, ConversationHistory } from './types';
export declare class SessionManager {
    private readonly DB_NAME;
    private readonly STORE_NAME;
    private readonly SESSION_KEY;
    private readonly DB_VERSION;
    private db;
    private currentSessionId;
    constructor(_apiUrl: string);
    private openDb;
    private generateSessionId;
    private getConversation;
    getCurrentSessionId(): string;
    createNewSession(): string;
    saveMessage(message: Message): Promise<void>;
    loadHistory(): Promise<Message[]>;
    getAllSessions(): Promise<ConversationHistory[]>;
    switchSession(sessionId: string): Promise<void>;
    deleteSession(sessionId: string): Promise<void>;
    clearAllSessions(): Promise<void>;
}
//# sourceMappingURL=session.d.ts.map