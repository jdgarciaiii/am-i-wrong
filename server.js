const express = require('express');
const cors = require('cors');
const fetch = require('node-fetch');
const path = require('path');

const app = express();
const PORT = 5000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('static'));

// Your Anthropic API key
const ANTHROPIC_API_KEY = "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";

// Rate limiting (simple in-memory)
const rateLimitStore = {};

function rateLimitCheck(clientIp) {
    const currentTime = Math.floor(Date.now() / 1000);
    
    if (!rateLimitStore[clientIp]) {
        rateLimitStore[clientIp] = [];
    }
    
    // Remove old requests (older than 1 minute)
    rateLimitStore[clientIp] = rateLimitStore[clientIp].filter(
        time => currentTime - time < 60
    );
    
    if (rateLimitStore[clientIp].length >= 10) {
        return false;
    }
    
    rateLimitStore[clientIp].push(currentTime);
    return true;
}

function validateInput(text, maxLength = 800) {
    if (typeof text !== 'string') {
        throw new Error('Invalid input type');
    }
    
    // Remove potentially harmful content
    text = text.replace(/[<>"']/g, '');
    
    // Length validation
    if (text.length > maxLength) {
        throw new Error(`Text too long (max ${maxLength} characters)`);
    }
    
    if (text.trim().length < 10) {
        throw new Error('Text too short (minimum 10 characters)');
    }
    
    return text.trim();
}

app.post('/api/verdict', async (req, res) => {
    try {
        const clientIp = req.ip || req.connection.remoteAddress;
        
        // Rate limiting
        if (!rateLimitCheck(clientIp)) {
            return res.status(429).json({
                error: 'Too many requests. Please try again later.'
            });
        }
        
        const { sideA, sideB } = req.body;
        
        if (!sideA || !sideB) {
            return res.status(400).json({
                error: 'Both sides are required'
            });
        }
        
        // Validate inputs
        try {
            const validatedSideA = validateInput(sideA);
            const validatedSideB = validateInput(sideB);
        } catch (error) {
            return res.status(400).json({
                error: error.message
            });
        }
        
        const prompt = `You are an impartial judge. Two people are in a conflict.

Person A: ${sideA}

Person B: ${sideB}

Respond ONLY with valid JSON, no extra text:
{"winner":"A","scoreA":76,"scoreB":24,"ruling":"Two sentences explaining your decision.","advice":"One sentence of actionable advice."}

Rules: winner = "A", "B", or "tie". scoreA + scoreB = 100.`;

        const response = await fetch('https://api.anthropic.com/v1/messages', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': ANTHROPIC_API_KEY,
                'anthropic-version': '2023-06-01'
            },
            body: JSON.stringify({
                model: 'claude-3-haiku-20240307',
                max_tokens: 1000,
                messages: [{ role: 'user', content: prompt }]
            })
        });

        if (!response.ok) {
            throw new Error(`API request failed: ${response.status}`);
        }

        const result = await response.json();
        const text = result.content?.filter(c => c.type === 'text')
            .map(c => c.text).join('') || '';

        // Extract JSON
        const jsonMatch = text.match(/\{[\s\S]*\}/);
        if (!jsonMatch) {
            throw new Error('No JSON found in response');
        }

        let verdictData;
        try {
            verdictData = JSON.parse(jsonMatch[0]);
        } catch (e) {
            throw new Error('Could not parse JSON response');
        }

        // Validate response
        const requiredFields = ['winner', 'scoreA', 'scoreB', 'ruling', 'advice'];
        for (const field of requiredFields) {
            if (!(field in verdictData)) {
                throw new Error(`Missing field: ${field}`);
            }
        }

        // Validate scores
        if (!Number.isInteger(verdictData.scoreA) || !Number.isInteger(verdictData.scoreB)) {
            throw new Error('Invalid score format');
        }

        if (verdictData.scoreA + verdictData.scoreB !== 100) {
            throw new Error('Invalid score totals');
        }

        res.json(verdictData);

    } catch (error) {
        console.error('Error:', error);
        res.status(500).json({
            error: error.message || 'Internal server error'
        });
    }
});

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'static', 'index.html'));
});

app.listen(PORT, '127.0.0.1', () => {
    console.log('🚀 Am I Wrong? app is running!');
    console.log(`📍 http://127.0.0.1:${PORT}`);
    console.log('📱 Open the URL in your browser');
});
