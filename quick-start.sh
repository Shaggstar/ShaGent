#!/bin/bash

set -e

echo "🚀 Better Self - Quick Start Setup"
echo "=================================="
echo ""

echo "Checking prerequisites..."

if ! command -v node >/dev/null 2>&1; then
  echo "❌ Node.js not found. Please install Node.js 18+ first."
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "❌ npm not found. Please install npm."
  exit 1
fi

echo "✅ Node.js and npm detected."
echo ""

echo "📦 Setting up web app..."
pushd web-app >/dev/null

if [ ! -f package.json ]; then
  echo "❌ package.json not found in web-app. Aborting."
  exit 1
fi

npm install

if [ ! -f .env.local ]; then
  cp .env.local.example .env.local
  echo "📝 Created web-app/.env.local from template. Add your Supabase + OpenAI keys!"
fi

popd >/dev/null
echo "✅ Web app ready."
echo ""

echo "🔌 Setting up Obsidian plugin..."
pushd obsidian-plugin >/dev/null

if [ ! -f package.json ]; then
  echo "❌ package.json not found in obsidian-plugin. Aborting."
  exit 1
fi

npm install
npm run build

popd >/dev/null
echo "✅ Obsidian plugin built."
echo ""

cat <<'EOF'
==================================
✅ Setup Complete!
==================================

Next steps:

1. Configure Supabase:
   - Create a project at https://supabase.com
   - Run supabase/migrations/001_initial_schema.sql
   - Copy your project URL and anon key

2. Configure the web app:
   - Edit web-app/.env.local with Supabase + OpenAI keys
   - Start with: cd web-app && npm run dev

3. Install the Obsidian plugin:
   - Copy obsidian-plugin/main.js and manifest.json into YOUR_VAULT/.obsidian/plugins/better-self/
   - Reload Obsidian, enable Better Self, and paste your Supabase details

4. Kick off the workflow:
   - In Obsidian: "Better Self: Create Morning Check-In" then "Generate Today's Tasks"
   - In the browser: http://localhost:3000/focus for focus mode, /interview for mock interviews

See SETUP.md for more detail. Happy building!
EOF
