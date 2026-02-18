FROM node:20-slim

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy built files
COPY dist/ ./dist/

# Create non-root user
RUN useradd -m -u 1000 parceldata && chown -R parceldata:parceldata /app
USER parceldata

# Run MCP server
CMD ["node", "dist/index.js"]
