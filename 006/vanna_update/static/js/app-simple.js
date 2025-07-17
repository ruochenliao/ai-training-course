// Simplified version of the app.js for testing
console.log('Simple app loaded');

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded in simple app');
    
    // Create a simple chat interface
    const appDiv = document.getElementById('app');
    appDiv.innerHTML = `
        <div style="max-width: 800px; margin: 0 auto; padding: 20px;">
            <h1 style="color: #4285f4;">Vanna Text2SQL - Simple Test</h1>
            <p>This is a simplified version of the application for testing.</p>
            
            <div id="chat-container" style="border: 1px solid #dadce0; border-radius: 8px; padding: 20px; margin: 20px 0; height: 400px; overflow-y: auto;"></div>
            
            <div style="display: flex;">
                <input type="text" id="input-field" placeholder="Ask a question about your data..." 
                    style="flex: 1; padding: 10px; border: 1px solid #dadce0; border-radius: 4px; font-size: 16px;">
                <button id="send-btn" 
                    style="padding: 10px 20px; background-color: #4285f4; color: white; border: none; border-radius: 4px; margin-left: 10px; cursor: pointer;">
                    Send
                </button>
            </div>
            
            <div style="margin-top: 20px;">
                <h3>Test Highlight.js</h3>
                <button id="test-highlight-btn" 
                    style="padding: 10px 20px; background-color: #34a853; color: white; border: none; border-radius: 4px; cursor: pointer;">
                    Test Syntax Highlighting
                </button>
            </div>
        </div>
    `;
    
    // Add event listeners
    const inputField = document.getElementById('input-field');
    const sendBtn = document.getElementById('send-btn');
    const chatContainer = document.getElementById('chat-container');
    const testHighlightBtn = document.getElementById('test-highlight-btn');
    
    sendBtn.addEventListener('click', () => {
        const question = inputField.value.trim();
        if (question) {
            // Add user message
            addMessage('user', question);
            
            // Clear input field
            inputField.value = '';
            
            // Simulate assistant response
            setTimeout(() => {
                const sqlQuery = `SELECT * FROM data WHERE question = '${question}';`;
                addMessage('assistant', `I've translated your question into SQL:\n\n\`\`\`sql\n${sqlQuery}\n\`\`\`\n\nThis is a simulated response for testing purposes.`);
            }, 1000);
        }
    });
    
    // Allow pressing Enter to send message
    inputField.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            sendBtn.click();
        }
    });
    
    // Test highlight.js
    testHighlightBtn.addEventListener('click', () => {
        const sqlCode = `SELECT 
    customers.name, 
    SUM(orders.amount) AS total_amount
FROM 
    customers
JOIN 
    orders ON customers.id = orders.customer_id
WHERE 
    orders.date BETWEEN '2023-01-01' AND '2023-12-31'
    AND customers.status = 'active'
GROUP BY 
    customers.name
HAVING 
    SUM(orders.amount) > 1000
ORDER BY 
    total_amount DESC
LIMIT 10;`;
        
        addMessage('assistant', `Testing syntax highlighting:\n\n\`\`\`sql\n${sqlCode}\n\`\`\`\n\nCheck if the SQL code above is properly highlighted.`);
    });
    
    // Helper function to add a message to the chat
    function addMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.style.marginBottom = '15px';
        messageDiv.style.padding = '10px';
        messageDiv.style.borderRadius = '8px';
        
        if (role === 'user') {
            messageDiv.style.backgroundColor = '#e6f4ff';
            messageDiv.style.marginLeft = '50px';
            messageDiv.innerHTML = `<strong>You:</strong> ${escapeHTML(content)}`;
        } else {
            messageDiv.style.backgroundColor = '#f8f9fa';
            messageDiv.style.marginRight = '50px';
            
            // Format the message with code highlighting
            let formattedContent = formatMessage(content);
            messageDiv.innerHTML = `<strong>Vanna:</strong> ${formattedContent}`;
            
            // Apply syntax highlighting if available
            if (window.hljs) {
                messageDiv.querySelectorAll('pre code').forEach((block) => {
                    try {
                        window.hljs.highlightElement(block);
                        console.log('Syntax highlighting applied');
                    } catch (error) {
                        console.error('Error applying syntax highlighting:', error);
                    }
                });
            } else {
                console.warn('highlight.js not available for syntax highlighting');
            }
        }
        
        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    // Helper function to escape HTML
    function escapeHTML(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Helper function to format messages with code blocks
    function formatMessage(message) {
        // Replace code blocks
        let formattedMessage = message.replace(/```(\\w+)?\\n([\\s\\S]*?)```/g, (match, language, code) => {
            const lang = language || 'sql';
            
            // Apply simple syntax highlighting if hljs is not available
            let highlightedCode = escapeHTML(code.trim());
            
            // Simple SQL syntax highlighting as fallback
            if (lang === 'sql' && !window.hljs) {
                // Highlight SQL keywords
                const keywords = ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING', 'JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'INNER JOIN', 'OUTER JOIN', 'ON', 'AS', 'AND', 'OR', 'NOT', 'IN', 'LIKE', 'BETWEEN', 'IS NULL', 'IS NOT NULL', 'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'DISTINCT', 'UNION', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP', 'TABLE', 'VIEW', 'INDEX', 'CONSTRAINT', 'PRIMARY KEY', 'FOREIGN KEY', 'REFERENCES', 'DEFAULT', 'NULL', 'NOT NULL', 'AUTO_INCREMENT', 'LIMIT', 'OFFSET'];
                
                keywords.forEach(keyword => {
                    // Case-insensitive replacement
                    const regex = new RegExp(`\\b${keyword}\\b`, 'gi');
                    highlightedCode = highlightedCode.replace(regex, `<span style="color: #0033b3; font-weight: bold;">$&</span>`);
                });
                
                // Highlight strings
                highlightedCode = highlightedCode.replace(/('[^']*')/g, `<span style="color: #008000;">$1</span>`);
                highlightedCode = highlightedCode.replace(/("[^"]*")/g, `<span style="color: #008000;">$1</span>`);
                
                // Highlight numbers
                highlightedCode = highlightedCode.replace(/(\\b\\d+(\\.\\d+)?\\b)/g, `<span style="color: #0000ff;">$1</span>`);
                
                // Highlight comments
                highlightedCode = highlightedCode.replace(/(--[^\\n]*)/g, `<span style="color: #808080;">$1</span>`);
            }
            
            return `
                <div style="background-color: #f6f8fa; border-radius: 6px; padding: 16px; margin: 16px 0; position: relative;">
                    <div style="display: flex; justify-content: space-between; padding: 8px 16px; background-color: #f1f3f4; border-top-left-radius: 6px; border-top-right-radius: 6px; font-family: monospace; color: #5f6368; font-size: 12px;">
                        <span>${lang}</span>
                        <button style="background: none; border: none; cursor: pointer; color: #5f6368; font-size: 14px;" onclick="navigator.clipboard.writeText(this.parentNode.nextElementSibling.textContent)">
                            Copy
                        </button>
                    </div>
                    <pre style="margin: 0;"><code class="${lang}">${highlightedCode}</code></pre>
                </div>
            `;
        });
        
        // Replace inline code
        formattedMessage = formattedMessage.replace(/`([^`]+)`/g, '<code style="background-color: #f6f8fa; padding: 2px 4px; border-radius: 3px; font-family: monospace;">$1</code>');
        
        // Replace newlines with <br>
        formattedMessage = formattedMessage.replace(/\\n/g, '<br>');
        
        return formattedMessage;
    }
    
    // Add a welcome message
    addMessage('assistant', 'Hello! I\'m your Text2SQL assistant. Ask me a question about your data, and I\'ll translate it into SQL.');
});
