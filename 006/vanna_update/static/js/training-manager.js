// Training Manager Component
export class TrainingManager {
    constructor(apiService) {
        this.apiService = apiService;
    }
    
    async getTrainingData() {
        try {
            return await this.apiService.getTrainingData();
        } catch (error) {
            console.error('Failed to get training data:', error);
            throw error;
        }
    }
    
    async addTrainingData(trainingData) {
        try {
            return await this.apiService.addTrainingData(trainingData);
        } catch (error) {
            console.error('Failed to add training data:', error);
            throw error;
        }
    }
    
    async removeTrainingData(id) {
        try {
            return await this.apiService.removeTrainingData(id);
        } catch (error) {
            console.error('Failed to remove training data:', error);
            throw error;
        }
    }
}
