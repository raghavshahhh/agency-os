export const metadata = {
  title: 'RAGS Pro | AI Automation Agency',
  description: 'AI-powered automation for businesses. Chatbots, lead scrapers, SaaS MVPs.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-dark text-white">{children}</body>
    </html>
  )
}
