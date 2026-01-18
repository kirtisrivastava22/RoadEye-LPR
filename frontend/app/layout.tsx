import "./globals.css";
import Sidebar from "../components/Sidebar";

export const metadata = {
  title: "RoadEye LPR",
  description: "License Plate Recognition System",
  icons: {
    icon: "/icon.png",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full">
      <body className="flex min-h-screen bg-[#0B0F14]">
  <Sidebar /> {/* w-64 */}
  <main className="flex-1 p-8 overflow-y-auto"> {/* flex-1 takes the remaining width */}
    {children}
  </main>
</body>
    </html>
  )
}

