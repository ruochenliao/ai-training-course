// API Service for communicating with the backend
export class ApiService {
    constructor() {
        this.baseUrl = '/api/v0';
        // Make sure we're using the correct base URL
        if (window.location.port === '9000') {
            // Development environment
            this.baseUrl = 'http://localhost:8000/api/v0';
        }
    }

    async generateQuestions() {
        try {
            const response = await fetch(`${this.baseUrl}/generate_questions`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            return data.questions || [];
        } catch (error) {
            console.error('Error generating questions:', error);
            throw error;
        }
    }

    async generateSQL(question) {
        try {
            const response = await fetch(`${this.baseUrl}/generate_sql?question=${encodeURIComponent(question)}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            if (data.type === 'error') {
                throw new Error(data.error);
            }
            return data;
        } catch (error) {
            console.error('Error generating SQL:', error);
            throw error;
        }
    }

    async runSQL(id) {
        try {
            const response = await fetch(`${this.baseUrl}/run_sql?id=${id}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            if (data.type === 'error') {
                throw new Error(data.error);
            }
            return data;
        } catch (error) {
            console.error('Error running SQL:', error);
            throw error;
        }
    }

    async generatePlotlyFigure(id) {
        try {
            const response = await fetch(`${this.baseUrl}/generate_plotly_figure?id=${id}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            if (data.type === 'error') {
                throw new Error(data.error);
            }
            return data;
        } catch (error) {
            console.error('Error generating Plotly figure:', error);
            throw error;
        }
    }

    async generateFollowupQuestions(id) {
        try {
            const response = await fetch(`${this.baseUrl}/generate_followup_questions?id=${id}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            if (data.type === 'error') {
                throw new Error(data.error);
            }
            return data;
        } catch (error) {
            console.error('Error generating followup questions:', error);
            throw error;
        }
    }

    async loadQuestion(id) {
        try {
            const response = await fetch(`${this.baseUrl}/load_question?id=${id}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            if (data.type === 'error') {
                throw new Error(data.error);
            }
            return data;
        } catch (error) {
            console.error('Error loading question:', error);
            throw error;
        }
    }

    async getQuestionHistory() {
        try {
            const response = await fetch(`${this.baseUrl}/get_question_history`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            return data.questions || [];
        } catch (error) {
            console.error('Error getting question history:', error);
            throw error;
        }
    }

    async downloadCSV(id) {
        try {
            window.open(`${this.baseUrl}/download_csv?id=${id}`, '_blank');
        } catch (error) {
            console.error('Error downloading CSV:', error);
            throw error;
        }
    }

    async getTrainingData() {
        try {
            const response = await fetch(`${this.baseUrl}/get_training_data`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            if (data.type === 'error') {
                throw new Error(data.error);
            }
            return JSON.parse(data.df) || [];
        } catch (error) {
            console.error('Error getting training data:', error);
            throw error;
        }
    }

    async addTrainingData(trainingData) {
        try {
            const response = await fetch(`${this.baseUrl}/train`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(trainingData)
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            if (data.type === 'error') {
                throw new Error(data.error);
            }
            return data;
        } catch (error) {
            console.error('Error adding training data:', error);
            throw error;
        }
    }

    async removeTrainingData(id) {
        try {
            const response = await fetch(`${this.baseUrl}/remove_training_data`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ id })
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            if (data.type === 'error') {
                throw new Error(data.error);
            }
            return data;
        } catch (error) {
            console.error('Error removing training data:', error);
            throw error;
        }
    }
}
