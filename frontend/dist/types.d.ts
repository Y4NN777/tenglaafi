export interface Message {
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
    sources?: Source[];
}
export interface Source {
    id: string;
    title: string;
    url?: string;
    source: string;
    relevance_score?: number;
}
export interface ChatRequest {
    message: string;
    session_id?: string;
    top_k?: number;
    include_sources?: boolean;
}
export interface ChatResponse {
    session_id: string;
    message: string;
    answer: string;
    sources: Source[];
    timestamp: string;
    processing_time: number;
}
export interface ConversationHistory {
    session_id: string;
    messages: Message[];
    created_at: string;
    last_updated: string;
}
//# sourceMappingURL=types.d.ts.map