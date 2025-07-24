import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';

// Get __dirname equivalent in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;
const isDev = process.env.NODE_ENV !== 'production';

// Serve static files from the parent directory (project root)
app.use(express.static(path.join(__dirname, '..')));

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, '..', 'index.html'));
});

// Simple development endpoint to check if server is running
app.get('/health', (req, res) => {
  res.json({ status: 'ok', env: isDev ? 'development' : 'production' });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`🚀 CYOA Server running at http://localhost:${PORT}`);
  console.log(`📁 Serving files from: ${path.join(__dirname, '..')}`);
  if (isDev) {
    console.log('🔄 Development mode - use "npm run dev" for auto-restart');
  }
});