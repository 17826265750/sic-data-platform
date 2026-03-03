# Frontend Dockerfile
# Build stage
FROM node:20-alpine as build

# Install dependencies for building
RUN apk add --no-cache libc6-compat

# Create non-root user for build
RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 --ingroup nodejs builduser

WORKDIR /app

# Copy package files
COPY --chown=builduser:nodejs package.json package-lock.json* ./

# Install dependencies
RUN npm install --legacy-peer-deps

# Copy source code
COPY --chown=builduser:nodejs . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Install curl for health check
RUN apk add --no-cache curl

# Create non-root user for nginx
RUN addgroup --system --gid 1001 nginx-user \
    && adduser --system --uid 1001 --ingroup nginx-user nginx-user \
    && chown -R nginx-user:nginx-user /var/cache/nginx /var/log/nginx /etc/nginx/conf.d \
    && touch /var/run/nginx.pid \
    && chown -R nginx-user:nginx-user /var/run/nginx.pid

# Copy built files
COPY --from=build --chown=nginx-user:nginx-user /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY --chown=nginx-user:nginx-user nginx.conf /etc/nginx/conf.d/default.conf

# Switch to non-root user
USER nginx-user

# Expose port (non-root can use ports > 1024)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Labels for metadata
LABEL maintainer="SIC Data Platform Team" \
      version="1.0.0" \
      description="SiC Data Processing Platform Frontend"

# Start nginx (use port 8080 for non-root)
CMD ["nginx", "-g", "daemon off;"]