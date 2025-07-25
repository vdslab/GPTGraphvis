import { type RouteConfig, index, route } from "@react-router/dev/routes";

export default [
  index("routes/home.tsx"),
  route("/auth", "routes/auth.tsx"),
  route("/login", "routes/auth.tsx"), // /loginも/authと同じコンポーネントを使用
  route("/register", "routes/auth.tsx"), // /registerも/authと同じコンポーネントを使用
  route("/dashboard", "routes/dashboard.tsx"),
] satisfies RouteConfig;
