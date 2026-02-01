declare class TengLaafiChat {
    private readonly API_URL;
    private readonly HEALTH_CHECK_INTERVAL;
    private sessionManager;
    private chatContainer;
    private messageInput;
    private sendButton;
    private statusIndicator;
    private themeToggleBtn;
    private loadingElement;
    private loadingInterval;
    private sidebar;
    private sidebarOverlay;
    private conversationList;
    constructor();
    /**
     * Initialize the chat application
     */
    init(): Promise<void>;
    /**
     * Setup event listeners
     */
    private setupEventListeners;
    /**
     * Setup example query buttons
     */
    private setupExampleQueries;
    /**
     * Hide example queries (after first message)
     */
    private hideExampleQueries;
    /**
     * Show example queries (for new conversations)
     */
    private showExampleQueries;
    /**
     * Setup sidebar event listeners
     */
    private setupSidebarEvents;
    private initTheme;
    private toggleTheme;
    private updateHljsTheme;
    /**
     * Toggle sidebar visibility
     */
    private toggleSidebar;
    /**
     * Close sidebar
     */
    private closeSidebar;
    /**
     * Render the conversation list in sidebar
     */
    private renderConversationList;
    /**
     * Generate a title for a conversation based on first user message
     */
    private generateConversationTitle;
    /**
     * Format date for display
     */
    private formatDate;
    /**
     * Switch to a different conversation
     */
    switchToConversation(sessionId: string): Promise<void>;
    /**
     * Delete a conversation
     */
    deleteConversation(sessionId: string): Promise<void>;
    /**
     * Load conversation history from localStorage
     */
    private loadConversationHistory;
    /**
     * Check backend health status
     */
    private checkBackendStatus;
    /**
     * Handle sending a message
     */
    private handleSendMessage;
    /**
     * Remove citations from text
     */
    private removeCitations;
    /**
     * Add a message to the chat container
     */
    private addMessage;
    /**
     * Show loading indicator with animated dots
     */
    private showLoadingIndicator;
    /**
     * Hide loading indicator
     */
    private hideLoadingIndicator;
    /**
     * Format response text to HTML using marked.js for markdown
     */
    private formatResponse;
    /**
     * Apply syntax highlighting to code blocks
     */
    private highlightCodeBlocks;
    /**
     * Render sources as collapsible cards
     */
    private renderSources;
    /**
     * Get source type info (icon, label, color)
     */
    private getSourceTypeInfo;
    /**
     * Get color based on relevance score
     */
    private getRelevanceColor;
    /**
     * Create a new conversation
     */
    createNewConversation(): Promise<void>;
}
declare global {
    interface Window {
        tengLaafiChat: TengLaafiChat;
    }
}
export {};
//# sourceMappingURL=app.d.ts.map