# WebPDTool Frontend

Vue 3 frontend application for WebPDTool.

## Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Run development server:
```bash
npm run dev
```

3. Build for production:
```bash
npm run build
```

## Technology Stack

- **Framework**: Vue 3 (Composition API)
- **UI Library**: Element Plus
- **State Management**: Pinia
- **Router**: Vue Router
- **HTTP Client**: Axios
- **Build Tool**: Vite

## Directory Structure

```
frontend/
├── public/           # Static assets
├── src/
│   ├── api/         # API calls
│   ├── assets/      # Images, styles
│   ├── components/  # Reusable components
│   ├── router/      # Vue Router configuration
│   ├── stores/      # Pinia stores
│   ├── views/       # Page components
│   ├── utils/       # Utility functions
│   ├── App.vue      # Root component
│   └── main.js      # Application entry point
├── package.json
└── vite.config.js
```
