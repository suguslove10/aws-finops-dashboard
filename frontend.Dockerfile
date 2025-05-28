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

# Expose the frontend port
EXPOSE 3000

# Set environment variable for production
ENV NODE_ENV=production

# Run the Next.js server
CMD ["npm", "run", "start"] 