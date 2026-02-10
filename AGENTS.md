# AGENTS.md

## Build/Lint/Test Commands

### General Commands
- `npm run dev` - Start development server (Electron + Nuxt)
- `npm run test:unit` - Run unit tests for the Electron app with Jest
- `npm run build-unstable` - Build unstable release version
- `npm run build-prod` - Build production release version
- `npm run build-beta96` - Build beta 96 release version

### UI Commands (in ui/ directory)
- `npm run test:unit` - Run unit tests for the Vue components
- `npm run lint` - Lint code with ESLint
- `npm run build` - Build production bundle

### Running Single Tests
- `npm run test:unit` or `jest -c jest.config.js` (in electron/ directory) for running all unit tests in the Electron app.
- `npm run test:unit-no-prebuild` - Run tests without pre-build step.

## Code Style Guidelines

### Imports
- Always use named imports (`import {foo} from 'bar'`) instead of default imports unless specifically required.
- Prefer consistent import styles throughout the codebase (e.g., all named or all default).
- Organize imports in order: external libraries, core modules, internal modules.

### Formatting
- Follow Prettier's formatting rules for consistent styling.
- Use 2-space indentation for JSX and Vue files.
- Avoid trailing spaces at end of lines.

### Types
- Define types using TypeScript where applicable (e.g., React components).
- Use generic type definitions when needed to support better typing practices.
- Prefer strongly-typed interfaces over loosely typed functions.

### Naming Conventions
- Use camelCase for all JavaScript/TypeScript variables and function names.
- Prefix private methods with underscore (`_`).
- Use PascalCase for component names (small caps).

### Error Handling
- Always wrap asynchronous operations in try/catch blocks to handle errors gracefully.
- Implement proper error logging using electron-log or similar tools.

## Cursor Rules

None defined yet.

## Copilot Instructions

None defined yet.