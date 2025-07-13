#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// Get the Railway URL from command line argument
const railwayUrl = process.argv[2];

if (!railwayUrl) {
    console.error('Usage: node update-api-url.js <RAILWAY_URL>');
    console.error('Example: node update-api-url.js https://my-app.railway.app');
    process.exit(1);
}

// Remove trailing slash if present
const cleanUrl = railwayUrl.replace(/\/$/, '');
const apiUrl = `${cleanUrl}/api`;

const scriptPath = path.join(__dirname, 'frontend', 'script.js');

try {
    // Read the current script
    let scriptContent = fs.readFileSync(scriptPath, 'utf8');
    
    // Replace the API base URL
    const updatedContent = scriptContent.replace(
        /this\.apiBase\s*=\s*['"`][^'"`]*['"`];/,
        `this.apiBase = '${apiUrl}';`
    );
    
    // Write back to file
    fs.writeFileSync(scriptPath, updatedContent);
    
    console.log('✅ Successfully updated API endpoint!');
    console.log(`📍 New API URL: ${apiUrl}`);
    console.log('🚀 You can now deploy to Netlify');
    
} catch (error) {
    console.error('❌ Error updating API endpoint:', error.message);
    process.exit(1);
} 