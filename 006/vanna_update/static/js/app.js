// Main application script
import { ApiService } from '/static/js/api-service.js';
import { ChatUI } from '/static/js/chat-ui.js';
import { HistoryManager } from '/static/js/history-manager.js';
import { TrainingManager } from '/static/js/training-manager.js';

class VannaApp {
    constructor() {
        this.apiService = new ApiService();
        this.historyManager = new HistoryManager(this.apiService);
        this.trainingManager = new TrainingManager(this.apiService);
        this.chatUI = new ChatUI(
            this.apiService,
            this.historyManager,
            this.trainingManager,
            this.handleUserQuestion.bind(this),
            this.handleSuggestedQuestionClick.bind(this)
        );

        this.currentSessionId = null;
        this.darkMode = localStorage.getItem('darkMode') === 'true';

        this.init();
    }

    async init() {
        // Apply dark mode if enabled
        if (this.darkMode) {
            document.body.classList.add('dark-mode');
        }

        // Initialize UI
        this.chatUI.renderApp();

        // Load question history
        await this.historyManager.loadQuestionHistory();
        this.chatUI.updateHistoryList(this.historyManager.getHistory());

        // Listen for question loaded events
        document.addEventListener('questionLoaded', (event) => {
            this.loadQuestion(event.detail.id);
        });

        // Generate initial questions
        try {
            const suggestedQuestions = await this.apiService.generateQuestions();
            this.chatUI.displaySuggestedQuestions(suggestedQuestions);
        } catch (error) {
            console.error('加载初始问题失败:', error);
        }
    }

    async handleUserQuestion(question) {
        if (!question.trim()) return;

        // Display user message
        this.chatUI.addUserMessage(question);

        try {
            // Generate SQL
            this.chatUI.startAssistantResponse();
            const sqlResponse = await this.apiService.generateSQL(question);
            this.currentSessionId = sqlResponse.id;

            // Display SQL
            this.chatUI.updateAssistantResponse(
                `<div class="sql-result">
<div class="sql-copy-btn"><i class="fas fa-copy"></i></div>
<pre class="sql-code">${sqlResponse.text}</pre>
</div>

让我运行这个查询来获取您的答案...`
            );

            // Run SQL
            const dataResponse = await this.apiService.runSQL(this.currentSessionId);

            // Parse the data
            const data = JSON.parse(dataResponse.df);

            // Update the response with data
            this.chatUI.updateAssistantResponse(
                `<div class="sql-result">
<div class="sql-copy-btn"><i class="fas fa-copy"></i></div>
<pre class="sql-code">${sqlResponse.text}</pre>
</div>

以下是查询结果：`,
                data
            );

            // Generate visualization
            try {
                const figResponse = await this.apiService.generatePlotlyFigure(this.currentSessionId);
                if (figResponse && figResponse.fig) {
                    try {
                        const figData = JSON.parse(figResponse.fig);
                        this.chatUI.addVisualization(figData);
                    } catch (parseError) {
                        console.error('解析可视化数据失败:', parseError);
                    }
                } else {
                    console.warn('没有可视化数据返回');
                }
            } catch (error) {
                console.error('生成可视化图表失败:', error);
            }

            // Generate followup questions
            try {
                const followupResponse = await this.apiService.generateFollowupQuestions(this.currentSessionId);
                this.chatUI.displaySuggestedQuestions(followupResponse.questions);
            } catch (error) {
                console.error('Failed to generate followup questions:', error);
            }

            // Add to history
            this.historyManager.addToHistory({
                id: this.currentSessionId,
                question: question
            });
            this.chatUI.updateHistoryList(this.historyManager.getHistory());

        } catch (error) {
            console.error('处理问题时出错:', error);
            this.chatUI.showErrorMessage('抱歉，处理您的问题时出现错误。请重试。');
        }
    }

    async handleSuggestedQuestionClick(question) {
        // Set the question in the input field and submit
        this.chatUI.setInputValue(question);
        this.handleUserQuestion(question);
    }

    async loadQuestion(id) {
        try {
            const questionData = await this.apiService.loadQuestion(id);
            this.currentSessionId = questionData.id;

            // Clear chat and add the loaded conversation
            this.chatUI.clearChat();

            // Add user message
            this.chatUI.addUserMessage(questionData.question);

            // Add assistant message with SQL, data and visualization
            const data = JSON.parse(questionData.df);
            this.chatUI.addAssistantMessage(
                `<div class="sql-result">
<div class="sql-copy-btn"><i class="fas fa-copy"></i></div>
<pre class="sql-code">${questionData.sql}</pre>
</div>

以下是查询结果：`,
                data
            );

            // Add visualization if available
            if (questionData.fig) {
                const figData = JSON.parse(questionData.fig);
                this.chatUI.addVisualization(figData);
            }

            // Display followup questions if available
            if (questionData.followup_questions) {
                this.chatUI.displaySuggestedQuestions(questionData.followup_questions);
            }

        } catch (error) {
            console.error('加载问题失败:', error);
            this.chatUI.showErrorMessage('加载对话失败。请重试。');
        }
    }

    toggleDarkMode() {
        this.darkMode = !this.darkMode;
        document.body.classList.toggle('dark-mode', this.darkMode);
        localStorage.setItem('darkMode', this.darkMode);
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.vannaApp = new VannaApp();
});
