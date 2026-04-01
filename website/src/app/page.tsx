'use client'

import { motion } from 'framer-motion'
import { Bot, Zap, Users, ArrowRight, Check, Sparkles } from 'lucide-react'
import Link from 'next/link'

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-darker to-dark">
      {/* Hero */}
      <section className="relative px-6 py-24 lg:px-8">
        <div className="mx-auto max-w-4xl text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 inline-flex items-center gap-2 rounded-full bg-primary/10 px-4 py-2 text-primary"
          >
            <Sparkles className="h-4 w-4" />
            <span className="text-sm font-medium">AI Automation Agency</span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-5xl font-bold tracking-tight text-white sm:text-7xl"
          >
            Stop Doing{' '}
            <span className="bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
              Manual Work
            </span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="mt-6 text-lg text-gray-400"
          >
            AI-powered automation for businesses. Chatbots, lead scrapers, workflow automation.
            <br />
            Built by a 22yo founder who ships in days, not months.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center"
          >
            <Link
              href="#pricing"
              className="flex items-center gap-2 rounded-full bg-primary px-8 py-4 font-semibold text-white hover:bg-primary/90"
            >
              See Pricing <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="https://cal.com/raghavshah"
              className="rounded-full border border-gray-700 px-8 py-4 font-semibold text-white hover:bg-white/5"
            >
              Book Free Call
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Services */}
      <section className="px-6 py-16 lg:px-8">
        <div className="mx-auto max-w-6xl">
          <h2 className="text-center text-3xl font-bold text-white">What I Build</h2>
          <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {[
              { icon: Bot, title: 'AI Chatbots', desc: 'WhatsApp, Telegram, Web chatbots that qualify leads 24/7' },
              { icon: Zap, title: 'Lead Scrapers', desc: 'Automated lead generation from Reddit, LinkedIn, Twitter' },
              { icon: Users, title: 'Workflow Automation', desc: 'n8n, Make.com, custom integrations' },
            ].map((service, i) => (
              <motion.div
                key={service.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 * i }}
                className="rounded-2xl border border-gray-800 bg-white/5 p-6"
              >
                <service.icon className="h-8 w-8 text-primary" />
                <h3 className="mt-4 text-lg font-semibold text-white">{service.title}</h3>
                <p className="mt-2 text-gray-400">{service.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="px-6 py-16 lg:px-8">
        <div className="mx-auto max-w-5xl">
          <h2 className="text-center text-3xl font-bold text-white">Pricing</h2>
          <p className="mt-4 text-center text-gray-400">Fixed prices. No scope creep. Delivery in days.</p>

          <div className="mt-12 grid gap-6 lg:grid-cols-3">
            {[
              {
                name: 'Chatbot',
                price: '₹25,000',
                desc: 'AI chatbot for one platform',
                features: ['WhatsApp/Telegram/Web', 'Lead qualification', 'Auto-responses', '1 week delivery'],
              },
              {
                name: 'Automation',
                price: '₹35,000',
                desc: 'Workflow automation system',
                features: ['n8n/Make setup', '3 integrations', 'Custom logic', '2 week delivery'],
                popular: true,
              },
              {
                name: 'Lead Scraper',
                price: '₹45,000',
                desc: 'Custom lead generation tool',
                features: ['Multi-source scraping', 'Email extraction', 'Auto-outreach', '2 week delivery'],
              },
            ].map((plan, i) => (
              <motion.div
                key={plan.name}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 * i }}
                className={`rounded-2xl border p-6 ${plan.popular ? 'border-primary bg-primary/5' : 'border-gray-800 bg-white/5'}`}
              >
                {plan.popular && (
                  <span className="rounded-full bg-primary/20 px-3 py-1 text-xs font-medium text-primary">
                    Most Popular
                  </span>
                )}
                <h3 className="mt-4 text-xl font-semibold text-white">{plan.name}</h3>
                <p className="mt-1 text-gray-400">{plan.desc}</p>
                <p className="mt-4 text-4xl font-bold text-white">{plan.price}</p>
                <ul className="mt-6 space-y-3">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-center gap-2 text-gray-300">
                      <Check className="h-4 w-4 text-primary" />
                      {feature}
                    </li>
                  ))}
                </ul>
                <Link
                  href={`/payment?plan=${plan.name.toLowerCase()}`}
                  className={`mt-6 block w-full rounded-full py-3 text-center font-semibold ${
                    plan.popular
                      ? 'bg-primary text-white hover:bg-primary/90'
                      : 'border border-gray-700 text-white hover:bg-white/5'
                  }`}
                >
                  Get Started
                </Link>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-800 px-6 py-12">
        <div className="mx-auto max-w-6xl text-center text-gray-400">
          <p>© 2025 RAGS Pro. Built by a 22yo founder in Delhi.</p>
          <p className="mt-2">ragspro.com | raghav@ragspro.com | +91 98765 43210</p>
        </div>
      </footer>
    </main>
  )
}
