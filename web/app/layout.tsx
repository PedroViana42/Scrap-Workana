import type { Metadata } from "next";
import "./globals.css";
import { Header } from "@/components/layout/header";

export const metadata: Metadata = {
  title: "Radar",
  description: "Agregador de oportunidades com ranking de relevancia.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body>
        <Header />
        <main className="container-shell py-6">{children}</main>
      </body>
    </html>
  );
}
