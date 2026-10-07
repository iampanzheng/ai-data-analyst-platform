FROM node:22-alpine

WORKDIR /app
RUN chown -R node:node /app

USER node

COPY --chown=node:node frontend/web/package.json frontend/web/package-lock.json ./
RUN npm ci
COPY --chown=node:node frontend/web/ ./

EXPOSE 5173
CMD ["npm", "run", "dev"]
