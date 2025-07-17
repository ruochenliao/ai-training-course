// Chat UI Component
// Make sure hljs is available globally
// We'll check for hljs before using it
export class ChatUI {
    constructor(apiService, historyManager, trainingManager, onQuestionSubmit, onSuggestedQuestionClick) {
        this.apiService = apiService;
        this.historyManager = historyManager;
        this.trainingManager = trainingManager;
        this.onQuestionSubmit = onQuestionSubmit;
        this.onSuggestedQuestionClick = onSuggestedQuestionClick;

        this.currentAssistantMessageId = null;
        this.isSidebarOpen = false;
    }

    renderApp() {
        const appContainer = document.getElementById('app');
        appContainer.innerHTML = `
            <div class="app-container">
                <div class="sidebar">
                    <div class="sidebar-header">
                        <div class="logo">
                            <i class="fas fa-database"></i>
                            <span>Vanna Text2SQL</span>
                        </div>
                    </div>
                    <button class="new-chat-btn" id="new-chat-btn">
                        <i class="fas fa-plus"></i>
                        <span>新建聊天</span>
                    </button>
                    <div class="history-list" id="history-list">
                        <!-- History items will be added here -->
                    </div>
                    <div class="sidebar-footer">
                        <div class="sidebar-footer-item" id="training-data-btn">
                            <i class="fas fa-graduation-cap"></i>
                            <span>训练数据</span>
                        </div>
                        <div class="sidebar-footer-item" id="toggle-theme-btn">
                            <i class="fas fa-moon"></i>
                            <span>切换暗黑模式</span>
                        </div>
                    </div>
                </div>
                <div class="main-content">
                    <div class="chat-header">
                        <div class="chat-title">Text2SQL 助手</div>
                        <div class="header-actions">
                            <button class="header-btn" id="sidebar-toggle">
                                <i class="fas fa-bars"></i>
                            </button>
                        </div>
                    </div>
                    <div class="chat-container" id="chat-container">
                        <div class="message-container" id="message-container">
                            <!-- Welcome screen -->
                            <div class="welcome-screen" id="welcome-screen">
                                <div class="welcome-logo">
                                    <i class="fas fa-database" style="font-size: 64px; color: var(--primary-color);"></i>
                                </div>
                                <h1 class="welcome-title">欢迎使用 Vanna Text2SQL</h1>
                                <p class="welcome-subtitle">
                                    用自然语言提问关于您数据的问题，我将把它们转换成SQL查询和可视化图表。
                                </p>
                                <div class="example-queries" id="example-queries">
                                    <!-- Example queries will be added here -->
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="input-container">
                        <div class="input-box">
                            <textarea
                                class="input-field"
                                id="input-field"
                                placeholder="请输入关于您数据的问题..."
                                rows="1"
                            ></textarea>
                            <div class="input-actions">
                                <button class="input-action-btn send-btn" id="send-btn" disabled>
                                    <i class="fas fa-paper-plane"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Training Data Modal -->
            <div class="modal-overlay" id="training-modal" style="display: none;">
                <div class="modal-container">
                    <div class="modal-header">
                        <div class="modal-title">训练数据管理</div>
                        <button class="modal-close-btn" id="close-training-modal">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="modal-body">
                        <div class="training-tabs">
                            <button class="training-tab active" id="view-tab">查看训练数据</button>
                            <button class="training-tab" id="add-tab">添加训练数据</button>
                        </div>

                        <div class="training-content" id="view-content">
                            <div id="training-data-container">
                                <!-- Training data will be loaded here -->
                                <div style="display: flex; justify-content: center; padding: 40px 0;">
                                    <div style="display: flex; flex-direction: column; align-items: center;">
                                        <div style="width: 48px; height: 48px; margin-bottom: 16px;">
                                            <div class="typing-indicator" style="justify-content: center;">
                                                <div class="typing-dot"></div>
                                                <div class="typing-dot"></div>
                                                <div class="typing-dot"></div>
                                            </div>
                                        </div>
                                        <p>正在加载训练数据...</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="training-content" id="add-content" style="display: none;">
                            <div class="training-sections">
                                <!-- 问题和SQL查询部分 -->
                                <div class="training-section" id="question-sql-section">
                                    <div class="training-section-header">
                                        <h3>问题和SQL查询</h3>
                                        <p class="training-section-description">添加自然语言问题及其对应的SQL查询</p>
                                    </div>
                                    <form class="training-form" id="question-sql-form">
                                        <div class="form-group">
                                            <label class="form-label" for="question-input">问题</label>
                                            <input type="text" class="form-input" id="question-input" placeholder="输入自然语言问题">
                                            <div class="form-hint">示例：“显示按收入排名前10的客户”</div>
                                        </div>
                                        <div class="form-group">
                                            <label class="form-label" for="sql-input">SQL 查询</label>
                                            <textarea class="form-input" id="sql-input" placeholder="输入相应的SQL查询"></textarea>
                                            <div class="form-hint">示例： SELECT c.name, SUM(o.amount) AS revenue FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.name ORDER BY revenue DESC LIMIT 10</div>
                                        </div>
                                        <div class="form-actions">
                                            <button type="button" class="modal-btn modal-btn-primary" id="save-question-sql-btn">保存问题和SQL</button>
                                        </div>
                                    </form>
                                </div>

                                <!-- 表结构定义部分 -->
                                <div class="training-section" id="ddl-section">
                                    <div class="training-section-header">
                                        <h3>表结构定义</h3>
                                        <p class="training-section-description">添加数据库表结构定义</p>
                                    </div>
                                    <form class="training-form" id="ddl-form">
                                        <div class="form-group">
                                            <label class="form-label" for="ddl-input">表结构定义</label>
                                            <textarea class="form-input" id="ddl-input" placeholder="输入表定义" rows="8"></textarea>
                                            <div class="form-hint">示例： CREATE TABLE customers (id INT, name VARCHAR(100)); CREATE TABLE orders (id INT, customer_id INT, amount DECIMAL(10,2));</div>
                                        </div>
                                        <div class="form-actions">
                                            <button type="button" class="modal-btn modal-btn-primary" id="save-ddl-btn">保存表结构</button>
                                        </div>
                                    </form>
                                </div>

                                <!-- 文档说明部分 -->
                                <div class="training-section" id="documentation-section">
                                    <div class="training-section-header">
                                        <h3>文档说明</h3>
                                        <p class="training-section-description">添加数据模型或查询的说明文档</p>
                                    </div>
                                    <form class="training-form" id="documentation-form">
                                        <div class="form-group">
                                            <label class="form-label" for="documentation-input">文档说明</label>
                                            <textarea class="form-input" id="documentation-input" placeholder="输入文档说明" rows="8"></textarea>
                                            <div class="form-hint">关于数据模型或查询的任何额外上下文或解释</div>
                                        </div>
                                        <div class="form-actions">
                                            <button type="button" class="modal-btn modal-btn-primary" id="save-documentation-btn">保存文档</button>
                                        </div>
                                    </form>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="modal-btn modal-btn-secondary" id="cancel-training-btn">关闭</button>
                    </div>
                </div>
            </div>
        `;

        this.setupEventListeners();
        this.adjustTextareaHeight();
    }

    setupEventListeners() {
        // Input field
        const inputField = document.getElementById('input-field');
        const sendBtn = document.getElementById('send-btn');

        inputField.addEventListener('input', () => {
            sendBtn.disabled = !inputField.value.trim();
            this.adjustTextareaHeight();
        });

        inputField.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (!sendBtn.disabled) {
                    this.handleSendMessage();
                }
            }
        });

        sendBtn.addEventListener('click', () => {
            this.handleSendMessage();
        });

        // New chat button
        document.getElementById('new-chat-btn').addEventListener('click', () => {
            this.clearChat();
            this.showWelcomeScreen();

            // Generate initial questions
            this.apiService.generateQuestions()
                .then(questions => {
                    this.displaySuggestedQuestions(questions);
                })
                .catch(error => {
                    console.error('Failed to load initial questions:', error);
                });
        });

        // Sidebar toggle
        document.getElementById('sidebar-toggle').addEventListener('click', () => {
            this.toggleSidebar();
        });

        // Theme toggle
        document.getElementById('toggle-theme-btn').addEventListener('click', () => {
            document.body.classList.toggle('dark-mode');
            const isDarkMode = document.body.classList.contains('dark-mode');
            localStorage.setItem('darkMode', isDarkMode);

            // Update icon
            const themeIcon = document.querySelector('#toggle-theme-btn i');
            themeIcon.className = isDarkMode ? 'fas fa-sun' : 'fas fa-moon';
        });

        // Training data modal
        document.getElementById('training-data-btn').addEventListener('click', () => {
            this.showTrainingModal();
        });

        document.getElementById('close-training-modal').addEventListener('click', () => {
            this.hideTrainingModal();
        });

        document.getElementById('cancel-training-btn').addEventListener('click', () => {
            this.hideTrainingModal();
        });

        document.getElementById('save-question-sql-btn').addEventListener('click', () => {
            this.saveQuestionSql();
        });

        document.getElementById('save-ddl-btn').addEventListener('click', () => {
            this.saveDdl();
        });

        document.getElementById('save-documentation-btn').addEventListener('click', () => {
            this.saveDocumentation();
        });

        // Training tabs
        document.getElementById('view-tab').addEventListener('click', () => {
            this.switchTrainingTab('view');
        });

        document.getElementById('add-tab').addEventListener('click', () => {
            this.switchTrainingTab('add');
        });
    }

    handleSendMessage() {
        const inputField = document.getElementById('input-field');
        const question = inputField.value.trim();

        if (question) {
            // Hide welcome screen if visible
            this.hideWelcomeScreen();

            // Submit question
            this.onQuestionSubmit(question);

            // Clear input field
            inputField.value = '';
            inputField.style.height = 'auto';
            document.getElementById('send-btn').disabled = true;
        }
    }

    adjustTextareaHeight() {
        const textarea = document.getElementById('input-field');
        textarea.style.height = 'auto';
        textarea.style.height = (textarea.scrollHeight) + 'px';
    }

    clearChat() {
        const messageContainer = document.getElementById('message-container');
        messageContainer.innerHTML = '';
        this.currentAssistantMessageId = null;
    }

    showWelcomeScreen() {
        const messageContainer = document.getElementById('message-container');

        // Check if welcome screen already exists
        if (!document.getElementById('welcome-screen')) {
            messageContainer.innerHTML = `
                <div class="welcome-screen" id="welcome-screen">
                    <div class="welcome-logo">
                        <i class="fas fa-database" style="font-size: 64px; color: var(--primary-color);"></i>
                    </div>
                    <h1 class="welcome-title">Welcome to Vanna Text2SQL</h1>
                    <p class="welcome-subtitle">
                        Ask questions about your data in natural language, and I'll translate them into SQL queries and visualizations.
                    </p>
                    <div class="example-queries" id="example-queries">
                        <!-- Example queries will be added here -->
                    </div>
                </div>
            `;
        }
    }

    hideWelcomeScreen() {
        const welcomeScreen = document.getElementById('welcome-screen');
        if (welcomeScreen) {
            welcomeScreen.remove();
        }
    }

    addUserMessage(message) {
        const messageContainer = document.getElementById('message-container');
        const messageId = 'user-msg-' + Date.now();

        const messageHTML = `
            <div class="message user-message" id="${messageId}">
                <div class="message-avatar user-avatar">
                    <i class="fas fa-user"></i>
                </div>
                <div class="message-content">
                    <div class="message-header">
                        <div>您</div>
                    </div>
                    <div class="message-text">${this.escapeHTML(message)}</div>
                </div>
            </div>
        `;

        messageContainer.insertAdjacentHTML('beforeend', messageHTML);
        this.scrollToBottom();
    }

    startAssistantResponse() {
        const messageContainer = document.getElementById('message-container');
        const messageId = 'assistant-msg-' + Date.now();
        this.currentAssistantMessageId = messageId;

        const messageHTML = `
            <div class="message assistant-message" id="${messageId}">
                <div class="message-avatar assistant-avatar">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="message-content">
                    <div class="message-header">
                        <div>Vanna</div>
                        <div class="message-actions">
                            <button class="message-action-btn copy-btn" title="Copy response">
                                <i class="fas fa-copy"></i>
                            </button>
                        </div>
                    </div>
                    <div class="message-text">
                        <div class="typing-indicator">
                            <div class="typing-dot"></div>
                            <div class="typing-dot"></div>
                            <div class="typing-dot"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        messageContainer.insertAdjacentHTML('beforeend', messageHTML);
        this.scrollToBottom();
    }

    updateAssistantResponse(message, data = null) {
        if (!this.currentAssistantMessageId) return;

        const messageElement = document.getElementById(this.currentAssistantMessageId);
        if (!messageElement) return;

        const messageTextElement = messageElement.querySelector('.message-text');

        // Format the message with markdown-like syntax
        let formattedMessage = this.formatMessage(message);

        // Add data table if provided
        if (data && Array.isArray(data) && data.length > 0) {
            formattedMessage += this.createDataTable(data);
        }

        messageTextElement.innerHTML = formattedMessage;

        // Initialize syntax highlighting if hljs is available
        if (window.hljs) {
            messageElement.querySelectorAll('pre code').forEach((block) => {
                window.hljs.highlightElement(block);
            });
        }

        // Add event listener to copy buttons
        messageElement.querySelectorAll('.copy-code-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const codeBlock = btn.closest('.code-block').querySelector('code');
                navigator.clipboard.writeText(codeBlock.textContent);

                // Show copied feedback
                const originalText = btn.innerHTML;
                btn.innerHTML = '<i class="fas fa-check"></i> Copied!';
                setTimeout(() => {
                    btn.innerHTML = originalText;
                }, 2000);
            });
        });

        this.scrollToBottom();

        // 设置SQL复制按钮
        this.setupSqlCopyButtons();
    }

    addAssistantMessage(message, data = null) {
        const messageContainer = document.getElementById('message-container');
        const messageId = 'assistant-msg-' + Date.now();

        // Format the message with markdown-like syntax
        let formattedMessage = this.formatMessage(message);

        // Add data table if provided
        if (data && Array.isArray(data) && data.length > 0) {
            formattedMessage += this.createDataTable(data);
        }

        const messageHTML = `
            <div class="message assistant-message" id="${messageId}">
                <div class="message-avatar assistant-avatar">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="message-content">
                    <div class="message-header">
                        <div>Vanna</div>
                        <div class="message-actions">
                            <button class="message-action-btn copy-btn" title="复制回复">
                                <i class="fas fa-copy"></i>
                            </button>
                        </div>
                    </div>
                    <div class="message-text">
                        ${formattedMessage}
                    </div>
                </div>
            </div>
        `;

        messageContainer.insertAdjacentHTML('beforeend', messageHTML);

        // Initialize syntax highlighting if hljs is available
        const messageElement = document.getElementById(messageId);
        if (window.hljs) {
            messageElement.querySelectorAll('pre code').forEach((block) => {
                window.hljs.highlightElement(block);
            });
        }

        // Add event listener to copy buttons
        messageElement.querySelectorAll('.copy-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const codeBlock = btn.closest('.code-block').querySelector('code');
                navigator.clipboard.writeText(codeBlock.textContent);

                // Show copied feedback
                const originalText = btn.innerHTML;
                btn.innerHTML = '<i class="fas fa-check"></i> 已复制!';
                setTimeout(() => {
                    btn.innerHTML = originalText;
                }, 2000);
            });
        });

        this.scrollToBottom();

        // 设置SQL复制按钮
        this.setupSqlCopyButtons();
    }

    addVisualization(figData) {
        if (!this.currentAssistantMessageId) return;

        const messageElement = document.getElementById(this.currentAssistantMessageId);
        if (!messageElement) return;

        const messageTextElement = messageElement.querySelector('.message-text');

        // Create visualization container with loading indicator
        const visualizationContainer = document.createElement('div');
        visualizationContainer.className = 'visualization-container';
        visualizationContainer.id = 'viz-' + Date.now();

        // Add loading indicator
        const loadingIndicator = document.createElement('div');
        loadingIndicator.className = 'visualization-loading';
        loadingIndicator.innerHTML = `
            <div style="text-align: center;">
                <div class="typing-indicator" style="justify-content: center; margin-bottom: 10px;">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
                <div>正在生成可视化图表...</div>
            </div>
        `;
        visualizationContainer.appendChild(loadingIndicator);

        messageTextElement.appendChild(visualizationContainer);

        // Render the visualization
        try {
            if (window.Plotly) {
                // 优化图表配置
                const layout = figData.layout || {};

                // 设置默认边距
                layout.margin = layout.margin || { l: 50, r: 30, t: 50, b: 50 };

                // 确保有标题
                if (!layout.title) {
                    layout.title = {
                        text: '数据可视化',
                        font: { size: 18, color: '#202124' }
                    };
                }

                // 设置字体
                layout.font = layout.font || { family: 'Google Sans, Arial, sans-serif' };

                // 设置背景色
                layout.paper_bgcolor = 'rgba(0,0,0,0)';
                layout.plot_bgcolor = 'rgba(0,0,0,0)';

                // 设置网格线
                layout.xaxis = layout.xaxis || {};
                layout.yaxis = layout.yaxis || {};
                layout.xaxis.gridcolor = '#e1e4e8';
                layout.yaxis.gridcolor = '#e1e4e8';
                layout.xaxis.gridwidth = 1;
                layout.yaxis.gridwidth = 1;

                // 检测暗黑模式
                const isDarkMode = document.body.classList.contains('dark-mode');

                // 暗黑模式下的颜色调整
                if (isDarkMode) {
                    // 调整标题颜色
                    if (layout.title && layout.title.font) {
                        layout.title.font.color = '#e8eaed';
                    }

                    // 调整字体颜色
                    layout.font.color = '#e8eaed';

                    // 调整坐标轴颜色
                    layout.xaxis.color = '#9aa0a6';
                    layout.yaxis.color = '#9aa0a6';
                    layout.xaxis.gridcolor = '#3c4043';
                    layout.yaxis.gridcolor = '#3c4043';
                }

                // 设置配置选项
                const config = {
                    responsive: true,
                    displayModeBar: true,
                    displaylogo: false,
                    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
                    toImageButtonOptions: {
                        format: 'png',
                        filename: 'vanna_visualization',
                        height: 500,
                        width: 700,
                        scale: 2
                    }
                };

                // 渲染图表
                setTimeout(() => {
                    // 移除加载指示器
                    const loadingIndicator = visualizationContainer.querySelector('.visualization-loading');
                    if (loadingIndicator) {
                        loadingIndicator.remove();
                    }

                    // 渲染图表
                    window.Plotly.newPlot(visualizationContainer.id, figData.data, layout, config);

                    // 确保图表完全适应容器
                    setTimeout(() => {
                        window.Plotly.relayout(visualizationContainer.id, {
                            'autosize': true
                        });
                    }, 100);
                }, 500);
                console.log('Visualization rendered successfully');
            } else {
                console.error('Plotly is not available');
                visualizationContainer.innerHTML = '<div style="padding: 40px; text-align: center; color: #ea4335;"><i class="fas fa-exclamation-circle" style="font-size: 48px; margin-bottom: 16px;"></i><br>无法加载可视化库</div>';
            }
        } catch (error) {
            console.error('Error rendering visualization:', error);
            visualizationContainer.innerHTML = '<div style="padding: 40px; text-align: center; color: #ea4335;"><i class="fas fa-exclamation-circle" style="font-size: 48px; margin-bottom: 16px;"></i><br>可视化渲染失败</div>';
        }

        this.scrollToBottom();
    }

    showErrorMessage(message) {
        if (this.currentAssistantMessageId) {
            const messageElement = document.getElementById(this.currentAssistantMessageId);
            if (messageElement) {
                const messageTextElement = messageElement.querySelector('.message-text');
                messageTextElement.innerHTML = `<div class="error-message"><i class="fas fa-exclamation-circle"></i> ${message}</div>`;
            }
        } else {
            this.startAssistantResponse();
            const messageElement = document.getElementById(this.currentAssistantMessageId);
            const messageTextElement = messageElement.querySelector('.message-text');
            messageTextElement.innerHTML = `<div class="error-message"><i class="fas fa-exclamation-circle"></i> ${message}</div>`;
        }

        this.scrollToBottom();
    }

    displaySuggestedQuestions(questions) {
        if (!questions || !questions.length) return;

        // Find the current assistant message or create a container for suggested questions
        let container;

        if (this.currentAssistantMessageId) {
            const messageElement = document.getElementById(this.currentAssistantMessageId);
            if (messageElement) {
                container = messageElement.querySelector('.message-text');
            }
        }

        if (!container) {
            // If we're showing the welcome screen, add to example queries
            const exampleQueriesContainer = document.getElementById('example-queries');
            if (exampleQueriesContainer) {
                exampleQueriesContainer.innerHTML = '';

                questions.forEach(question => {
                    const exampleQuery = document.createElement('div');
                    exampleQuery.className = 'example-query';
                    exampleQuery.innerHTML = `
                        <div class="example-query-icon">
                            <i class="fas fa-search"></i>
                        </div>
                        <div class="example-query-text">${this.escapeHTML(question)}</div>
                    `;

                    exampleQuery.addEventListener('click', () => {
                        this.onSuggestedQuestionClick(question);
                    });

                    exampleQueriesContainer.appendChild(exampleQuery);
                });

                return;
            }

            // Otherwise create a new message for suggested questions
            const messageContainer = document.getElementById('message-container');
            const messageId = 'suggestions-' + Date.now();

            const messageHTML = `
                <div class="message assistant-message" id="${messageId}">
                    <div class="message-avatar assistant-avatar">
                        <i class="fas fa-robot"></i>
                    </div>
                    <div class="message-content">
                        <div class="message-header">
                            <div>Vanna</div>
                        </div>
                        <div class="message-text">
                            <p>Here are some questions you might want to ask:</p>
                            <div class="suggested-questions" id="suggested-questions-${messageId}"></div>
                        </div>
                    </div>
                </div>
            `;

            messageContainer.insertAdjacentHTML('beforeend', messageHTML);
            container = document.getElementById(`suggested-questions-${messageId}`);
        } else {
            // Add suggested questions to the current message
            container.insertAdjacentHTML('beforeend', `
                <p>Here are some questions you might want to ask:</p>
                <div class="suggested-questions" id="suggested-questions-${this.currentAssistantMessageId}"></div>
            `);
            container = document.getElementById(`suggested-questions-${this.currentAssistantMessageId}`);
        }

        // Add the suggested questions
        questions.forEach(question => {
            const questionElement = document.createElement('div');
            questionElement.className = 'suggested-question';
            questionElement.textContent = question;

            questionElement.addEventListener('click', () => {
                this.onSuggestedQuestionClick(question);
            });

            container.appendChild(questionElement);
        });

        this.scrollToBottom();
    }

    updateHistoryList(history) {
        const historyList = document.getElementById('history-list');
        historyList.innerHTML = '';

        if (!history || !history.length) {
            historyList.innerHTML = '<div class="history-empty">No history yet</div>';
            return;
        }

        history.forEach(item => {
            const historyItem = document.createElement('div');
            historyItem.className = 'history-item';
            historyItem.dataset.id = item.id;
            historyItem.innerHTML = `
                <i class="fas fa-history"></i>
                <span>${this.truncateText(item.question, 30)}</span>
            `;

            historyItem.addEventListener('click', () => {
                this.historyManager.loadQuestion(item.id);
            });

            historyList.appendChild(historyItem);
        });
    }

    setInputValue(text) {
        const inputField = document.getElementById('input-field');
        inputField.value = text;
        inputField.focus();
        this.adjustTextareaHeight();
        document.getElementById('send-btn').disabled = false;
    }

    toggleSidebar() {
        const sidebar = document.querySelector('.sidebar');
        this.isSidebarOpen = !this.isSidebarOpen;
        sidebar.classList.toggle('open', this.isSidebarOpen);
    }

    showTrainingModal() {
        document.getElementById('training-modal').style.display = 'flex';
        this.loadTrainingData();
    }

    hideTrainingModal() {
        document.getElementById('training-modal').style.display = 'none';
    }

    switchTrainingTab(tab) {
        // Update tab buttons
        document.getElementById('view-tab').classList.toggle('active', tab === 'view');
        document.getElementById('add-tab').classList.toggle('active', tab === 'add');

        // Show/hide content
        document.getElementById('view-content').style.display = tab === 'view' ? 'block' : 'none';
        document.getElementById('add-content').style.display = tab === 'add' ? 'block' : 'none';

        // Update footer buttons
        document.getElementById('save-training-btn').style.display = tab === 'add' ? 'block' : 'none';

        if (tab === 'view') {
            this.loadTrainingData();
        }
    }

    async loadTrainingData() {
        const container = document.getElementById('training-data-container');
        container.innerHTML = `
            <div style="display: flex; justify-content: center; padding: 40px 0;">
                <div style="display: flex; flex-direction: column; align-items: center;">
                    <div style="width: 48px; height: 48px; margin-bottom: 16px;">
                        <div class="typing-indicator" style="justify-content: center;">
                            <div class="typing-dot"></div>
                            <div class="typing-dot"></div>
                            <div class="typing-dot"></div>
                        </div>
                    </div>
                    <p>正在加载训练数据...</p>
                </div>
            </div>
        `;

        try {
            const data = await this.apiService.getTrainingData();

            if (!data || data.length === 0) {
                container.innerHTML = `
                    <div style="display: flex; justify-content: center; padding: 40px 0;">
                        <div style="display: flex; flex-direction: column; align-items: center; text-align: center;">
                            <div style="font-size: 48px; color: var(--text-secondary); margin-bottom: 16px;">
                                <i class="fas fa-database"></i>
                            </div>
                            <h3 style="margin-bottom: 8px;">没有可用的训练数据</h3>
                            <p style="color: var(--text-secondary); max-width: 400px;">
                                添加训练数据可以提高系统将自然语言转换为SQL的能力。
                            </p>
                            <button class="modal-btn modal-btn-primary" style="margin-top: 16px;" id="add-training-btn">
                                <i class="fas fa-plus"></i> 添加训练数据
                            </button>
                        </div>
                    </div>
                `;

                // Add event listener to the Add Training Data button
                document.getElementById('add-training-btn').addEventListener('click', () => {
                    this.switchTrainingTab('add');
                });

                return;
            }

            let tableHTML = `
                <table class="training-data-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>类型</th>
                            <th>内容</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            data.forEach(item => {
                // 确定数据类型和内容
                let dataType = '';
                let content = '';
                let codeClass = 'sql';

                if (item.question && item.sql) {
                    dataType = '问题和SQL查询';
                    content = `<strong>问题:</strong> ${this.escapeHTML(item.question)}<br><br>
                              <strong>SQL:</strong><br><pre><code class="sql">${this.escapeHTML(item.sql)}</code></pre>`;
                } else if (item.ddl) {
                    dataType = '表结构定义';
                    content = `<pre><code class="sql">${this.escapeHTML(item.ddl)}</code></pre>`;
                } else if (item.documentation) {
                    dataType = '文档说明';
                    content = this.escapeHTML(item.documentation).replace(/\n/g, '<br>');
                    codeClass = '';
                } else {
                    dataType = '未知类型';
                    content = '无效数据';
                }

                tableHTML += `
                    <tr>
                        <td>${item.id || 'N/A'}</td>
                        <td><span class="data-type-badge">${dataType}</span></td>
                        <td class="content-cell">${content}</td>
                        <td>
                            <div class="training-data-actions">
                                <button class="training-data-btn delete" data-id="${item.id}" title="删除">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </td>
                    </tr>
                `;
            });

            tableHTML += `
                    </tbody>
                </table>
            `;

            container.innerHTML = tableHTML;

            // Add event listeners to delete buttons
            container.querySelectorAll('.delete').forEach(btn => {
                btn.addEventListener('click', () => {
                    const id = btn.dataset.id;
                    const row = btn.closest('tr');
                    const dataType = row.querySelector('.data-type-badge').textContent;

                    // Create custom confirmation dialog
                    const confirmDialog = document.createElement('div');
                    confirmDialog.className = 'modal-overlay';
                    confirmDialog.style.zIndex = '2000';
                    confirmDialog.innerHTML = `
                        <div class="modal-container" style="max-width: 400px;">
                            <div class="modal-header">
                                <div class="modal-title">确认删除</div>
                                <button class="modal-close-btn" id="cancel-delete-btn">
                                    <i class="fas fa-times"></i>
                                </button>
                            </div>
                            <div class="modal-body">
                                <p style="margin-bottom: 16px;">您确定要删除这条训练数据吗？</p>
                                <div style="background-color: #f8f9fa; padding: 12px; border-radius: 8px; margin-bottom: 16px; border-left: 4px solid var(--primary-color);">
                                    <strong>类型：</strong> ${dataType}
                                </div>
                                <p style="color: var(--accent-color);"><i class="fas fa-exclamation-triangle"></i> 此操作无法撤销。</p>
                            </div>
                            <div class="modal-footer">
                                <button class="modal-btn modal-btn-secondary" id="cancel-delete-confirm-btn">取消</button>
                                <button class="modal-btn modal-btn-primary" style="background-color: var(--accent-color);" id="confirm-delete-btn">删除</button>
                            </div>
                        </div>
                    `;

                    document.body.appendChild(confirmDialog);

                    // Add event listeners to the dialog buttons
                    document.getElementById('cancel-delete-btn').addEventListener('click', () => {
                        document.body.removeChild(confirmDialog);
                    });

                    document.getElementById('cancel-delete-confirm-btn').addEventListener('click', () => {
                        document.body.removeChild(confirmDialog);
                    });

                    document.getElementById('confirm-delete-btn').addEventListener('click', () => {
                        // Show loading state
                        const confirmBtn = document.getElementById('confirm-delete-btn');
                        confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 正在删除...';
                        confirmBtn.disabled = true;

                        this.trainingManager.removeTrainingData(id)
                            .then(() => {
                                document.body.removeChild(confirmDialog);
                                this.loadTrainingData();
                            })
                            .catch(error => {
                                console.error('删除训练数据失败:', error);
                                confirmBtn.innerHTML = '删除';
                                confirmBtn.disabled = false;

                                // Show error message in the dialog
                                const modalBody = confirmDialog.querySelector('.modal-body');
                                const errorMessage = document.createElement('div');
                                errorMessage.className = 'form-error';
                                errorMessage.style.marginTop = '16px';
                                errorMessage.innerHTML = '<i class="fas fa-exclamation-circle"></i> 删除训练数据失败。请重试。';
                                modalBody.appendChild(errorMessage);
                            });
                    });
                });
            });

            // Initialize syntax highlighting if hljs is available
            if (window.hljs) {
                container.querySelectorAll('pre code').forEach((block) => {
                    window.hljs.highlightElement(block);
                });
            }

        } catch (error) {
            console.error('Failed to load training data:', error);
            container.innerHTML = `
                <div style="display: flex; justify-content: center; padding: 40px 0;">
                    <div style="display: flex; flex-direction: column; align-items: center; text-align: center;">
                        <div style="font-size: 48px; color: var(--accent-color); margin-bottom: 16px;">
                            <i class="fas fa-exclamation-circle"></i>
                        </div>
                        <h3 style="margin-bottom: 8px; color: var(--accent-color);">加载训练数据出错</h3>
                        <p style="color: var(--text-secondary); max-width: 400px;">
                            加载训练数据时出现问题。请稍后再试。
                        </p>
                        <button class="modal-btn modal-btn-primary" style="margin-top: 16px;" id="retry-load-btn">
                            <i class="fas fa-sync"></i> 重试
                        </button>
                    </div>
                </div>
            `;

            // Add event listener to the Retry button
            document.getElementById('retry-load-btn').addEventListener('click', () => {
                this.loadTrainingData();
            });
        }
    }

    // 保存问题和SQL查询
    saveQuestionSql() {
        const question = document.getElementById('question-input').value.trim();
        const sql = document.getElementById('sql-input').value.trim();

        // 验证输入
        let hasError = false;

        if (!question) {
            const questionInput = document.getElementById('question-input');
            questionInput.style.borderColor = 'var(--accent-color)';
            hasError = true;
        }

        if (!sql) {
            const sqlInput = document.getElementById('sql-input');
            sqlInput.style.borderColor = 'var(--accent-color)';
            hasError = true;
        }

        if (hasError) {
            // 显示错误消息
            const formError = document.createElement('div');
            formError.className = 'form-error';
            formError.innerHTML = '<i class="fas fa-exclamation-circle"></i> 问题和SQL查询为必填项。';

            // 插入到表单顶部
            const form = document.getElementById('question-sql-form');
            form.insertBefore(formError, form.firstChild);

            // 3秒后移除错误消息
            setTimeout(() => {
                formError.remove();
                document.getElementById('question-input').style.borderColor = '';
                document.getElementById('sql-input').style.borderColor = '';
            }, 3000);

            return;
        }

        // 显示加载状态
        const saveBtn = document.getElementById('save-question-sql-btn');
        const originalBtnText = saveBtn.innerHTML;
        saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 正在保存...';
        saveBtn.disabled = true;

        const trainingData = {
            question,
            sql
        };

        this.trainingManager.addTrainingData(trainingData)
            .then(() => {
                // 显示成功消息
                const successMessage = document.createElement('div');
                successMessage.className = 'form-success';
                successMessage.innerHTML = '<i class="fas fa-check-circle"></i> 问题和SQL查询添加成功！';

                // 插入到表单顶部
                const form = document.getElementById('question-sql-form');
                form.insertBefore(successMessage, form.firstChild);

                // 清空表单
                document.getElementById('question-input').value = '';
                document.getElementById('sql-input').value = '';

                // 重置按钮
                saveBtn.innerHTML = originalBtnText;
                saveBtn.disabled = false;

                // 2秒后移除成功消息并刷新训练数据列表
                setTimeout(() => {
                    successMessage.remove();
                    this.loadTrainingData();
                }, 2000);
            })
            .catch(error => {
                console.error('添加训练数据失败:', error);

                // 显示错误消息
                const errorMessage = document.createElement('div');
                errorMessage.className = 'form-error';
                errorMessage.innerHTML = '<i class="fas fa-exclamation-circle"></i> 添加问题和SQL查询失败。请重试。';

                // 插入到表单顶部
                const form = document.getElementById('question-sql-form');
                form.insertBefore(errorMessage, form.firstChild);

                // 重置按钮
                saveBtn.innerHTML = originalBtnText;
                saveBtn.disabled = false;

                // 3秒后移除错误消息
                setTimeout(() => {
                    errorMessage.remove();
                }, 3000);
            });
    }

    // 保存表结构定义
    saveDdl() {
        const ddl = document.getElementById('ddl-input').value.trim();

        // 验证输入
        if (!ddl) {
            // 显示错误消息
            const formError = document.createElement('div');
            formError.className = 'form-error';
            formError.innerHTML = '<i class="fas fa-exclamation-circle"></i> 表结构定义不能为空。';

            // 插入到表单顶部
            const form = document.getElementById('ddl-form');
            form.insertBefore(formError, form.firstChild);

            // 3秒后移除错误消息
            setTimeout(() => {
                formError.remove();
            }, 3000);

            return;
        }

        // 显示加载状态
        const saveBtn = document.getElementById('save-ddl-btn');
        const originalBtnText = saveBtn.innerHTML;
        saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 正在保存...';
        saveBtn.disabled = true;

        const trainingData = {
            ddl
        };

        this.trainingManager.addTrainingData(trainingData)
            .then(() => {
                // 显示成功消息
                const successMessage = document.createElement('div');
                successMessage.className = 'form-success';
                successMessage.innerHTML = '<i class="fas fa-check-circle"></i> 表结构定义添加成功！';

                // 插入到表单顶部
                const form = document.getElementById('ddl-form');
                form.insertBefore(successMessage, form.firstChild);

                // 清空表单
                document.getElementById('ddl-input').value = '';

                // 重置按钮
                saveBtn.innerHTML = originalBtnText;
                saveBtn.disabled = false;

                // 2秒后移除成功消息并刷新训练数据列表
                setTimeout(() => {
                    successMessage.remove();
                    this.loadTrainingData();
                }, 2000);
            })
            .catch(error => {
                console.error('添加表结构定义失败:', error);

                // 显示错误消息
                const errorMessage = document.createElement('div');
                errorMessage.className = 'form-error';
                errorMessage.innerHTML = '<i class="fas fa-exclamation-circle"></i> 添加表结构定义失败。请重试。';

                // 插入到表单顶部
                const form = document.getElementById('ddl-form');
                form.insertBefore(errorMessage, form.firstChild);

                // 重置按钮
                saveBtn.innerHTML = originalBtnText;
                saveBtn.disabled = false;

                // 3秒后移除错误消息
                setTimeout(() => {
                    errorMessage.remove();
                }, 3000);
            });
    }

    // 保存文档说明
    saveDocumentation() {
        const documentation = document.getElementById('documentation-input').value.trim();

        // 验证输入
        if (!documentation) {
            // 显示错误消息
            const formError = document.createElement('div');
            formError.className = 'form-error';
            formError.innerHTML = '<i class="fas fa-exclamation-circle"></i> 文档说明不能为空。';

            // 插入到表单顶部
            const form = document.getElementById('documentation-form');
            form.insertBefore(formError, form.firstChild);

            // 3秒后移除错误消息
            setTimeout(() => {
                formError.remove();
            }, 3000);

            return;
        }

        // 显示加载状态
        const saveBtn = document.getElementById('save-documentation-btn');
        const originalBtnText = saveBtn.innerHTML;
        saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 正在保存...';
        saveBtn.disabled = true;

        const trainingData = {
            documentation
        };

        this.trainingManager.addTrainingData(trainingData)
            .then(() => {
                // 显示成功消息
                const successMessage = document.createElement('div');
                successMessage.className = 'form-success';
                successMessage.innerHTML = '<i class="fas fa-check-circle"></i> 文档说明添加成功！';

                // 插入到表单顶部
                const form = document.getElementById('documentation-form');
                form.insertBefore(successMessage, form.firstChild);

                // 清空表单
                document.getElementById('documentation-input').value = '';

                // 重置按钮
                saveBtn.innerHTML = originalBtnText;
                saveBtn.disabled = false;

                // 2秒后移除成功消息并刷新训练数据列表
                setTimeout(() => {
                    successMessage.remove();
                    this.loadTrainingData();
                }, 2000);
            })
            .catch(error => {
                console.error('添加文档说明失败:', error);

                // 显示错误消息
                const errorMessage = document.createElement('div');
                errorMessage.className = 'form-error';
                errorMessage.innerHTML = '<i class="fas fa-exclamation-circle"></i> 添加文档说明失败。请重试。';

                // 插入到表单顶部
                const form = document.getElementById('documentation-form');
                form.insertBefore(errorMessage, form.firstChild);

                // 重置按钮
                saveBtn.innerHTML = originalBtnText;
                saveBtn.disabled = false;

                // 3秒后移除错误消息
                setTimeout(() => {
                    errorMessage.remove();
                }, 3000);
            });
    }

    // Helper methods
    scrollToBottom() {
        const chatContainer = document.getElementById('chat-container');
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // 添加SQL复制功能
    setupSqlCopyButtons() {
        document.querySelectorAll('.sql-copy-btn').forEach(btn => {
            // 移除旧的事件监听器
            btn.removeEventListener('click', this.handleSqlCopy);
            // 添加新的事件监听器
            btn.addEventListener('click', this.handleSqlCopy);
        });
    }

    // SQL复制按钮点击处理函数
    handleSqlCopy(event) {
        const btn = event.currentTarget;
        const sqlCode = btn.nextElementSibling.textContent;

        // 复制到剪贴板
        navigator.clipboard.writeText(sqlCode)
            .then(() => {
                // 显示复制成功反馈
                const originalHTML = btn.innerHTML;
                btn.innerHTML = '<i class="fas fa-check"></i>';

                // 2秒后恢复原始图标
                setTimeout(() => {
                    btn.innerHTML = originalHTML;
                }, 2000);
            })
            .catch(err => {
                console.error('复制失败:', err);
            });
    }

    escapeHTML(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    truncateText(text, maxLength) {
        if (!text) return '';
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    }

    formatMessage(message) {
        // Replace code blocks
        let formattedMessage = message.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, language, code) => {
            const lang = language || 'sql';
            let cleanCode = this.escapeHTML(code.trim());

            // Apply custom SQL syntax highlighting
            if (lang === 'sql') {
                // SQL keywords (case insensitive)
                const keywords = [
                    'SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING', 'JOIN', 'LEFT JOIN',
                    'RIGHT JOIN', 'INNER JOIN', 'OUTER JOIN', 'FULL JOIN', 'CROSS JOIN', 'ON', 'AS', 'AND',
                    'OR', 'NOT', 'IN', 'EXISTS', 'LIKE', 'BETWEEN', 'IS NULL', 'IS NOT NULL', 'DISTINCT',
                    'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'WITH',
                    'UNION', 'ALL', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP', 'TABLE', 'VIEW',
                    'INDEX', 'CONSTRAINT', 'PRIMARY KEY', 'FOREIGN KEY', 'REFERENCES', 'DEFAULT', 'NULL',
                    'NOT NULL', 'AUTO_INCREMENT', 'LIMIT', 'OFFSET', 'TOP', 'DESC', 'ASC'
                ];

                // Create a single regex for all keywords with word boundaries
                const keywordPattern = new RegExp('\\b(' + keywords.join('|') + ')\\b', 'gi');
                cleanCode = cleanCode.replace(keywordPattern, '<span class="keyword">$&</span>');

                // Highlight strings (single quotes)
                cleanCode = cleanCode.replace(/('[^']*')/g, '<span class="string">$1</span>');

                // Highlight strings (double quotes)
                cleanCode = cleanCode.replace(/("[^"]*")/g, '<span class="string">$1</span>');

                // Highlight numbers
                cleanCode = cleanCode.replace(/(\b\d+(\.\d+)?\b)/g, '<span class="number">$1</span>');

                // Highlight comments
                cleanCode = cleanCode.replace(/(--[^\n]*)/g, '<span class="comment">$1</span>');
                cleanCode = cleanCode.replace(/(\/\*[\s\S]*?\*\/)/g, '<span class="comment">$1</span>');
            }

            return `
                <div class="code-block">
                    <div class="code-header">
                        <span><i class="fas fa-code" style="margin-right: 6px; font-size: 12px;"></i>${lang.toUpperCase()}</span>
                        <button class="copy-btn" title="复制代码">
                            <i class="fas fa-copy" style="margin-right: 3px; font-size: 11px;"></i>复制
                        </button>
                    </div>
                    <pre><code class="${lang}">${cleanCode}</code></pre>
                </div>
            `;
        });

        // Replace inline code
        formattedMessage = formattedMessage.replace(/`([^`]+)`/g, '<code>$1</code>');

        // Replace newlines with <br>
        formattedMessage = formattedMessage.replace(/\n/g, '<br>');

        return formattedMessage;
    }

    createDataTable(data) {
        if (!data || !data.length) return '';

        const columns = Object.keys(data[0]);

        let tableHTML = `
            <div class="data-table-container">
                <table class="data-table">
                    <thead>
                        <tr>
                            ${columns.map(col => `<th>${this.escapeHTML(col)}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody>
        `;

        data.forEach(row => {
            tableHTML += '<tr>';
            columns.forEach(col => {
                const value = row[col] !== null && row[col] !== undefined ? row[col] : '';
                tableHTML += `<td>${this.escapeHTML(String(value))}</td>`;
            });
            tableHTML += '</tr>';
        });

        tableHTML += `
                    </tbody>
                </table>
            </div>
        `;

        return tableHTML;
    }
}
