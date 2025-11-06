FROM node:20-alpine
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* /app/
RUN npm install --legacy-peer-deps || true
COPY frontend /app
EXPOSE 5173
CMD ["npm","run","dev","--","--host"]






