// History Manager Component
export class HistoryManager {
    constructor(apiService) {
        this.apiService = apiService;
        this.history = [];
    }
    
    async loadQuestionHistory() {
        try {
            this.history = await this.apiService.getQuestionHistory();
            return this.history;
        } catch (error) {
            console.error('Failed to load question history:', error);
            return [];
        }
    }
    
    getHistory() {
        return this.history;
    }
    
    addToHistory(item) {
        // Check if item already exists
        const existingIndex = this.history.findIndex(h => h.id === item.id);
        
        if (existingIndex !== -1) {
            // Remove existing item
            this.history.splice(existingIndex, 1);
        }
        
        // Add to the beginning of the array
        this.history.unshift(item);
        
        return this.history;
    }
    
    async loadQuestion(id) {
        try {
            const questionData = await this.apiService.loadQuestion(id);
            
            // Dispatch a custom event to notify the app
            const event = new CustomEvent('questionLoaded', { detail: questionData });
            document.dispatchEvent(event);
            
            return questionData;
        } catch (error) {
            console.error('Failed to load question:', error);
            throw error;
        }
    }
}
