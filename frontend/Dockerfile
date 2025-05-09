FROM node:18-alpine

WORKDIR /app

# Set environment variables
ENV NODE_ENV=development
# API URL will be passed from docker-compose

COPY package*.json ./

RUN npm install

# Create environment files
RUN echo "VITE_API_URL=http://localhost:8000" > .env.development

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
