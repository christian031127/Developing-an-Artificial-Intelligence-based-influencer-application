# syntax=docker/dockerfile:1.6
FROM --platform=$BUILDPLATFORM node:20-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . /app
EXPOSE 5173
CMD ["npm","run","dev","--","--host","0.0.0.0"]