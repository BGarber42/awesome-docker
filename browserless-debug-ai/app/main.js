const express = require('express');
const cors = require('cors');
const { v7: uuidv7 } = require('uuid');
const path = require('path');
const fs = require('fs').promises;
const { chromium, firefox, webkit } = require('playwright');
const OpenAI = require('openai');

const app = express();
const PORT = process.env.PORT || 3000;

// Environment variables
const BROWSER_TYPE = process.env.BROWSER_TYPE || 'chrome';
const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
const SCREENSHOT_ENABLED = process.env.SCREENSHOT_ENABLED !== 'false';
const AI_ANALYSIS_ENABLED = process.env.AI_ANALYSIS_ENABLED !== 'false';
const DEBUG_MODE = process.env.DEBUG_MODE === 'true';

// AI Model Configuration
const AI_MODEL = process.env.AI_MODEL || 'gpt-5-mini';
const AI_TEMPERATURE = parseFloat(process.env.AI_TEMPERATURE) || 0.7;
const AI_MAX_TOKENS = parseInt(process.env.AI_MAX_TOKENS) || 1000;
const AI_TIMEOUT = parseInt(process.env.AI_TIMEOUT) || 30000; // 30 seconds timeout

// Model-specific parameter mapping
const MODEL_PARAMS = {
    'gpt-5-mini': {
        max_completion_tokens: AI_MAX_TOKENS
    },
    'gpt-4o': {
        max_tokens: AI_MAX_TOKENS
    },
    'gpt-4o-mini': {
        max_tokens: AI_MAX_TOKENS
    },
    'gpt-4-turbo': {
        max_tokens: AI_MAX_TOKENS
    },
    'gpt-4': {
        max_tokens: AI_MAX_TOKENS
    },
    'gpt-3.5-turbo': {
        max_tokens: AI_MAX_TOKENS
    }
};

// Initialize OpenAI if API key is provided
const openai = OPENAI_API_KEY ? new OpenAI({ apiKey: OPENAI_API_KEY }) : null;

// Logging utility
const log = {
    info: (message, data = null) => {
        console.log(`[INFO] ${message}`, data ? JSON.stringify(data, null, 2) : '');
    },
    debug: (message, data = null) => {
        if (DEBUG_MODE) {
            console.log(`[DEBUG] ${message}`, data ? JSON.stringify(data, null, 2) : '');
        }
    },
    error: (message, error = null) => {
        console.error(`[ERROR] ${message}`, error ? error.stack || error.message : '');
    },
    warn: (message, data = null) => {
        console.warn(`[WARN] ${message}`, data ? JSON.stringify(data, null, 2) : '');
    }
};

// Middleware
app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true }));

// Create directories if they don't exist
const createDirectories = async () => {
    const dirs = ['/app/reports', '/app/screenshots'];
    for (const dir of dirs) {
        try {
            await fs.mkdir(dir, { recursive: true });
        } catch (error) {
            console.log(`Directory ${dir} already exists or cannot be created`);
        }
    }
};

// AI Analysis
class AIAnalyzer {
    constructor() {
        this.openai = openai;
        this.model = AI_MODEL;
        this.temperature = AI_TEMPERATURE;
        this.modelParams = MODEL_PARAMS[this.model] || MODEL_PARAMS['gpt-5-mini'];
    }

    async analyzeError(error, script, logs) {
        if (!this.openai || !AI_ANALYSIS_ENABLED) {
            log.info('AI analysis disabled or OpenAI not configured - using fallback analysis');
            return this.generateBasicAnalysis(error, script);
        }

        log.info(`Starting AI analysis with model: ${this.model}`);
        
        try {
            const prompt = `
Analyze this browser automation error and provide suggestions:

Error: ${error.message}
Script: ${script}
Logs: ${logs}

Please provide:
1. Selector fix suggestions (CSS selectors, XPath alternatives)
2. Wait strategy recommendations
3. Bug report with reproduction steps
4. Suggested fixes

Return as JSON with this structure:
{
  "selector_suggestions": [
    {
      "original": "original_selector",
      "suggestions": ["suggestion1", "suggestion2"],
      "confidence": 0.85
    }
  ],
  "wait_strategy_recommendations": [
    "strategy1",
    "strategy2"
  ],
  "bug_report": {
    "title": "Error title",
    "description": "Error description",
    "reproduction_steps": ["step1", "step2"],
    "suggested_fixes": ["fix1", "fix2"]
  }
}
            `;

            // Create a timeout promise
            const timeoutPromise = new Promise((_, reject) => {
                setTimeout(() => reject(new Error('AI analysis timeout')), AI_TIMEOUT);
            });

            // Create the API call promise
            const apiCallPromise = this.openai.chat.completions.create({
                model: this.model,
                messages: [{ role: "user", content: prompt }],
                response_format: { type: "json_object" },
                ...(this.model !== 'gpt-5-mini' && { temperature: this.temperature }),
                ...this.modelParams
            });

            // Race between timeout and API call
            const completion = await Promise.race([apiCallPromise, timeoutPromise]);

            const content = completion.choices[0].message.content;
            if (!content || content.trim() === '') {
                log.error('OpenAI returned empty response');
                return this.generateBasicAnalysis(error, script);
            }

            // Extract token usage information
            const usage = completion.usage;
            const tokenInfo = usage ? {
                prompt_tokens: usage.prompt_tokens,
                completion_tokens: usage.completion_tokens,
                total_tokens: usage.total_tokens
            } : null;

            try {
                const parsedResponse = JSON.parse(content);
                log.info(`AI analysis completed successfully`, {
                    model: this.model,
                    tokens: tokenInfo,
                    response_size: content.length
                });
                
                // Add source indicator for real AI responses
                return {
                    source: "ai_analysis",
                    model: this.model,
                    timestamp: new Date().toISOString(),
                    token_usage: tokenInfo,
                    ...parsedResponse
                };
            } catch (parseError) {
                log.error('Failed to parse OpenAI response as JSON', parseError);
                log.debug('Raw response content', { content });
                log.info('Falling back to basic analysis due to JSON parse error');
                return this.generateBasicAnalysis(error, script);
            }
        } catch (error) {
            log.error('AI analysis failed', error);
            if (error.message === 'AI analysis timeout') {
                log.warn('AI analysis timed out - falling back to basic analysis');
            } else if (error.response) {
                log.error('OpenAI API error details', error.response.data);
            }
            log.info('Falling back to basic analysis');
            return this.generateBasicAnalysis(error, script);
        }
    }

    generateBasicAnalysis(error, script) {
        return {
            source: "fallback_analysis",
            note: "AI analysis unavailable - using basic fallback analysis",
            selector_suggestions: [
                {
                    original: "unknown",
                    suggestions: [
                        "Use more specific selectors",
                        "Add wait conditions",
                        "Check if element exists before interaction"
                    ],
                    confidence: 0.5
                }
            ],
            bug_report: {
                title: error.message || "Script execution failed",
                description: "Browser automation script encountered an error",
                reproduction_steps: [
                    "Run the provided script",
                    "Check browser console for errors",
                    "Verify element selectors"
                ],
                suggested_fixes: [
                    "Add explicit waits",
                    "Use more robust selectors",
                    "Handle potential errors"
                ]
            }
        };
    }
}

const aiAnalyzer = new AIAnalyzer();

// Script execution
class ScriptExecutor {
    constructor() {
        this.aiAnalyzer = aiAnalyzer;
    }

    async executeScript(script, options = {}) {
        const reportId = uuidv7();
        const startTime = Date.now();
        let browser = null;
        let page = null;
        
        log.info(`Starting script execution`, { reportId, options });
        
        try {
            // Create report directory
            const reportDir = `/app/reports/${reportId}`;
            await fs.mkdir(reportDir, { recursive: true });

            // Create a new browser instance for this request
            log.debug('Creating browser instance', { browser_type: BROWSER_TYPE });
            browser = await this.createBrowser();
            page = await browser.newPage();
            
            // Set timeouts
            await page.setDefaultTimeout(60000);
            await page.setDefaultNavigationTimeout(60000);

            // Execute script
            log.debug('Executing browser script');
            const result = await this.executeBrowserScript(script, page, options);

            // Take screenshot if enabled
            let screenshotPath = null;
            if (options.screenshot !== false) {
                log.debug('Taking screenshot');
                screenshotPath = await this.takeScreenshot(page, reportId);
            }

            // Generate report
            const report = {
                id: reportId,
                status: 'success',
                execution_time: Date.now() - startTime,
                result: result,
                screenshot: screenshotPath,
                timestamp: new Date().toISOString()
            };

            // Save report
            await fs.writeFile(`${reportDir}/report.json`, JSON.stringify(report, null, 2));
            log.info(`Script execution completed successfully`, { 
                reportId, 
                execution_time: report.execution_time 
            });

            return report;

        } catch (error) {
            log.error('Script execution failed', error);

            // Generate error report
            const errorReport = {
                id: reportId,
                status: 'error',
                execution_time: Date.now() - startTime,
                error: {
                    message: error.message,
                    stack: error.stack
                },
                timestamp: new Date().toISOString()
            };

            // AI analysis
            let aiAnalysis = null;
            if (options.ai_analysis !== false) {
                try {
                    log.debug('Starting AI analysis for error');
                    aiAnalysis = await this.aiAnalyzer.analyzeError(error, script, errorReport.error.message);
                    errorReport.ai_analysis = aiAnalysis;
                } catch (aiError) {
                    log.error('AI analysis failed', aiError);
                }
            }

            // Save error report
            const reportDir = `/app/reports/${reportId}`;
            try {
                await fs.mkdir(reportDir, { recursive: true });
                await fs.writeFile(`${reportDir}/report.json`, JSON.stringify(errorReport, null, 2));

                if (aiAnalysis) {
                    await fs.writeFile(`${reportDir}/ai_analysis.json`, JSON.stringify(aiAnalysis, null, 2));
                }
            } catch (fileError) {
                log.error('Failed to save error report', fileError);
            }

            return errorReport;

        } finally {
            // Always close browser and page
            log.debug('Cleaning up browser resources');
            try {
                await this.closeBrowser(browser, page);
            } catch (cleanupError) {
                log.error('Error during browser cleanup', cleanupError);
                // Don't re-throw - this is cleanup, so we don't want to fail the request
            }
        }
    }

    async createBrowser() {
        if (BROWSER_TYPE === 'firefox') {
            return await firefox.launch({
                headless: true,
                args: ['--no-sandbox', '--disable-setuid-sandbox']
            });
        } else {
            return await chromium.launch({
                headless: true,
                args: ['--no-sandbox', '--disable-setuid-sandbox']
            });
        }
    }

    async closeBrowser(browser, page) {
        try {
            if (page) {
                try {
                    await page.close();
                } catch (error) {
                    log.warn('Error closing page', error);
                }
            }
            if (browser) {
                try {
                    await browser.close();
                } catch (error) {
                    log.warn('Error closing browser', error);
                }
            }
        } catch (error) {
            log.error('Error in closeBrowser', error);
        }
    }

    async takeScreenshot(page, reportId) {
        if (!SCREENSHOT_ENABLED || !page) return null;
        
        try {
            const screenshotPath = `/app/screenshots/${reportId}.png`;
            await page.screenshot({ path: screenshotPath, fullPage: true });
            log.debug('Screenshot taken successfully', { path: screenshotPath });
            return screenshotPath;
        } catch (error) {
            log.error('Failed to take screenshot', error);
            return null;
        }
    }

    async executeBrowserScript(script, page, options) {
        // Determine if script needs page object (contains page.goto, page.click, etc.)
        const needsPageObject = /page\.(goto|click|fill|waitForSelector|evaluate|screenshot|title|url|textContent|inputValue)/.test(script);
        
        if (needsPageObject) {
            // Execute script in Node.js context with page object
            const safeScript = `
                (async () => {
                    try {
                        ${script}
                    } catch (error) {
                        throw new Error('Script execution failed: ' + error.message);
                    }
                })();
            `;
            
            try {
                // Use Function constructor to execute the script with page context
                const scriptFunction = new Function('page', safeScript);
                return await scriptFunction(page);
            } catch (error) {
                log.error('Script execution failed in Node.js context', error);
                throw error;
            }
        } else {
            // Execute script in browser context (DOM manipulation)
            const safeScript = `
                (async () => {
                    try {
                        ${script}
                    } catch (error) {
                        throw new Error('Script execution failed: ' + error.message);
                    }
                })();
            `;
            
            try {
                return await page.evaluate(safeScript);
            } catch (error) {
                log.error('Script execution failed in browser context', error);
                throw error;
            }
        }
    }
}

const scriptExecutor = new ScriptExecutor();

// Routes
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        browser_type: BROWSER_TYPE,
        features: {
            screenshot: SCREENSHOT_ENABLED,
            ai_analysis: AI_ANALYSIS_ENABLED && !!openai
        },
        ai_config: {
            model: AI_MODEL,
            temperature: AI_TEMPERATURE,
            max_tokens: AI_MAX_TOKENS,
            timeout_ms: AI_TIMEOUT,
            available_models: Object.keys(MODEL_PARAMS)
        }
    });
});

app.get('/', (req, res) => {
    res.json({
        name: 'Browserless Debug AI',
        version: '1.0.0',
        description: 'Headless browser debugging container with AI-assisted failure analysis',
        endpoints: {
            health: '/health',
            run_script: '/run-script',
            reports: '/reports',
            reports_by_id: '/reports/:id'
        },
        features: {
            browser_type: BROWSER_TYPE,
            screenshot_enabled: SCREENSHOT_ENABLED,
            ai_analysis_enabled: AI_ANALYSIS_ENABLED && !!openai
        }
    });
});

app.post('/run-script', async (req, res) => {
    try {
        const { script, options = {} } = req.body;

        if (!script) {
            return res.status(400).json({
                error: 'Script is required'
            });
        }

        log.info('Received script execution request', { 
            script_length: script.length,
            options 
        });

        const result = await scriptExecutor.executeScript(script, options);
        
        res.json(result);

    } catch (error) {
        log.error('Error in /run-script endpoint', error);
        res.status(500).json({
            error: 'Failed to execute script',
            message: error.message
        });
    }
});

app.get('/reports', async (req, res) => {
    try {
        const reportsDir = '/app/reports';
        const reports = [];

        try {
            const reportDirs = await fs.readdir(reportsDir);
            
            for (const dir of reportDirs) {
                const reportPath = path.join(reportsDir, dir, 'report.json');
                try {
                    const reportData = await fs.readFile(reportPath, 'utf8');
                    const report = JSON.parse(reportData);
                    reports.push({
                        id: report.id,
                        status: report.status,
                        timestamp: report.timestamp,
                        execution_time: report.execution_time
                    });
                } catch (error) {
                    console.log(`Could not read report ${dir}:`, error.message);
                }
            }
        } catch (error) {
            console.log('No reports directory found');
        }

        res.json({
            reports: reports.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
        });

    } catch (error) {
        console.error('Error in /reports:', error);
        res.status(500).json({
            error: 'Failed to get reports',
            message: error.message
        });
    }
});

app.get('/reports/:id', async (req, res) => {
    try {
        const { id } = req.params;
        const reportPath = `/app/reports/${id}/report.json`;

        try {
            const reportData = await fs.readFile(reportPath, 'utf8');
            const report = JSON.parse(reportData);

            // Check for AI analysis
            const aiAnalysisPath = `/app/reports/${id}/ai_analysis.json`;
            try {
                const aiData = await fs.readFile(aiAnalysisPath, 'utf8');
                report.ai_analysis = JSON.parse(aiData);
            } catch (error) {
                // AI analysis not available
            }

            res.json(report);

        } catch (error) {
            res.status(404).json({
                error: 'Report not found',
                id: id
            });
        }

    } catch (error) {
        console.error('Error in /reports/:id:', error);
        res.status(500).json({
            error: 'Failed to get report',
            message: error.message
        });
    }
});

// Error handling middleware
app.use((error, req, res, next) => {
    console.error('Unhandled error:', error);
    res.status(500).json({
        error: 'Internal server error',
        message: error.message
    });
});

// 404 handler
app.use((req, res) => {
    res.status(404).json({
        error: 'Endpoint not found',
        path: req.path
    });
});

// Initialize and start server
const startServer = async () => {
    try {
        await createDirectories();
        
        const server = app.listen(PORT, () => {
            log.info(`Browserless Debug AI server started`, {
                port: PORT,
                browser_type: BROWSER_TYPE,
                features: {
                    screenshot: SCREENSHOT_ENABLED,
                    ai_analysis: AI_ANALYSIS_ENABLED && !!openai
                },
                ai_config: {
                    model: AI_MODEL,
                    temperature: AI_TEMPERATURE,
                    max_tokens: AI_MAX_TOKENS,
                    timeout_ms: AI_TIMEOUT
                }
            });
        });

        // Graceful shutdown
        const gracefulShutdown = async (signal) => {
            log.info(`Received ${signal}. Starting graceful shutdown...`);
            
            // Close server
            server.close(() => {
                log.info('Server closed gracefully');
                process.exit(0);
            });
            
            // Force exit after 30 seconds
            setTimeout(() => {
                log.error('Forced shutdown after timeout');
                process.exit(1);
            }, 30000);
        };

        // Handle shutdown signals
        process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
        process.on('SIGINT', () => gracefulShutdown('SIGINT'));
        
        // Handle uncaught exceptions
        process.on('uncaughtException', (error) => {
            log.error('Uncaught Exception:', error);
            process.exit(1);
        });
        
        process.on('unhandledRejection', (reason, promise) => {
            log.error('Unhandled Rejection at:', promise, 'reason:', reason);
            // Don't exit immediately for unhandled rejections, just log them
            // This prevents container crashes from minor async issues
        });

    } catch (error) {
        console.error('Failed to start server:', error);
        process.exit(1);
    }
};

startServer();
