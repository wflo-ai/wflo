import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'wflo - AI Workflow Orchestration with Guardrails',
  description: 'See how wflo prevents runaway AI costs and provides governance with human-in-the-loop approval gates',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  )
}
