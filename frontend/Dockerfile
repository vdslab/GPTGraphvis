FROM node:20-alpine AS development-dependencies-env
COPY package*.json /app/
WORKDIR /app
RUN npm ci

FROM node:20-alpine AS build-env
COPY . /app/
COPY --from=development-dependencies-env /app/node_modules /app/node_modules
WORKDIR /app
RUN npm run build

FROM node:20-alpine
RUN npm install -g serve
COPY --from=build-env /app/build/client /app/client
WORKDIR /app
EXPOSE 3000
CMD ["serve", "-s", "client", "-l", "3000"]