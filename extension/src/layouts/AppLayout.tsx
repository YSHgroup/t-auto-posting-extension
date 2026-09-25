import { NavLink, Outlet } from "react-router-dom";

const links = [
  ["", "Dashboard"],
  ["groups", "Groups"],
  ["feed", "Feed"],
  ["posts", "Posts"],
  ["scheduler", "Scheduler"],
  ["history", "History"],
  ["notifications", "Notifications"],
  ["opportunities", "Opportunities"],
  ["settings", "Settings"],
];

export function AppLayout() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <h1>Telegram Auto Bot</h1>
        <nav>
          {links.map(([path, label]) => (
            <NavLink
              key={path}
              to={path === "" ? "/" : `/${path}`}
              end={path === ""}
              className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
            >
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
