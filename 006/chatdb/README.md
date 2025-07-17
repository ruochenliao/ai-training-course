# ChatDB - Text2SQL System

ChatDB is an intelligent Text2SQL system that allows users to query databases using natural language. The system features a React frontend for schema visualization and management, a Python FastAPI backend for processing queries, and uses MySQL and Neo4j for metadata storage and schema relationship management.

## Features

- **Database Connection Management**: Connect to various database systems
- **Schema Visualization & Management**: Visualize and maintain database schema with an interactive graph interface
- **Intelligent Query**: Convert natural language questions to SQL queries using LLM technology
- **Value Mappings**: Map natural language terms to actual database values

## Architecture

- **Frontend**: React with Ant Design and React Flow for visualization
- **Backend**: Python FastAPI
- **Metadata Storage**: MySQL
- **Schema Relationship Storage**: Neo4j
- **LLM Integration**: OpenAI GPT-4 (or other LLM services)

## Prerequisites

- Docker and Docker Compose
- OpenAI API Key (or other LLM service API key)

## Setup and Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/chatdb.git
   cd chatdb
   ```

2. Create a `.env` file in the root directory with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

3. Start the services using Docker Compose:
   ```
   docker-compose up -d
   ```

4. Initialize the database (first time only):
   ```
   docker-compose exec backend python init_db.py
   ```

5. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/docs
   - Neo4j Browser: http://localhost:7474 (username: neo4j, password: password)

## Usage Guide

### 1. Database Connections

1. Navigate to the "Database Connections" page
2. Click "Add Connection" to create a new database connection
3. Fill in the connection details and click "Save"
4. Test the connection using the "Test" button

### 2. Schema Management

1. Navigate to the "Schema Management" page
2. Select a database connection from the dropdown
3. The system will discover the schema from the target database
4. Drag tables from the left panel to the canvas
5. Connect tables by dragging from one table to another
6. Click on tables or relationships to edit their properties
7. Click "Publish Schema" to save your changes

### 3. Intelligent Query

1. Navigate to the "Intelligent Query" page
2. Select a database connection from the dropdown
3. Enter your question in natural language
4. Click "Execute Query" to generate and run the SQL
5. View the generated SQL, query results, and context information

### 4. Value Mappings

1. Navigate to the "Value Mappings" page
2. Select a connection, table, and column
3. Add mappings between natural language terms and database values
4. These mappings will be used when processing natural language queries

## Development

### Backend

The backend is built with FastAPI and uses SQLAlchemy for database ORM.

```
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

The frontend is built with React and uses Ant Design for UI components.

```
cd frontend
npm install
npm start
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

# SQL解释内容显示问题修复

本次修复解决了前端React应用中SQL解释内容显示后又变回"处理中"状态的问题。

## 主要修改内容

### 1. SQLTab.tsx组件改进
- 添加`explanationStable`状态追踪解释内容是否稳定
- 优化内容渲染逻辑，确保一旦内容显示就保持稳定
- 改进状态依赖关系，防止不必要的重渲染
- 添加优先级渲染逻辑，稳定内容优先显示
- 增强样式过渡效果，提升用户体验

### 2. page.tsx处理逻辑改进
- 增强`handleMessage`函数，防止非解释区域消息干扰解释内容
- 修改`handleFinalExplanation`函数，改进解释结果设置流程
- 提升状态更新的稳定性和可靠性，使用延时确保状态正确设置
- 抽取`handlePostMessageTasks`函数，优化代码结构
- 完善`resetProcessingState`函数，根据内容存在与否采取不同策略

### 3. api.ts文件修改
- 增强`handleFinalResult`方法的条件检查和日志记录
- 提供更详细的错误原因说明，便于调试

## 总结

通过以上修改，解决了SQL解释内容在界面上显示后会重新变为处理中状态的问题。主要原因是组件状态管理和渲染逻辑中的问题，导致当其他区域更新时会重置解释区域的状态。现在解释内容区域能够保持稳定，且支持流式显示，类似于查询分析区域的行为。
