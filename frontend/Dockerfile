FROM node:20-alpine

WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm ci
# Explicitly install react-force-graph-2d to ensure it's available
RUN npm install react-force-graph-2d@1.27.1

# Copy the rest of the application
COPY . .

# Build the application
RUN npm run build

# Install a simple http server to serve the static content
RUN npm install -g serve

# Copy serve.json configuration for API proxying
COPY serve.json ./dist/

# Expose the port the app will run on
EXPOSE 3000

# Command to run the application
CMD ["serve", "-s", "dist", "-l", "3000"]
