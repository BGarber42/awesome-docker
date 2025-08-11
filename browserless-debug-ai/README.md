# Browserless Debugging Sandbox with AI

A headless browser debugging container with AI-assisted failure analysis for Playwright scripts.

## Quick Start

```bash
# Start with default settings (Chrome)
docker compose up -d

# Start with OpenAI AI analysis
OPENAI_API_KEY=your_key docker compose up -d

# Start with Firefox
BROWSER_TYPE=firefox docker compose up -d
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BROWSER_TYPE` | `chrome` | Browser engine (`chrome`, `firefox`) |
| `SCREENSHOT_ENABLED` | `true` | Enable screenshot capture |
| `AI_ANALYSIS_ENABLED` | `true` | Enable AI error analysis |
| `OPENAI_API_KEY` | - | OpenAI API key for AI analysis |
| `AI_MODEL` | `gpt-4o` | OpenAI model for analysis |
| `AI_TEMPERATURE` | `0.7` | AI response creativity (0.0-2.0) |
| `AI_MAX_TOKENS` | `1000` | Max tokens for AI responses |
| `AI_TIMEOUT` | `30000` | AI analysis timeout (ms) |

## API Endpoints

### Health Check
```bash
curl http://localhost:3000/health
```

### Execute Script
```bash
curl -X POST http://localhost:3000/run-script \
  -H "Content-Type: application/json" \
  -d '{
    "script": "await page.goto(\"https://example.com\"); return { title: await page.title() };",
    "options": {
      "screenshot": true,
      "ai_analysis": true
    }
  }'
```

### Get Reports
```bash
curl http://localhost:3000/reports
curl http://localhost:3000/reports/{report_id}
```

## Example Scripts

### Basic Navigation
```javascript
await page.goto('https://example.com');
const title = await page.title();
return { title, url: page.url() };
```

### Form Interaction
```javascript
await page.goto('https://example.com/form');
await page.fill('#username', 'testuser');
await page.click('#submit');
await page.waitForSelector('.success');
return { message: await page.textContent('.success') };
```

### Error Handling
```javascript
try {
  await page.click('#nonexistent');
} catch (error) {
  throw new Error('Element not found - will trigger AI analysis');
}
```

## Output Structure

Reports are saved in `/app/reports/{report_id}/`:
- `report.json` - Main execution report
- `ai_analysis.json` - AI analysis results (if enabled)
- Screenshots saved to `/app/screenshots/`

### Report Example
```json
{
  "id": "uuid",
  "status": "success|error",
  "execution_time": 1234,
  "result": "script return value",
  "screenshot": "/app/screenshots/uuid.png",
  "timestamp": "2024-01-01T00:00:00.000Z",
  "ai_analysis": {
    "source": "ai_analysis",
    "model": "gpt-4o",
    "token_usage": {
      "prompt_tokens": 375,
      "completion_tokens": 266,
      "total_tokens": 641
    },
    "selector_suggestions": [...],
    "bug_report": {...}
  }
}
```

## Features

- **Multi-browser Support**: Chrome, Firefox via Playwright
- **AI Error Analysis**: OpenAI-powered failure analysis with token tracking
- **Screenshot Capture**: Full-page screenshots for debugging
- **Report Management**: Organized reports with metadata
- **Health Monitoring**: Built-in health checks and logging
