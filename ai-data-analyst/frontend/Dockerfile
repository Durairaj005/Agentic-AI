# Stage 1: Build static React SPA production assets
FROM node:20-alpine AS build

WORKDIR /app

# Copy package configurations and install dependencies using clean install
COPY package.json package-lock.json ./
RUN npm ci

# Copy source files and execute production bundler
COPY . .
ENV VITE_API_URL=""
RUN npm run build

# Stage 2: Serve production assets via Nginx
FROM nginx:1.25-alpine

# Copy reverse proxy Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy build files from Stage 1 to Nginx default public folder
COPY --from=build /app/dist /usr/share/nginx/html

# Expose Nginx container port
EXPOSE 80

# Run Nginx in the foreground
CMD ["nginx", "-g", "daemon off;"]
