'use client';
import Link from "next/link"
import { ReactNode } from "react"
import { Camera, Image, Video, Clock } from "lucide-react"

export default function Sidebar() {
  return (
    <aside className="w-64 bg-[#111827] p-6 border-r border-cyan-500/20">
      <h1 className="text-2xl font-bold text-cyan-400 mb-8">
        RoadEye AI
      </h1>

      <nav className="space-y-4">
        <NavItem href="/" icon={<Camera />} label="Live Camera" />
        <NavItem href="/image" icon={<Image />} label="Image" />
        <NavItem href="/video" icon={<Video />} label="Video" />
        <NavItem href="/history" icon={<Clock />} label="History" />
      </nav>
    </aside>
  )
}

type NavItemProps = {
  href: string
  icon: ReactNode
  label: string
}

function NavItem({ href, icon, label }: NavItemProps) {
  return (
    <Link
      href={href}
      className="flex items-center gap-3 p-3 rounded-lg hover:bg-cyan-500/10 transition"
    >
      {icon}
      <span>{label}</span>
    </Link>
  )
}
