import { type RouteConfig, index, route } from "@react-router/dev/routes";

// 各ルートに一意のIDを割り当てる
const homeRoute = index("routes/home.tsx");
homeRoute.id = "home";

const authRoute = route("/auth", "routes/auth.tsx");
authRoute.id = "auth";

const loginRoute = route("/login", "routes/auth.tsx"); // /loginも/authと同じコンポーネントを使用
loginRoute.id = "login";

const registerRoute = route("/register", "routes/auth.tsx"); // /registerも/authと同じコンポーネントを使用
registerRoute.id = "register";

const dashboardRoute = route("/dashboard", "routes/dashboard.tsx");
dashboardRoute.id = "dashboard";

export default [
  homeRoute,
  authRoute,
  loginRoute,
  registerRoute,
  dashboardRoute,
] satisfies RouteConfig;
