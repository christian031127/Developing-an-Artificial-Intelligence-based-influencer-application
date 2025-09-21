import Sidebar from "../components/Sidebar";
import Topbar from "../components/Topbar";

export default function Layout({ children, page, onNavigate }) {
  return (
    <div className="min-h-screen grid grid-cols-12">
      <aside className="col-span-12 md:col-span-2 border-r bg-white">
        <Sidebar current={page} onNavigate={onNavigate} />
      </aside>
      <main className="col-span-12 md:col-span-10">
        <Topbar />
        <div className="p-4 md:p-6">{children}</div>
      </main>
    </div>
  );
}
