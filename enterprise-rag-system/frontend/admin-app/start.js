#!/usr/bin/env node
/**
 * 企业级Agent+RAG知识库系统 - 管理端启动脚本
 */

// 加载 Node.js 兼容性 polyfill
require('./polyfills/node-polyfill');

const fs = require('fs');
const path = require('path');
const { spawn, exec } = require('child_process');
const chalk = require('chalk');

class AdminAppServer {
    constructor() {
        this.projectRoot = __dirname;
        this.envFile = path.join(this.projectRoot, '.env');
        this.packageFile = path.join(this.projectRoot, 'package.json');
        this.serverProcess = null;
    }

    /**
     * 日志输出
     */
    log(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const prefix = `[${timestamp}]`;
        
        switch (type) {
            case 'success':
                console.log(chalk.green(`${prefix} ✅ ${message}`));
                break;
            case 'error':
                console.log(chalk.red(`${prefix} ❌ ${message}`));
                break;
            case 'warning':
                console.log(chalk.yellow(`${prefix} ⚠️  ${message}`));
                break;
            case 'info':
            default:
                console.log(chalk.blue(`${prefix} 🔍 ${message}`));
                break;
        }
    }

    /**
     * 检查Node.js版本
     */
    checkNodeVersion() {
        this.log('检查Node.js版本...');
        
        const nodeVersion = process.version;
        const majorVersion = parseInt(nodeVersion.slice(1).split('.')[0]);
        
        if (majorVersion < 18) {
            this.log(`当前Node.js版本: ${nodeVersion}`, 'error');
            this.log('需要Node.js 18.0.0或更高版本', 'error');
            return false;
        }
        
        this.log(`Node.js版本检查通过: ${nodeVersion}`, 'success');
        return true;
    }

    /**
     * 检查依赖
     */
    async checkDependencies() {
        this.log('检查项目依赖...');
        
        if (!fs.existsSync(this.packageFile)) {
            this.log('package.json文件不存在', 'error');
            return false;
        }

        const nodeModulesPath = path.join(this.projectRoot, 'node_modules');
        if (!fs.existsSync(nodeModulesPath)) {
            this.log('node_modules目录不存在，正在安装依赖...', 'warning');
            return await this.installDependencies();
        }

        // 检查关键依赖
        const requiredDeps = ['nuxt', 'vue', '@nuxt/devtools'];
        for (const dep of requiredDeps) {
            const depPath = path.join(nodeModulesPath, dep);
            if (!fs.existsSync(depPath)) {
                this.log(`缺少依赖: ${dep}`, 'error');
                this.log('正在重新安装依赖...', 'warning');
                return await this.installDependencies();
            }
        }

        this.log('依赖检查通过', 'success');
        return true;
    }

    /**
     * 安装依赖
     */
    async installDependencies() {
        return new Promise((resolve) => {
            this.log('开始安装依赖...');
            
            const npm = process.platform === 'win32' ? 'npm.cmd' : 'npm';
            const installProcess = spawn(npm, ['install'], {
                cwd: this.projectRoot,
                stdio: 'inherit'
            });

            installProcess.on('close', (code) => {
                if (code === 0) {
                    this.log('依赖安装完成', 'success');
                    resolve(true);
                } else {
                    this.log('依赖安装失败', 'error');
                    resolve(false);
                }
            });

            installProcess.on('error', (err) => {
                this.log(`依赖安装出错: ${err.message}`, 'error');
                resolve(false);
            });
        });
    }

    /**
     * 检查环境配置
     */
    checkEnvironment() {
        this.log('检查环境配置...');
        
        if (!fs.existsSync(this.envFile)) {
            this.log('.env文件不存在，正在创建...', 'warning');
            this.createEnvFile();
        }

        // 加载环境变量
        try {
            const envContent = fs.readFileSync(this.envFile, 'utf8');
            const envVars = {};
            
            envContent.split('\n').forEach(line => {
                const [key, value] = line.split('=');
                if (key && value) {
                    envVars[key.trim()] = value.trim();
                }
            });

            // 检查关键配置
            const requiredVars = ['NUXT_PUBLIC_API_BASE_URL'];
            const missingVars = requiredVars.filter(varName => !envVars[varName]);
            
            if (missingVars.length > 0) {
                this.log(`缺少环境变量: ${missingVars.join(', ')}`, 'warning');
                this.log('请检查 .env 文件配置', 'warning');
            }

            this.log('环境配置检查完成', 'success');
            return true;
        } catch (error) {
            this.log(`环境配置检查失败: ${error.message}`, 'error');
            return false;
        }
    }

    /**
     * 创建环境文件
     */
    createEnvFile() {
        const envExamplePath = path.join(this.projectRoot, '.env.example');
        
        if (fs.existsSync(envExamplePath)) {
            fs.copyFileSync(envExamplePath, this.envFile);
            this.log('已从 .env.example 创建 .env 文件', 'success');
        } else {
            // 创建基本的环境文件
            const basicEnv = `# 管理端环境配置
NUXT_PUBLIC_APP_NAME=企业级RAG知识库管理后台
NUXT_PUBLIC_API_BASE_URL=http://localhost:8000
NUXT_PUBLIC_API_PREFIX=/api/v1
NUXT_PORT=3001
`;
            fs.writeFileSync(this.envFile, basicEnv);
            this.log('已创建基本的 .env 文件', 'success');
        }
    }

    /**
     * 检查后端服务
     */
    async checkBackendService() {
        this.log('检查后端服务连接...');
        
        const apiUrl = process.env.NUXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
        
        return new Promise((resolve) => {
            const { exec } = require('child_process');
            
            // 使用curl检查后端健康状态
            exec(`curl -s ${apiUrl}/health`, (error, stdout, stderr) => {
                if (error) {
                    this.log('后端服务未启动或不可访问', 'warning');
                    this.log('请确保后端服务正在运行', 'warning');
                    resolve(false);
                } else {
                    try {
                        const response = JSON.parse(stdout);
                        if (response.status === 'healthy') {
                            this.log('后端服务连接正常', 'success');
                            resolve(true);
                        } else {
                            this.log('后端服务状态异常', 'warning');
                            resolve(false);
                        }
                    } catch (e) {
                        this.log('后端服务响应格式异常', 'warning');
                        resolve(false);
                    }
                }
            });
        });
    }

    /**
     * 启动开发服务器
     */
    async startDevServer() {
        this.log('启动管理端开发服务器...');
        
        const port = process.env.NUXT_PORT || 3001;
        const host = process.env.NUXT_HOST || 'localhost';
        
        this.log(`服务地址: http://${host}:${port}`);
        
        const npm = process.platform === 'win32' ? 'npm.cmd' : 'npm';
        
        this.serverProcess = spawn(npm, ['run', 'dev'], {
            cwd: this.projectRoot,
            stdio: 'inherit',
            env: {
                ...process.env,
                NUXT_PORT: port,
                NUXT_HOST: host,
                NODE_OPTIONS: '--require ./polyfills/node-polyfill.js --no-warnings=ExperimentalWarning'
            }
        });

        this.serverProcess.on('close', (code) => {
            if (code !== 0) {
                this.log(`开发服务器退出，代码: ${code}`, 'error');
            }
        });

        this.serverProcess.on('error', (err) => {
            this.log(`开发服务器启动失败: ${err.message}`, 'error');
        });

        // 处理进程退出
        process.on('SIGINT', () => {
            this.log('正在停止开发服务器...');
            if (this.serverProcess) {
                this.serverProcess.kill('SIGINT');
            }
            process.exit(0);
        });

        process.on('SIGTERM', () => {
            this.log('正在停止开发服务器...');
            if (this.serverProcess) {
                this.serverProcess.kill('SIGTERM');
            }
            process.exit(0);
        });
    }

    /**
     * 构建生产版本
     */
    async buildProduction() {
        this.log('构建生产版本...');
        
        return new Promise((resolve) => {
            const npm = process.platform === 'win32' ? 'npm.cmd' : 'npm';
            
            const buildProcess = spawn(npm, ['run', 'build'], {
                cwd: this.projectRoot,
                stdio: 'inherit'
            });

            buildProcess.on('close', (code) => {
                if (code === 0) {
                    this.log('生产版本构建完成', 'success');
                    resolve(true);
                } else {
                    this.log('生产版本构建失败', 'error');
                    resolve(false);
                }
            });

            buildProcess.on('error', (err) => {
                this.log(`构建过程出错: ${err.message}`, 'error');
                resolve(false);
            });
        });
    }

    /**
     * 生成静态文件
     */
    async generateStatic() {
        this.log('生成静态文件...');
        
        return new Promise((resolve) => {
            const npm = process.platform === 'win32' ? 'npm.cmd' : 'npm';
            
            const generateProcess = spawn(npm, ['run', 'generate'], {
                cwd: this.projectRoot,
                stdio: 'inherit'
            });

            generateProcess.on('close', (code) => {
                if (code === 0) {
                    this.log('静态文件生成完成', 'success');
                    resolve(true);
                } else {
                    this.log('静态文件生成失败', 'error');
                    resolve(false);
                }
            });

            generateProcess.on('error', (err) => {
                this.log(`生成过程出错: ${err.message}`, 'error');
                resolve(false);
            });
        });
    }

    /**
     * 预览生产版本
     */
    async previewProduction() {
        this.log('启动生产版本预览...');
        
        const port = process.env.NUXT_PORT || 3001;
        const host = process.env.NUXT_HOST || 'localhost';
        
        this.log(`预览地址: http://${host}:${port}`);
        
        const npm = process.platform === 'win32' ? 'npm.cmd' : 'npm';
        
        this.serverProcess = spawn(npm, ['run', 'preview'], {
            cwd: this.projectRoot,
            stdio: 'inherit',
            env: {
                ...process.env,
                NUXT_PORT: port,
                NUXT_HOST: host
            }
        });

        this.serverProcess.on('close', (code) => {
            if (code !== 0) {
                this.log(`预览服务器退出，代码: ${code}`, 'error');
            }
        });

        this.serverProcess.on('error', (err) => {
            this.log(`预览服务器启动失败: ${err.message}`, 'error');
        });
    }

    /**
     * 运行服务器
     */
    async run(mode = 'dev') {
        console.log(chalk.magenta('🎯 企业级Agent+RAG知识库系统 - 管理端'));
        console.log(chalk.magenta('=' .repeat(60)));
        
        // 检查Node.js版本
        if (!this.checkNodeVersion()) {
            process.exit(1);
        }

        // 检查依赖
        if (!await this.checkDependencies()) {
            process.exit(1);
        }

        // 检查环境配置
        if (!this.checkEnvironment()) {
            process.exit(1);
        }

        // 检查后端服务
        await this.checkBackendService();

        switch (mode) {
            case 'build':
                // 构建模式
                if (!await this.buildProduction()) {
                    process.exit(1);
                }
                break;
            case 'generate':
                // 静态生成模式
                if (!await this.generateStatic()) {
                    process.exit(1);
                }
                break;
            case 'preview':
                // 预览模式
                await this.previewProduction();
                break;
            case 'dev':
            default:
                // 开发模式
                await this.startDevServer();
                break;
        }
    }
}

// 主函数
function main() {
    const args = process.argv.slice(2);
    const mode = args[0] || 'dev';
    
    if (!['dev', 'build', 'generate', 'preview'].includes(mode)) {
        console.log(chalk.red('❌ 无效的模式'));
        console.log(chalk.yellow('💡 支持的模式: dev, build, generate, preview'));
        process.exit(1);
    }
    
    const server = new AdminAppServer();
    server.run(mode).catch(error => {
        console.error(chalk.red(`❌ 启动失败: ${error.message}`));
        process.exit(1);
    });
}

if (require.main === module) {
    main();
}

module.exports = AdminAppServer;
