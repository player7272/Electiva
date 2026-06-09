FROM node:18-alpine

WORKDIR /app

# Copia package.json primero (aprovecha caché de Docker)
COPY package.json package-lock.json* ./

RUN npm install

# Copia el resto del código
COPY . .

EXPOSE 3000

# Usa nodemon en desarrollo para hot-reload
CMD ["node", "src/server.js"]
