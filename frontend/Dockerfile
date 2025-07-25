FROM node:20-alpine

WORKDIR /app

# Copy package.json and package-lock.json if available
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production=false

# Copy the rest of the application
COPY . .

# Clean any previous build artifacts
RUN rm -rf build

# Generate React Router types only
RUN npx react-router typegen

# Build the application with fresh cache
RUN npm run build

# Expose the port the app will run on
EXPOSE 3000

# Command to run the application using React Router's built-in server
CMD ["npm", "start"]