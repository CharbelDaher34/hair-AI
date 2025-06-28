# Build stage
FROM node:18-alpine AS build

WORKDIR /app

COPY package.json .
COPY package-lock.json .

RUN npm install

COPY . .

# Build the application - API calls will be proxied by nginx
RUN npm run build

# Production stage with nginx
FROM nginx:alpine

# install gettext for envsubst
RUN apk add --no-cache gettext

# Copy built application to nginx html directory
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/templates/default.conf.template

EXPOSE 8080

CMD ["/bin/sh", "-c", "envsubst '${PROXY_PASS_URL}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
