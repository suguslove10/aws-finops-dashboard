FROM node:18-alpine

# Create app directory
WORKDIR /app

# Copy package files first for better caching
COPY frontend/aws-finops-ui/package*.json ./

# Install dependencies
RUN npm install

# Copy frontend source code
COPY frontend/aws-finops-ui/src ./src
COPY frontend/aws-finops-ui/public ./public
COPY docker-next.config.js ./next.config.js
COPY frontend/aws-finops-ui/tsconfig.json ./
COPY frontend/aws-finops-ui/postcss.config.mjs ./
COPY frontend/aws-finops-ui/eslint.config.mjs ./

# Build the application for production with ESLint checks disabled
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# Copy public directory to the standalone directory for static files
RUN cp -R public .next/standalone/public
RUN cp -R .next/static .next/standalone/.next/static

# Expose the frontend port
EXPOSE 3000

# Set environment variable for production
ENV NODE_ENV=production

# Use node to run the standalone server instead of npm start
CMD ["node", ".next/standalone/server.js"] 