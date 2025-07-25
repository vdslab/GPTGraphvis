FROM node:20-alpine

WORKDIR /app

# Copy package.json (without package-lock.json to avoid npm bug)
COPY package.json ./

# Install dependencies (npm will create a new package-lock.json)
RUN npm install

# Copy the rest of the application
COPY . .

# Build the application
RUN npm run build

# Expose the port the app will run on
EXPOSE 3000

# Command to run the application using React Router's built-in server
CMD ["npm", "start"]