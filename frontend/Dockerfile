# --- build stage ---
FROM node:20-alpine AS build
WORKDIR /app

# 잠금파일이 있으면 함께 복사해서 npm ci 사용
COPY package.json package-lock.json ./
RUN npm ci

# 소스 복사 및 빌드
COPY . .
# API 베이스 경로 전달 (네가 쓰던 ARG/ENV 유지)
ARG VITE_API_BASE=/api
ENV VITE_API_BASE=$VITE_API_BASE
RUN npm run build

# --- serve stage ---
FROM nginx:1.27-alpine
# nginx.conf 경로는 프로젝트에 맞게 유지
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx","-g","daemon off;"]