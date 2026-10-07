FROM node:22-alpine
WORKDIR /app
COPY frontend/web/package.json frontend/web/package-lock.json ./
RUN npm ci
COPY frontend/web/ ./
EXPOSE 5173
CMD ["npm", "run", "dev"]
