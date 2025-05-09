FROM node:18-alpine

WORKDIR /app

# Define build arguments
ARG VITE_API_URL
ARG NODE_ENV

# Set environment variables
ENV NODE_ENV=${NODE_ENV}
ENV VITE_API_URL=${VITE_API_URL}

COPY package*.json ./

RUN npm install

# Create environment files
RUN echo "VITE_API_URL=${VITE_API_URL}" > .env.development

COPY . .

# Ensure postcss.config.js uses CommonJS format
RUN if grep -q "export default" /app/postcss.config.js; then \
    sed -i 's/export default/module.exports =/' /app/postcss.config.js; \
fi

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
