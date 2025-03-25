import { ReactNode } from "react";
import { Sidebar } from "../Sidebar/Sidebar";

interface LayoutProps {
  children: ReactNode;
  activePage?: string;
}

export const Layout = ({ children, activePage }: LayoutProps) => {
  console.log("Layout rendering, activePage:", activePage);
  return (
    <div className="container">
      <Sidebar activePage={activePage} />
      <main className="content">
        <header className="content__header">
          <h1 className="content__title">
            {activePage?.charAt(0).toUpperCase() + activePage?.slice(1)}
          </h1>
        </header>
        <div className="content__body">{children}</div>
      </main>
    </div>
  );
};
