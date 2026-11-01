FROM node:20-alpine
WORKDIR /service
ENV NODE_ENV=production
COPY package*.json ./
RUN npm install --omit=dev
COPY src ./src
EXPOSE 3001
USER node
CMD ["node", "src/server.js"]
