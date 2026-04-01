'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { useSearchParams } from 'next/navigation'
import { Loader2, CheckCircle } from 'lucide-react'

const PLANS = {
  chatbot: { name: 'Chatbot', price: 25000, desc: 'AI chatbot for one platform' },
  automation: { name: 'Automation', price: 35000, desc: 'Workflow automation system' },
  scraper: { name: 'Lead Scraper', price: 45000, desc: 'Custom lead generation tool' },
}

export default function PaymentPage() {
  const searchParams = useSearchParams()
  const planKey = searchParams.get('plan') || 'automation'
  const plan = PLANS[planKey as keyof typeof PLANS] || PLANS.automation

  const [form, setForm] = useState({ name: '', email: '', phone: '', company: '' })
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    // Simulate payment processing
    await new Promise((resolve) => setTimeout(resolve, 2000))

    // In real implementation, call Razorpay API here
    const response = await fetch('/api/create-order', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        amount: plan.price * 100, // paise
        currency: 'INR',
        receipt: `order_${Date.now()}`,
        notes: {
          customer_name: form.name,
          customer_email: form.email,
          customer_phone: form.phone,
          plan: plan.name,
        },
      }),
    })

    setLoading(false)
    setSuccess(true)
  }

  if (success) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-darker px-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <CheckCircle className="mx-auto h-16 w-16 text-green-500" />
          <h1 className="mt-6 text-2xl font-bold text-white">Payment Initiated!</h1>
          <p className="mt-2 text-gray-400">
            Check your email ({form.email}) for payment link.
            <br />
            50% upfront to start the project.
          </p>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-darker px-6 py-12">
      <div className="mx-auto max-w-md">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl border border-gray-800 bg-white/5 p-8"
        >
          <h1 className="text-2xl font-bold text-white">Complete Booking</h1>
          <p className="mt-2 text-gray-400">
            {plan.name} - ₹{plan.price.toLocaleString()}
          </p>

          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300">Name</label>
              <input
                type="text"
                required
                className="mt-1 w-full rounded-lg border border-gray-700 bg-dark px-4 py-3 text-white focus:border-primary focus:outline-none"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300">Email</label>
              <input
                type="email"
                required
                className="mt-1 w-full rounded-lg border border-gray-700 bg-dark px-4 py-3 text-white focus:border-primary focus:outline-none"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300">Phone</label>
              <input
                type="tel"
                required
                className="mt-1 w-full rounded-lg border border-gray-700 bg-dark px-4 py-3 text-white focus:border-primary focus:outline-none"
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300">Company</label>
              <input
                type="text"
                className="mt-1 w-full rounded-lg border border-gray-700 bg-dark px-4 py-3 text-white focus:border-primary focus:outline-none"
                value={form.company}
                onChange={(e) => setForm({ ...form, company: e.target.value })}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="mt-6 flex w-full items-center justify-center gap-2 rounded-full bg-primary py-4 font-semibold text-white hover:bg-primary/90 disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  Processing...
                </>
              ) : (
                `Pay ₹${(plan.price / 2).toLocaleString()} (50% upfront)`
              )}
            </button>

            <p className="mt-4 text-center text-sm text-gray-500">
              50% upfront to start. 50% on delivery.
            </p>
          </form>
        </motion.div>
      </div>
    </div>
  )
}
