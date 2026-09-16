FROM node:22-alpine
WORKDIR /app
COPY frontend/web/package.json ./
RUN npm install
COPY frontend/web/ ./
EXPOSE 5173
CMD ["npm", "run", "dev"]
