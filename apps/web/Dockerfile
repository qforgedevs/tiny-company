# Multi-stage build for Tiny Company Web

# Stage 1: Builder
FROM node:20-alpine as builder

WORKDIR /build

# Copy package files
COPY apps/web/package.json apps/web/package-lock.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY apps/web/. .

# Build application
RUN npm run build && npm run typecheck

# Stage 2: Runtime
FROM node:20-alpine

WORKDIR /app

# Install runtime dependencies
RUN npm install -g serve

# Copy built application from builder
COPY --from=builder /build/.next /app/.next
COPY --from=builder /build/public /app/public
COPY --from=builder /build/package.json /app/package.json
COPY --from=builder /build/package-lock.json /app/package-lock.json

# Create non-root user
RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose web port
EXPOSE 3000

# Environment variables
ENV NODE_ENV=production \
    NEXT_PUBLIC_API_URL=http://localhost:8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})"

# Start application
CMD ["npm", "run", "start"]
