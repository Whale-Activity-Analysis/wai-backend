# WAI Backend

Zentrale REST-API für den Whale Activity Index (WAI).
Erstellt mit NestJS. Dient als API für Frontend und externe Services.

## Features
- Whale Activity Score Endpunkte
- Historische Zeitserien (aus der Datenbank)
- Auth (später)
- Endpunkte für Collector-Uploads
- Validation, Caching, Logging

## Tech Stack
- NestJS
- Node.js
- PostgreSQL
- Redis (optional)
- Prisma oder MikroORM (empfohlen)

## Entwicklung
npm install  
npm run start:dev

## ENV Variablen
DATABASE_URL=postgresql://user:pass@localhost:5432/wai
REDIS_URL=redis://localhost:6379
PORT=3000

## Migrationen (Prisma)
npx prisma migrate dev
